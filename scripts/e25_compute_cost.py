#!/usr/bin/env python
"""E25: descriptive computational-cost measurement (protocols/E25_compute_cost_protocol_2026-11-07.md).

Measures, for the frozen E4-bis training procedures of HANFIS, FlatANFISMatched and the full flat ANFIS:
fit wall-clock time, peak-RSS increase during the fit, single-row inference latency, batch throughput,
and rule/parameter counts. Uses the frozen code unchanged (imports scripts/e4_run.py helpers and the
model modules); nothing is tuned. Every (model, fold, repetition) runs in a fresh subprocess.

  python scripts/e25_compute_cost.py --run         # the real measurement (45 subprocess runs)
  python scripts/e25_compute_cost.py --smoke       # function check only: 1 fold, 1 repetition, 3 epochs; output is discarded
  python scripts/e25_compute_cost.py --worker MODEL FOLD REP [--epochs N]   # internal

Writes results_python/e25/raw_<stamp>.csv, summary_<stamp>.json and env_<stamp>.json.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import platform
import statistics
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "python_hanfis"))
import e4_run as E4  # noqa: E402  (frozen helpers: normalise, train_best_of_restarts, INPUTS, SEEDS)
from splits import GroupTimeSplit  # noqa: E402
from hanfis_end2end import HANFIS, fit_hybrid_lower_alternating, predict as hanfis_predict  # noqa: E402
from flat_anfis_matched import build_matched, fit_hybrid as fit_matched, predict as matched_predict  # noqa: E402
import hanfis_models  # noqa: E402

TABLE = ROOT / "data" / "processed" / "asset_weeks_v2_120assets_e4bis.csv"
SEED = E4.SEEDS[0]            # first frozen seed (20260928); protocol section 3
EPOCHS = 600                  # frozen E4 value
MODELS = ["hanfis", "matched", "flat_full"]
N_FOLDS, REPS = 5, 3
LAT_WARMUP, LAT_CALLS, TP_CALLS = 200, 2000, 20


def load_split():
    df = pd.read_csv(TABLE); df["week_start_utc"] = pd.to_datetime(df["week_start_utc"], utc=True)
    df["asset_id"] = df["event_id"].str.rsplit("__", n=1).str[0]
    df = df.sort_values(["asset_id", "week_start_utc"]).reset_index(drop=True)
    df["y_lag"] = df.groupby("asset_id")["y"].shift(4)
    sup = df.dropna(subset=["y"]).reset_index(drop=True)
    X = E4.normalise(sup); y01 = np.clip(sup["y"].to_numpy(dtype=np.float64) / 100.0, 0.0, 1.0)
    sp = GroupTimeSplit(n_splits=min(N_FOLDS, sup["image_id"].nunique()), embargo_days=30, min_train_weeks=4)
    folds = sp.split(sup); sp.assert_no_leakage(sup, folds)
    return X, y01, folds


def vm_mib(key: str) -> float:
    """VmRSS / VmHWM (peak resident set) of this process in MiB, from /proc/self/status."""
    for line in open("/proc/self/status"):
        if line.startswith(key + ":"):
            return int(line.split()[1]) / 1024.0
    raise RuntimeError(key)


def reset_peak_rss() -> None:
    with open("/proc/self/clear_refs", "w") as fh:     # "5" resets the peak-RSS (VmHWM) watermark (Linux >= 4.0)
        fh.write("5")


def build_and_fit(model_name, X, y01, tr_idx, val_idx, epochs):
    if model_name == "hanfis":
        model, _ = E4.train_best_of_restarts(
            fit_hybrid_lower_alternating, lambda: HANFIS(m_raw=2, m_intermediate=3, mf_family="gauss", monotone=True),
            X[tr_idx], y01[tr_idx], X[val_idx], y01[val_idx], 3, SEED, epochs=epochs, patience=100, min_epochs=200, ridge=None)
        params = model.parameter_count
        return model, hanfis_predict, model.rule_count, params() if callable(params) else params
    if model_name == "matched":
        torch.manual_seed(SEED)
        model, search = build_matched(X[tr_idx])
        fit_matched(model, X[tr_idx], y01[tr_idx], X[val_idx], y01[val_idx], epochs=epochs, patience=100, min_epochs=200)
        return model, matched_predict, search["n_rules"], search["n_params"]
    torch.manual_seed(SEED)
    model = hanfis_models.SugenoANFIS(n_inputs=7, n_mfs=2)
    hanfis_models.fit_anfis(model, X[tr_idx], y01[tr_idx], X[val_idx], y01[val_idx], epochs=epochs, patience=60)
    rules = model.rule_count
    return model, hanfis_models.predict, rules() if callable(rules) else rules, int(sum(p.numel() for p in model.parameters() if p.requires_grad))


def worker(model_name: str, fold_idx: int, rep: int, epochs: int) -> dict:
    import gc
    torch.set_num_threads(1)
    X, y01, folds = load_split()
    f = folds[fold_idx]
    tr_all, te = f.train_index, f.test_index
    n_val = max(1, int(0.15 * len(tr_all)))
    rng = np.random.default_rng(20260928 + f.index)          # same validation carve-out as E4
    val_idx = rng.choice(tr_all, size=n_val, replace=False)
    tr_idx = np.setdiff1d(tr_all, val_idx)
    # Warm-up: one full pass of the same code path with 3 epochs (discarded), so library start-up and lazily loaded
    # code pages are already resident; then the peak-RSS watermark is reset and only the measured fit can raise it.
    build_and_fit(model_name, X, y01, tr_idx, val_idx, 3)
    gc.collect(); reset_peak_rss()
    base = vm_mib("VmHWM")
    t0 = time.perf_counter()
    model, pred, rules, params = build_and_fit(model_name, X, y01, tr_idx, val_idx, epochs)
    fit_s = time.perf_counter() - t0
    mem_delta = vm_mib("VmHWM") - base
    Xte = X[te]
    for i in range(LAT_WARMUP):
        pred(model, Xte[i % len(Xte): i % len(Xte) + 1])
    lat = []
    for i in range(LAT_CALLS):
        row = Xte[i % len(Xte): i % len(Xte) + 1]
        s = time.perf_counter(); pred(model, row); lat.append((time.perf_counter() - s) * 1e6)
    tp = []
    for _ in range(TP_CALLS):
        s = time.perf_counter(); pred(model, Xte); tp.append(len(Xte) / (time.perf_counter() - s))
    return {"model": model_name, "fold": fold_idx, "rep": rep, "fit_seconds": round(fit_s, 3), "peak_rss_increase_mib": round(mem_delta, 2),
            "latency_us_median": round(statistics.median(lat), 2), "latency_us_p95": round(float(np.percentile(lat, 95)), 2),
            "throughput_rows_per_s_median": round(statistics.median(tp), 1), "rules": int(rules), "parameters": int(params),
            "n_train": int(len(tr_idx)), "n_test_rows": int(len(te))}


def environment() -> dict:
    cpu = next((l.split(":", 1)[1].strip() for l in open("/proc/cpuinfo") if l.startswith("model name")), "unknown")
    git = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    return {"generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "git_head": git, "cpu": cpu,
            "logical_cores": __import__("os").cpu_count(), "python": platform.python_version(), "torch": torch.__version__,
            "torch_threads": 1, "platform": platform.platform(), "seed": SEED, "epochs": EPOCHS, "table": str(TABLE.relative_to(ROOT)),
            "reps": REPS, "folds": N_FOLDS, "note": "CPU only; WSL2 on a Windows mini PC; Docker, Kubernetes and Prometheus may be running concurrently"}


def orchestrate(smoke: bool) -> int:
    epochs = 3 if smoke else EPOCHS
    folds = [0] if smoke else list(range(N_FOLDS))
    reps = 1 if smoke else REPS
    out = ROOT / "results_python" / ("e25_smoke" if smoke else "e25"); out.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    rows = []
    for rep in range(1, reps + 1):
        for fold in folds:
            for m in MODELS:
                cmd = [sys.executable, str(Path(__file__).resolve()), "--worker", m, str(fold), str(rep), "--epochs", str(epochs)]
                r = subprocess.run(cmd, capture_output=True, text=True)
                line = [l for l in r.stdout.splitlines() if l.startswith("E25_ROW ")]
                if r.returncode != 0 or not line:
                    print("TECHNICAL FAILURE", m, fold, rep, r.stderr[-400:]); return 1
                row = json.loads(line[-1][len("E25_ROW "):]); rows.append(row)
                print(f"rep {rep} fold {fold} {m}: fit {row['fit_seconds']}s  mem+{row['peak_rss_increase_mib']}MiB  lat {row['latency_us_median']}us")
    df = pd.DataFrame(rows); df.to_csv(out / f"raw_{stamp}.csv", index=False)
    summ = {}
    for m, g in df.groupby("model"):
        per_fold = g.groupby("fold").median(numeric_only=True)
        summ[m] = {k: {"median": float(g[k].median()), "min": float(g[k].min()), "max": float(g[k].max()), "per_fold_median": {int(i): float(v) for i, v in per_fold[k].items()}}
                   for k in ("fit_seconds", "peak_rss_increase_mib", "latency_us_median", "latency_us_p95", "throughput_rows_per_s_median", "rules", "parameters")}
    (out / f"summary_{stamp}.json").write_text(json.dumps(summ, indent=1)); (out / f"env_{stamp}.json").write_text(json.dumps(environment(), indent=1))
    print("STATUS=E25_SMOKE_DONE" if smoke else "STATUS=E25_DONE", out)
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--run", action="store_true"); g.add_argument("--smoke", action="store_true")
    g.add_argument("--worker", nargs=3, metavar=("MODEL", "FOLD", "REP"))
    p.add_argument("--epochs", type=int, default=EPOCHS)
    a = p.parse_args(argv)
    if a.worker:
        row = worker(a.worker[0], int(a.worker[1]), int(a.worker[2]), a.epochs)
        print("E25_ROW " + json.dumps(row)); return 0
    return orchestrate(smoke=a.smoke)


if __name__ == "__main__":
    sys.exit(main())

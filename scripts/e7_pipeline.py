#!/usr/bin/env python
"""E7 -- model akhir dan prediksi forward (draf praregistrasi: protocols/E7_preregistration_DRAFT.md, A-44 .. A-47).

  python scripts/e7_pipeline.py train   [--first-forward-week 2026-08-31] [--table <csv>] [--out-dir results_python/e7_final]
  python scripts/e7_pipeline.py predict --first-week 2026-08-31 --last-week 2026-10-05 --table <v3.csv> --models-dir results_python/e7_final --out <csv>
  tambahkan --smoke pada `train` untuk latihan cepat (1 seed, 1 restart, 40 epoch) dan --first-forward-week 2026-07-20 untuk latihan pseudo-forward.

Aturan kebocoran temporal (A-47): sama dengan GroupTimeSplit di E4. Cutoff = minggu forward pertama - 30 hari; hanya baris berlabel dengan week_start <= cutoff dipakai melatih,
sehingga jendela label baris latih (t, t+28] berakhir SEBELUM waktu fitur forward pertama. Embargo < 28 hari ditolak.
Konfigurasi pelatihan identik dengan scripts/e4_run.py (A-09/A-10): HANFIS(m_raw=2, m_intermediate=3, gauss, monotone), fit_hybrid_lower_alternating, 3 restart terbaik, patience 100,
min_epochs 200, ridge=None, validasi acak 15% dengan seed tetap. Normalisasi, seed, dan fungsi latih diimpor dari e4_run.py agar tidak ada salinan yang bisa menyimpang.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import platform
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FROZEN_TABLE = "data/processed/asset_weeks_v2_120assets_e4bis.csv"
VAL_SEED = 20260933          # 20260928 + 5: "lipatan ke-5" = model akhir (lipatan 0..4 dipakai E4)
N_PARAMS = 176
OUTCOME_DAYS = 28


def sha256_file(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load_table(path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["week_start_utc"] = pd.to_datetime(df["week_start_utc"], utc=True)
    df["asset_id"] = df["event_id"].str.rsplit("__", n=1).str[0]
    return df.sort_values(["asset_id", "week_start_utc"]).reset_index(drop=True)


def select_training(df: pd.DataFrame, first_forward_week: str, embargo_days: int = 30):
    """Baris berlabel dengan week_start <= first_forward_week - embargo. Menolak embargo yang lebih pendek dari jendela label."""
    if embargo_days < OUTCOME_DAYS:
        raise ValueError(f"embargo {embargo_days} hari < jendela label {OUTCOME_DAYS} hari: kebocoran temporal")
    ffw = pd.Timestamp(first_forward_week, tz="UTC")
    cutoff = ffw - pd.Timedelta(int(embargo_days), unit="D")
    tr = df.dropna(subset=["y"])
    tr = tr[tr["week_start_utc"] <= cutoff].reset_index(drop=True)
    if tr.empty:
        raise ValueError("tidak ada baris latih setelah embargo")
    last_window_end = tr["week_start_utc"].max() + pd.Timedelta(OUTCOME_DAYS, unit="D")
    if last_window_end >= ffw:
        raise ValueError(f"jendela label latih ({last_window_end.date()}) menembus minggu forward pertama ({ffw.date()})")
    return tr, cutoff


def split_val(n: int, seed: int = VAL_SEED):
    rng = np.random.default_rng(seed)
    n_val = max(1, int(0.15 * n))
    val = rng.choice(np.arange(n), size=n_val, replace=False)
    return np.setdiff1d(np.arange(n), val), val


def forward_rows(df: pd.DataFrame, first_week: str, last_week: str, lag_weeks: int = 4) -> pd.DataFrame:
    """Baris forward berlabel dengan y_lag4 = label minggu t-28 hari (pencocokan kalender), dx2_4w dan dkev_4w terhadap minggu t-28 hari."""
    lag = df[["asset_id", "week_start_utc", "y", "exploitability", "threat_intelligence"]].copy()
    lag["week_start_utc"] = lag["week_start_utc"] + pd.Timedelta(7 * lag_weeks, unit="D")
    lag = lag.rename(columns={"y": "y_lag4", "exploitability": "x2_lag", "threat_intelligence": "x7_lag"})
    m = df.merge(lag, on=["asset_id", "week_start_utc"], how="left")
    lo, hi = pd.Timestamp(first_week, tz="UTC"), pd.Timestamp(last_week, tz="UTC")
    sel = m[(m["week_start_utc"] >= lo) & (m["week_start_utc"] <= hi) & m["y"].notna() & m["y_lag4"].notna()].copy()
    sel["dx2_4w"] = sel["exploitability"] - sel["x2_lag"]
    sel["dkev_4w"] = sel["threat_intelligence"] - sel["x7_lag"]
    return sel.reset_index(drop=True)


def _env():
    sys.path.insert(0, str(ROOT / "scripts"))
    sys.path.insert(0, str(ROOT / "python_hanfis"))
    import torch  # noqa: E402
    import e4_run as E  # noqa: E402
    from hanfis_end2end import HANFIS, fit_hybrid_lower_alternating, predict  # noqa: E402
    return torch, E, HANFIS, fit_hybrid_lower_alternating, predict


def cmd_train(a) -> int:
    torch, E, HANFIS, fit, _ = _env()
    out = Path(a.out_dir)
    if (out / "final_models_manifest.json").exists():
        print(f"ABORT: {out}/final_models_manifest.json sudah ada (model akhir dibuat sekali; hapus folder bila ini latihan)"); return 2
    df = load_table(a.table)
    tr_df, cutoff = select_training(df, a.first_forward_week, a.embargo_days)
    n = len(tr_df); obs_per_param = n / N_PARAMS
    print(f"baris latih {n} (minggu {tr_df['week_start_utc'].min().date()} .. {tr_df['week_start_utc'].max().date()}), cutoff {cutoff.date()}, obs/parameter {obs_per_param:.1f}")
    if obs_per_param < a.min_obs_per_param:
        print(f"ABORT: gerbang kecukupan data gagal ({obs_per_param:.1f} < {a.min_obs_per_param})"); return 2
    X = E.normalise(tr_df); y_raw = tr_df["y"].to_numpy(dtype=np.float64); y01 = np.clip(y_raw / 100.0, 0.0, 1.0)
    tr, va = split_val(n)
    seeds = a.seeds[:1] if a.smoke else a.seeds
    if list(a.seeds) != list(E.SEEDS) and not a.smoke:
        print(f"ABORT: seed {a.seeds} bukan seed beku {E.SEEDS}"); return 2
    (out / "models").mkdir(parents=True, exist_ok=True)
    entries = []
    for seed in seeds:
        model, val = E.train_best_of_restarts(
            fit, lambda: HANFIS(m_raw=2, m_intermediate=3, mf_family="gauss", monotone=True),
            X[tr], y01[tr], X[va], y01[va], 1 if a.smoke else a.n_restarts, seed,
            epochs=40 if a.smoke else a.epochs, patience=100, min_epochs=1 if a.smoke else 200, ridge=None)
        path = out / "models" / f"final_seed{seed}_hanfis.pt"
        torch.save(model.state_dict(), path)
        entries.append({"seed": seed, "file": path.name, "sha256": sha256_file(path), "best_val_mse": float(val)})
        print(f"seed {seed}: best_val_mse={val:.5f}  {path.name}  sha256 {entries[-1]['sha256'][:16]}")
    beta = E.ridge_fit(X[tr], y_raw[tr])
    manifest = {
        "kind": "E7 final models" + (" (SMOKE / pseudo-forward latihan; bukan model E7)" if a.smoke else ""), "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "first_forward_week": a.first_forward_week, "embargo_days": a.embargo_days, "cutoff": str(cutoff.date()),
        "train_weeks": [str(tr_df["week_start_utc"].min().date()), str(tr_df["week_start_utc"].max().date())], "n_train_rows": n, "n_fit_rows": int(len(tr)), "n_val_rows": int(len(va)),
        "obs_per_parameter": obs_per_param, "val_seed": VAL_SEED, "models": entries, "ridge7_beta": [float(b) for b in beta],
        "table": str(a.table), "table_sha256": sha256_file(a.table), "e4_run_sha256": sha256_file(ROOT / "scripts" / "e4_run.py"), "pipeline_sha256": sha256_file(__file__),
        "python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__, "torch": getattr(torch, "__version__", "?"),
        "training": {"m_raw": 2, "m_intermediate": 3, "mf_family": "gauss", "monotone": True, "n_restarts": 1 if a.smoke else a.n_restarts, "epochs": 40 if a.smoke else a.epochs,
                     "patience": 100, "min_epochs": 1 if a.smoke else 200, "ridge": None},
    }
    (out / "final_models_manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    print(f"ditulis: {out}/final_models_manifest.json\nSTATUS=E7_TRAIN_DONE" + (" (SMOKE)" if a.smoke else ""))
    return 0


def cmd_predict(a) -> int:
    torch, E, HANFIS, _, hpredict = _env()
    mdir = Path(a.models_dir); man = json.loads((mdir / "final_models_manifest.json").read_text(encoding="utf-8"))
    ffw = pd.Timestamp(man["first_forward_week"], tz="UTC")
    if pd.Timestamp(a.first_week, tz="UTC") < ffw:
        print(f"ABORT: --first-week {a.first_week} lebih awal dari minggu forward pertama model ({man['first_forward_week']}): kebocoran temporal"); return 2
    preds, betas = [], np.asarray(man["ridge7_beta"])
    df = load_table(a.table); rows = forward_rows(df, a.first_week, a.last_week)
    if rows.empty:
        print("ABORT: tidak ada baris forward berlabel pada rentang itu"); return 2
    X = E.normalise(rows)
    for ent in man["models"]:
        path = mdir / "models" / ent["file"]
        if sha256_file(path) != ent["sha256"]:
            print(f"ABORT: hash {ent['file']} tidak cocok dengan manifest"); return 2
        m = HANFIS(m_raw=2, m_intermediate=3, mf_family="gauss", monotone=True); m.load_state_dict(torch.load(path, map_location="cpu")); preds.append(hpredict(m, X))
    out = pd.DataFrame({"event_id": rows["event_id"], "week": rows["week_start_utc"].dt.strftime("%Y-%m-%d"), "y_true": rows["y"],
                        "y_hanfis": np.mean(preds, axis=0) * 100.0, "y_lag4": rows["y_lag4"], "y_ridge7": E.ridge_predict(betas, X),
                        "dx2_4w": rows["dx2_4w"], "dkev_4w": rows["dkev_4w"]})
    diag = Path(a.diagnostics) if a.diagnostics else Path(str(a.table).replace(".csv", "_diagnostics.csv"))
    if diag.exists():
        d = pd.read_csv(diag)
        if {"event_id", "epss_model_version"} <= set(d.columns):
            out = out.merge(d[["event_id", "epss_model_version"]].drop_duplicates("event_id"), on="event_id", how="left")
    Path(a.out).parent.mkdir(parents=True, exist_ok=True); out.to_csv(a.out, index=False)
    print(f"{len(out)} baris, {out['week'].nunique()} minggu ({out['week'].min()} .. {out['week'].max()}), {out['event_id'].str.rsplit('__', n=1).str[0].nunique()} aset -> {a.out}\nSTATUS=E7_PREDICT_DONE")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter); sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("train"); t.add_argument("--table", default=str(ROOT / FROZEN_TABLE)); t.add_argument("--first-forward-week", default="2026-08-31")
    t.add_argument("--embargo-days", type=int, default=30); t.add_argument("--out-dir", default=str(ROOT / "results_python" / "e7_final"))
    t.add_argument("--seeds", type=int, nargs="+", default=[20260928, 20261005, 20261012, 20261019, 20261026]); t.add_argument("--n-restarts", type=int, default=3)
    t.add_argument("--epochs", type=int, default=600); t.add_argument("--min-obs-per-param", type=float, default=10.0); t.add_argument("--smoke", action="store_true")
    p = sub.add_parser("predict"); p.add_argument("--table", required=True); p.add_argument("--models-dir", default=str(ROOT / "results_python" / "e7_final"))
    p.add_argument("--first-week", required=True); p.add_argument("--last-week", required=True); p.add_argument("--out", required=True); p.add_argument("--diagnostics")
    a = ap.parse_args(argv)
    return cmd_train(a) if a.cmd == "train" else cmd_predict(a)


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python
"""E5: accuracy/complexity curve over the inter-tier bottleneck width k (patch 0055).
RUN tests/test_bottleneck_smoke.py FIRST.

Trains HANFISBottleneck at each k in --ks (default 1 2; k>=3 refused by estimate_params unless
--allow-oversize) on the SAME GroupTimeSplit folds and frozen seeds as E4, using the simpler
Integration-only closed-form scheme (NOT E2 -- see hanfis_bottleneck.py's module docstring for
why). Reports RMSE and skill vs persistence per k, alongside rule/parameter counts, so the
accuracy/complexity trade-off is visible directly rather than asserted.

  python scripts/e5_sweep.py --ks 1 2
"""
from __future__ import annotations

import argparse
import datetime as dt
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python_hanfis"))
from splits import GroupTimeSplit  # noqa: E402
from hanfis_bottleneck import HANFISBottleneck, BottleneckBudgetError, fit_hybrid, predict, estimate_params  # noqa: E402

INPUTS = ["cvss", "exploitability", "patch_risk", "mfa_risk", "kubernetes_exposure", "asset_criticality", "threat_intelligence"]
SEEDS = [20260928, 20261005, 20261012, 20261019, 20261026]


def normalise(df: pd.DataFrame) -> np.ndarray:
    X = df[INPUTS].to_numpy(dtype=np.float64, copy=True)
    X[:, 0] /= 10.0; X[:, 2] /= 2.0; X[:, 5] = (X[:, 5] - 1) / 4.0
    return np.nan_to_num(X, nan=0.0)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--table", default=str(ROOT / "data" / "processed" / "asset_weeks_v2.csv"))
    p.add_argument("--n-splits", type=int, default=5); p.add_argument("--embargo-days", type=int, default=30)
    p.add_argument("--min-train-weeks", type=int, default=4); p.add_argument("--n-restarts", type=int, default=3)
    p.add_argument("--epochs", type=int, default=600); p.add_argument("--lag-weeks", type=int, default=4)
    p.add_argument("--ks", type=int, nargs="+", default=[1, 2])
    p.add_argument("--max-params", type=int, default=2000)
    p.add_argument("--allow-oversize", action="store_true", help="train a k whose estimated params exceed --max-params anyway")
    p.add_argument("--out-dir", default=str(ROOT / "results_python" / "e5"))
    a = p.parse_args(argv)

    for k in a.ks:
        est = estimate_params(2, 3, k)
        flag = "OK" if est["total_params"] <= a.max_params else ("ALLOWED (--allow-oversize)" if a.allow_oversize else "WILL BE REFUSED")
        print(f"k={k}: estimated {est['integration_rules']} integration rules, {est['total_params']} total params -> {flag}")
    if any(estimate_params(2, 3, k)["total_params"] > a.max_params for k in a.ks) and not a.allow_oversize:
        print("Some k values exceed --max-params and will raise BottleneckBudgetError when reached;"
              " this is itself the E5 finding about combinatorial growth, not a bug. Drop them from"
              " --ks or pass --allow-oversize to pay the cost anyway.")

    df = pd.read_csv(a.table); df["week_start_utc"] = pd.to_datetime(df["week_start_utc"], utc=True)
    df["asset_id"] = df["event_id"].str.rsplit("__", n=1).str[0]
    df = df.sort_values(["asset_id", "week_start_utc"]).reset_index(drop=True)
    df["y_lag"] = df.groupby("asset_id")["y"].shift(a.lag_weeks)
    sup = df.dropna(subset=["y"]).reset_index(drop=True)
    X_all = normalise(sup); y_raw = sup["y"].to_numpy(dtype=np.float64); y01 = np.clip(y_raw / 100.0, 0.0, 1.0)

    n_groups = min(a.n_splits, sup["image_id"].nunique())
    sp = GroupTimeSplit(n_splits=n_groups, embargo_days=a.embargo_days, min_train_weeks=a.min_train_weeks)
    folds = sp.split(sup); sp.assert_no_leakage(sup, folds)

    rows = []
    for k in a.ks:
        try:
            estimate_k = estimate_params(2, 3, k)
        except Exception:
            estimate_k = {}
        for f in folds:
            t0 = time.time()
            tr_all, te = f.train_index, f.test_index
            n_val = max(1, int(0.15 * len(tr_all)))
            rng = np.random.default_rng(20260928 + f.index)
            val_idx = rng.choice(tr_all, size=n_val, replace=False)
            tr_idx = np.setdiff1d(tr_all, val_idx)

            clim = float(y_raw[tr_idx].mean())
            pers_raw = sup["y_lag"].to_numpy()[te]
            y_pers = np.where(np.isnan(pers_raw), clim, pers_raw)

            preds = []
            try:
                for seed in SEEDS:
                    best_val, best_model = float("inf"), None
                    for r in range(a.n_restarts):
                        torch.manual_seed(seed * 100 + r)
                        model = HANFISBottleneck(bottleneck_k=k, monotone=True, max_params=a.max_params, allow_oversize=a.allow_oversize)
                        hist = fit_hybrid(model, X_all[tr_idx], y01[tr_idx], X_all[val_idx], y01[val_idx],
                                         epochs=a.epochs, patience=100, min_epochs=200)
                        if hist["best_validation_loss"] < best_val:
                            best_val, best_model = hist["best_validation_loss"], model
                    preds.append(predict(best_model, X_all[te]))
            except BottleneckBudgetError as exc:
                print(f"k={k} fold {f.index}: REFUSED -- {exc}")
                break
            y_hanfis = np.mean(preds, axis=0) * 100.0
            rmse = float(np.sqrt(np.mean((y_hanfis - y_raw[te]) ** 2)))
            mse_pers = float(np.mean((y_pers - y_raw[te]) ** 2))
            mse_h = float(np.mean((y_hanfis - y_raw[te]) ** 2))
            ss_pers = 1 - mse_h / mse_pers if mse_pers > 0 else float("nan")
            rows.append({"k": k, "fold": f.index, "rmse": rmse, "ss_pers": ss_pers, "n_test": len(te),
                        "rules": best_model.rule_count, "params": best_model.parameter_count,
                        "time_sec": round(time.time() - t0, 1), **{f"est_{kk}": vv for kk, vv in estimate_k.items()}})
            print(f"k={k} fold {f.index}: rmse={rmse:.4f} ss_pers={ss_pers:.4f} "
                  f"rules={best_model.rule_count} params={best_model.parameter_count} ({time.time()-t0:.0f}s)")

    res = pd.DataFrame(rows)
    out = Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    res.to_csv(out / f"e5_sweep_{stamp}.csv", index=False)
    if not res.empty:
        summary = res.groupby("k").agg(rmse_mean=("rmse", "mean"), rmse_std=("rmse", "std"),
                                       ss_pers_mean=("ss_pers", "mean"), rules=("rules", "first"),
                                       params=("params", "first"), time_sec_total=("time_sec", "sum"))
        print(); print(summary.round(4).to_string())
        summary.to_csv(out / f"e5_summary_{stamp}.csv")
    print(f"\nwrote {out}/e5_sweep_{stamp}.csv")
    print("STATUS=E5_SWEEP_DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())

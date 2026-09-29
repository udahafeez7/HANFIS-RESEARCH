#!/usr/bin/env python
"""E2 pilot (patch 0035): does alternating lower-panel LSE beat the current default?

Compares, under GroupTimeSplit (A-16), 3 restarts each:
  - fit_hybrid                   (current default: Integration closed-form only)
  - fit_hybrid_lower_alternating (E2: both lower panels closed-form too)
  - fit_adam                     (pure gradient, kept for completeness / E-INT comparison)
on the real asset-week table. RUN tests/test_e2_alternating_smoke.py FIRST.

  python scripts/e2_pilot.py --table data/processed/asset_weeks_v2.csv --n-splits 5
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python_hanfis"))
from splits import GroupTimeSplit  # noqa: E402
from hanfis_end2end import HANFIS, fit_hybrid, fit_hybrid_lower_alternating, fit_adam, predict  # noqa: E402

INPUTS = ["cvss", "exploitability", "patch_risk", "mfa_risk", "kubernetes_exposure", "asset_criticality", "threat_intelligence"]
METHODS = {"hybrid_integration_only": fit_hybrid, "hybrid_lower_alternating": fit_hybrid_lower_alternating, "adam": fit_adam}


def normalise(df: pd.DataFrame) -> np.ndarray:
    X = df[INPUTS].to_numpy(dtype=np.float32, copy=True)
    X[:, 0] /= 10.0; X[:, 2] /= 2.0; X[:, 5] = (X[:, 5] - 1) / 4.0
    return np.nan_to_num(X, nan=0.0)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--table", default=str(ROOT / "data" / "processed" / "asset_weeks_v2.csv"))
    p.add_argument("--n-splits", type=int, default=5); p.add_argument("--embargo-days", type=int, default=30)
    p.add_argument("--min-train-weeks", type=int, default=4); p.add_argument("--n-restarts", type=int, default=3)
    p.add_argument("--epochs", type=int, default=600); p.add_argument("--out-dir", default=str(ROOT / "results_python" / "e2"))
    a = p.parse_args(argv)

    df = pd.read_csv(a.table); df["week_start_utc"] = pd.to_datetime(df["week_start_utc"], utc=True)
    sup = df.dropna(subset=["y"]).reset_index(drop=True)
    y_raw = sup["y"].to_numpy(dtype=np.float32) / 100.0     # 0-100 -> 0-1, matches the [0,1]-clamped model output
    X = normalise(sup)

    n_groups = min(a.n_splits, sup["image_id"].nunique())
    sp = GroupTimeSplit(n_splits=n_groups, embargo_days=a.embargo_days, min_train_weeks=a.min_train_weeks)
    folds = sp.split(sup); sp.assert_no_leakage(sup, folds)

    rows = []
    for f in folds:
        tr_all, te = f.train_index, f.test_index
        n_val = max(1, int(0.15 * len(tr_all)))
        rng = np.random.default_rng(20260928 + f.index)
        val_idx = rng.choice(tr_all, size=n_val, replace=False)
        tr_idx = np.setdiff1d(tr_all, val_idx)
        for method_name, fit_fn in METHODS.items():
            best_val = float("inf"); best_model = None
            for k in range(a.n_restarts):
                torch.manual_seed(20260928 * 1000 + f.index * 100 + k)
                model = HANFIS(m_raw=2, m_intermediate=3, mf_family="gauss", monotone=True)
                kwargs = dict(epochs=a.epochs, patience=100, min_epochs=200) if method_name != "adam" else dict(epochs=a.epochs, patience=60)
                hist = fit_fn(model, X[tr_idx], y_raw[tr_idx], X[val_idx], y_raw[val_idx], **kwargs)
                if hist["best_validation_loss"] < best_val:
                    best_val, best_model = hist["best_validation_loss"], model
            yhat = predict(best_model, X[te]) * 100.0
            ytrue = sup["y"].to_numpy(dtype=np.float32)[te]
            rmse = float(np.sqrt(np.mean((yhat - ytrue) ** 2)))
            rows.append({"fold": f.index, "method": method_name, "rmse": rmse, "n_test": len(te),
                        "best_val_mse": best_val, "params": best_model.parameter_count, "rules": best_model.rule_count})
            print(f"fold {f.index}  {method_name:26s}  rmse={rmse:.4f}  val_mse={best_val:.5f}")

    res = pd.DataFrame(rows)
    out = Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    res.to_csv(out / f"e2_pilot_{stamp}.csv", index=False)
    summary = res.groupby("method")["rmse"].agg(["mean", "std"]).round(4)
    print(); print(summary.to_string())
    print(f"\nwrote {out}/e2_pilot_{stamp}.csv")
    print("STATUS=E2_PILOT_DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())

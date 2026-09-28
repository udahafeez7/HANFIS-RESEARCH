#!/usr/bin/env python
"""E3 pilot: mandatory cheap baselines on the real asset-week table under GroupTimeSplit (A-16).

Baselines (memory §2): persistence, climatology, single CVSS. Plus a ridge on the 7 inputs as a
capacity-free linear reference (reported separately, not a §2 comparator). Metrics per fold on the
test rows: RMSE, MAE, R2, and skill scores SS_clim = 1 - MSE/MSE_clim, SS_pers = 1 - MSE/MSE_pers.
Label scales: raw y (0-100) and log1p(y); the A-13 scale decision is still open, so both are reported.

Persistence is strictly causal: y(a,t) becomes observable only at t + 30 d, so the latest known
outcome at t is y(a, t - 28 d) (4 weekly steps); missing -> climatology of the training rows.

  python scripts/e3_baselines.py --table data/processed/asset_weeks_v2.csv --n-splits 5
Outputs: results_python/e3/baselines_<utc>.csv (per fold x baseline x scale), _summary.csv, _folds.csv.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python_hanfis"))
from splits import GroupTimeSplit, summarise_folds  # noqa: E402

INPUTS = ["cvss", "exploitability", "patch_risk", "mfa_risk", "kubernetes_exposure", "asset_criticality", "threat_intelligence"]
SCALES = {"raw": (lambda y: y, lambda z: z), "log1p": (np.log1p, np.expm1)}


def metrics(y, yhat, y_clim, y_pers) -> dict:
    err = lambda a, b: float(np.mean((a - b) ** 2))
    mse, mse_c, mse_p = err(y, yhat), err(y, y_clim), err(y, y_pers)
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    return {"rmse": mse ** 0.5, "mae": float(np.mean(np.abs(y - yhat))),
            "r2": 1 - mse * len(y) / ss_tot if ss_tot > 0 else float("nan"),
            "ss_clim": 1 - mse / mse_c if mse_c > 0 else float("nan"),
            "ss_pers": 1 - mse / mse_p if mse_p > 0 else float("nan"), "n_test": int(len(y))}


def ridge_fit(X, y, lam=1e-3):
    Xa = np.c_[np.ones(len(X)), X]
    return np.linalg.solve(Xa.T @ Xa + lam * np.eye(Xa.shape[1]), Xa.T @ y)


def ridge_predict(beta, X):
    return np.c_[np.ones(len(X)), X] @ beta


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--table", default=str(ROOT / "data" / "processed" / "asset_weeks_v2.csv"))
    p.add_argument("--n-splits", type=int, default=5); p.add_argument("--embargo-days", type=int, default=30)
    p.add_argument("--min-train-weeks", type=int, default=4); p.add_argument("--lag-weeks", type=int, default=4)
    p.add_argument("--out-dir", default=str(ROOT / "results_python" / "e3"))
    a = p.parse_args(argv)

    df = pd.read_csv(a.table)
    df["week_start_utc"] = pd.to_datetime(df["week_start_utc"], utc=True)
    df["asset_id"] = df["event_id"].str.rsplit("__", n=1).str[0]
    df = df.sort_values(["asset_id", "week_start_utc"]).reset_index(drop=True)
    # causal persistence: own outcome lag_weeks earlier (observable at t), computed on the full table
    df["y_lag"] = df.groupby("asset_id")["y"].shift(a.lag_weeks)
    sup = df.dropna(subset=["y"]).reset_index(drop=True)
    for c in INPUTS:
        sup[c] = sup[c].astype(float)
    # normalise inputs to [0,1] with the contract ranges (x1/10, x3/2, x6 (1..5)->(0..1))
    X_all = sup[INPUTS].to_numpy(copy=True)
    X_all[:, 0] /= 10.0; X_all[:, 2] /= 2.0; X_all[:, 5] = (X_all[:, 5] - 1) / 4.0
    X_all = np.nan_to_num(X_all, nan=0.0)

    n_groups = min(a.n_splits, sup["image_id"].nunique())
    sp = GroupTimeSplit(n_splits=n_groups, embargo_days=a.embargo_days, min_train_weeks=a.min_train_weeks)
    folds = sp.split(sup); sp.assert_no_leakage(sup, folds)
    fold_table = summarise_folds(sup, folds)

    rows = []
    for f in folds:
        tr, te = sup.iloc[f.train_index], sup.iloc[f.test_index]
        for scale, (fwd, _) in SCALES.items():
            ytr, yte = fwd(tr["y"].to_numpy()), fwd(te["y"].to_numpy())
            clim = float(ytr.mean())
            y_clim = np.full(len(te), clim)
            pers = fwd(te["y_lag"].to_numpy()); y_pers = np.where(np.isnan(pers), clim, pers)
            preds = {"climatology": y_clim, "persistence": y_pers}
            b1 = ridge_fit(X_all[f.train_index][:, :1], ytr); preds["cvss_only"] = ridge_predict(b1, X_all[f.test_index][:, :1])
            b7 = ridge_fit(X_all[f.train_index], ytr); preds["ridge_7inputs"] = ridge_predict(b7, X_all[f.test_index])
            for name, yhat in preds.items():
                rows.append({"fold": f.index, "scale": scale, "baseline": name, **metrics(yte, yhat, y_clim, y_pers)})
    res = pd.DataFrame(rows)
    summary = (res.groupby(["scale", "baseline"])[["rmse", "mae", "r2", "ss_clim", "ss_pers"]]
               .agg(["mean", "std"]).round(4))
    # Pooled skill scores: MSE summed over all test rows of all folds, then one ratio. A mean of
    # per-fold ratios explodes when a fold's reference MSE is near zero (seen on the 27-asset pilot).
    pooled_rows = []
    for scale in SCALES:
        sub = res[res.scale == scale]
        mse = sub.assign(sse=lambda d: d.rmse ** 2 * d.n_test).groupby("baseline")["sse"].sum()
        n = sub.groupby("baseline")["n_test"].sum()
        pooled_mse = (mse / n)
        for b in pooled_mse.index:
            pooled_rows.append({"scale": scale, "baseline": b, "rmse_pooled": float(pooled_mse[b] ** 0.5),
                                "ss_clim_pooled": float(1 - pooled_mse[b] / pooled_mse["climatology"]),
                                "ss_pers_pooled": float(1 - pooled_mse[b] / pooled_mse["persistence"])})
    pooled = pd.DataFrame(pooled_rows).set_index(["scale", "baseline"]).round(4)
    out = Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    res.to_csv(out / f"baselines_{stamp}.csv", index=False)
    summary.to_csv(out / f"baselines_{stamp}_summary.csv")
    pooled.to_csv(out / f"baselines_{stamp}_pooled.csv")
    fold_table.to_csv(out / f"baselines_{stamp}_folds.csv", index=False)
    (out / f"baselines_{stamp}_meta.json").write_text(json.dumps({
        "table": a.table, "rows_supervised": int(len(sup)), "assets": int(sup["asset_id"].nunique()),
        "image_groups": int(sup["image_id"].nunique()), "n_splits_used": n_groups, "embargo_days": a.embargo_days,
        "lag_weeks": a.lag_weeks, "group_assignment": sp.group_assignment(sup), "generated_utc": stamp}, indent=2))
    print(fold_table[["fold", "train_rows", "test_rows", "train_images", "test_images", "test_target_nonzero_share"]].to_string(index=False))
    print(); print(summary.to_string()); print(); print("pooled over all test rows:"); print(pooled.to_string())
    print(f"\nwrote {out}/baselines_{stamp}*.csv  |  rows={len(sup)} assets={sup['asset_id'].nunique()} folds={len(folds)}")
    print("STATUS=E3_BASELINES_DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())

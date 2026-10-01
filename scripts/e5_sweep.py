#!/usr/bin/env python
"""E5: accuracy/complexity curve over the inter-tier bottleneck width k (patch 0055/0058/0059).
RUN tests/test_bottleneck_smoke.py FIRST.

Trains HANFISBottleneck at each k in --ks (default 1 2; k>=3 refused by estimate_params unless
--allow-oversize) on the SAME GroupTimeSplit folds and frozen seeds as E4, with the vector
generalisation of the A-19 alternating scheme (default) and, since patch 0059, with the
Integration intercept refit and clamp_intermediates OFF (--clamp-intermediates on reproduces
the patch-0058 forward for a parity check against the A-09 model).

Reporting (patch 0059). The per-fold mean of ss_pers is NOT a usable summary: ss = 1 - mse/
mse_pers explodes on folds whose test block is nearly static (persistence RMSE ~0.09-0.10 on the
0-100 scale gave -124 and -102 on 2026-10-01) and the mean is then meaningless. The E4
preregistration scores skill on the POOLED MSE over all test rows; this script now writes every
test-row prediction (e5_predictions_<stamp>.csv: event_id, image_id, k, fold, y, y_pers,
y_hanfis) and reports ss_pers_pooled and rmse_pooled per k, with the per-fold median as a
robustness check. The per-fold mean is kept in the CSV only for continuity. It also reports
obs_per_param = n_train / params per fold: the §9 gate asks >= 10, and k=2 (1,152 params) is
below it on every fold of the 109-asset inventory -- the sweep still runs (mechanism probe),
but the flag must travel with the number into the manuscript.

  python scripts/e5_sweep.py --ks 1 2
  python scripts/e5_sweep.py --ks 1 --clamp-intermediates on     # parity run vs A-09 forward
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
from hanfis_bottleneck import HANFISBottleneck, BottleneckBudgetError, fit_hybrid, fit_hybrid_lower_alternating, predict, estimate_params  # noqa: E402

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
    p.add_argument("--scheme", choices=["integration_only", "alternating"], default="alternating",
                   help="training scheme: 'alternating' (default) is the vector-generalised E2/A-09 "
                        "scheme that de-confounds the sweep; 'integration_only' reproduces the "
                        "earlier, confounded e5_sweep_20261001T045940Z.csv run for comparison")
    p.add_argument("--allow-oversize", action="store_true", help="train a k whose estimated params exceed --max-params anyway")
    p.add_argument("--clamp-intermediates", choices=["on", "off"], default="off",
                   help="'off' (default, patch 0059): forward() evaluates the same unclamped v,e the closed-form "
                        "solves minimise; 'on' reproduces the patch-0058 forward (v,e clamped to [0,1])")
    p.add_argument("--min-obs-per-param", type=float, default=10.0, help="§9 gate threshold used only to FLAG folds (never to skip them)")
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

    rows = []; pred_rows = []
    clamp_flag = a.clamp_intermediates == "on"
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
                    fit_fn = fit_hybrid_lower_alternating if a.scheme == "alternating" else fit_hybrid
                    for r in range(a.n_restarts):
                        torch.manual_seed(seed * 100 + r)
                        model = HANFISBottleneck(bottleneck_k=k, monotone=True, max_params=a.max_params,
                                                 allow_oversize=a.allow_oversize, clamp_intermediates=clamp_flag)
                        hist = fit_fn(model, X_all[tr_idx], y01[tr_idx], X_all[val_idx], y01[val_idx],
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
            obs_per_param = len(tr_idx) / best_model.parameter_count
            rows.append({"k": k, "fold": f.index, "scheme": a.scheme, "clamp_intermediates": a.clamp_intermediates,
                        "rmse": rmse, "ss_pers": ss_pers, "rmse_pers": float(np.sqrt(mse_pers)), "n_test": len(te),
                        "n_train": int(len(tr_idx)), "obs_per_param": round(obs_per_param, 2),
                        "underpowered": bool(obs_per_param < a.min_obs_per_param),
                        "rules": best_model.rule_count, "params": best_model.parameter_count,
                        "time_sec": round(time.time() - t0, 1), **{f"est_{kk}": vv for kk, vv in estimate_k.items()}})
            pred_rows.append(pd.DataFrame({"event_id": sup["event_id"].to_numpy()[te], "image_id": sup["image_id"].to_numpy()[te],
                                           "k": k, "fold": f.index, "y": y_raw[te], "y_pers": y_pers, "y_hanfis": y_hanfis}))
            print(f"k={k} fold {f.index}: rmse={rmse:.4f} rmse_pers={np.sqrt(mse_pers):.4f} ss_pers={ss_pers:.4f} "
                  f"n_train={len(tr_idx)} obs/param={obs_per_param:.1f}{' UNDERPOWERED' if obs_per_param < a.min_obs_per_param else ''} "
                  f"rules={best_model.rule_count} params={best_model.parameter_count} ({time.time()-t0:.0f}s)")

    res = pd.DataFrame(rows)
    out = Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    res.to_csv(out / f"e5_sweep_{stamp}.csv", index=False)
    if not res.empty:
        preds_df = pd.concat(pred_rows, ignore_index=True)
        preds_df.to_csv(out / f"e5_predictions_{stamp}.csv", index=False)
        pooled = []
        for k, g in preds_df.groupby("k"):
            mse_h = float(np.mean((g["y_hanfis"] - g["y"]) ** 2)); mse_p = float(np.mean((g["y_pers"] - g["y"]) ** 2))
            pooled.append({"k": k, "rmse_pooled": np.sqrt(mse_h), "rmse_pers_pooled": np.sqrt(mse_p),
                           "ss_pers_pooled": 1 - mse_h / mse_p if mse_p > 0 else float("nan"), "n_test_total": int(len(g))})
        pooled = pd.DataFrame(pooled).set_index("k")
        summary = res.groupby("k").agg(rmse_mean=("rmse", "mean"), rmse_std=("rmse", "std"),
                                       ss_pers_median=("ss_pers", "median"), ss_pers_mean_UNSTABLE=("ss_pers", "mean"),
                                       obs_per_param_min=("obs_per_param", "min"), folds_underpowered=("underpowered", "sum"),
                                       rules=("rules", "first"), params=("params", "first"), time_sec_total=("time_sec", "sum"))
        summary = pooled.join(summary)
        print(); print(summary.round(4).to_string())
        print("\nHeadline per k = ss_pers_pooled / rmse_pooled (E4 preregistration metric). ss_pers_mean_UNSTABLE is the "
              "per-fold mean of ratios, kept for continuity only. Any folds_underpowered > 0 must be reported with the number.")
        summary.to_csv(out / f"e5_summary_{stamp}.csv")
        print(f"wrote {out}/e5_predictions_{stamp}.csv")
    print(f"\nwrote {out}/e5_sweep_{stamp}.csv")
    print("STATUS=E5_SWEEP_DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())

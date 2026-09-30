#!/usr/bin/env python
"""E4 confirmatory training (patch 0050): HANFIS, FlatANFISMatched, and the full flat ANFIS
reference, trained on frozen folds/seeds per protocols/E4_preregistration_2026-09-29.md.
RUN tests/test_e2_alternating_smoke.py and tests/test_flat_anfis_matched_smoke.py FIRST.

Per fold (GroupTimeSplit, A-16) and per pre-registered seed, three restarts are trained and the
lowest-validation-loss restart kept; the five seeds' held-out predictions for each row are then
averaged into one prediction per row before scripts/e4_analyse.py computes skill scores (this
mirrors E3's per-fold structure while respecting "no seed added after seeing results").

Baselines (CVSS-only, persistence, ridge-7) are recomputed inline with the SAME fold/row
definitions as scripts/e3_baselines.py, so all six columns in the output predictions CSV are
directly comparable row-for-row.

  python scripts/e4_run.py --n-splits 5

Writes results_python/e4/predictions_<timestamp>.csv with columns: event_id, image_id, fold,
y_true, y_hanfis, y_cvss_only, y_persistence, y_ridge_7inputs, y_matched, plus a
_meta_<timestamp>.json recording the frozen seeds, fold group assignment, and per-fold/method
wall-clock time.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python_hanfis"))
from splits import GroupTimeSplit  # noqa: E402
from hanfis_end2end import HANFIS, fit_hybrid_lower_alternating, predict as hanfis_predict  # noqa: E402
from flat_anfis_matched import build_matched, fit_hybrid as fit_matched, predict as matched_predict, ClusterSearchError  # noqa: E402
import hanfis_models  # noqa: E402  (flat ANFIS full reference, m=2 grid partition -- H2', no criteria)

INPUTS = ["cvss", "exploitability", "patch_risk", "mfa_risk", "kubernetes_exposure", "asset_criticality", "threat_intelligence"]
SEEDS = [20260928, 20261005, 20261012, 20261019, 20261026]   # frozen per preregistration


def normalise(df: pd.DataFrame) -> np.ndarray:
    X = df[INPUTS].to_numpy(dtype=np.float64, copy=True)
    X[:, 0] /= 10.0; X[:, 2] /= 2.0; X[:, 5] = (X[:, 5] - 1) / 4.0
    return np.nan_to_num(X, nan=0.0)


def ridge_fit(X, y, lam=1e-3):
    Xa = np.c_[np.ones(len(X)), X]
    return np.linalg.solve(Xa.T @ Xa + lam * np.eye(Xa.shape[1]), Xa.T @ y)


def ridge_predict(beta, X):
    return np.c_[np.ones(len(X)), X] @ beta


def train_best_of_restarts(fit_fn, model_fn, x_tr, y_tr, x_va, y_va, n_restarts, seed_base, **fit_kwargs):
    best_val, best_model = float("inf"), None
    for k in range(n_restarts):
        torch.manual_seed(seed_base * 100 + k)
        model = model_fn()
        hist = fit_fn(model, x_tr, y_tr, x_va, y_va, **fit_kwargs)
        if hist["best_validation_loss"] < best_val:
            best_val, best_model = hist["best_validation_loss"], model
    return best_model, best_val


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--table", default=str(ROOT / "data" / "processed" / "asset_weeks_v2.csv"))
    p.add_argument("--n-splits", type=int, default=5); p.add_argument("--embargo-days", type=int, default=30)
    p.add_argument("--min-train-weeks", type=int, default=4); p.add_argument("--n-restarts", type=int, default=3)
    p.add_argument("--epochs", type=int, default=600); p.add_argument("--lag-weeks", type=int, default=4)
    p.add_argument("--out-dir", default=str(ROOT / "results_python" / "e4"))
    p.add_argument("--seeds", type=int, nargs="+", default=SEEDS,
                   help="override the frozen seed list -- only for a quick smoke run, never for the real E4 result")
    a = p.parse_args(argv)
    if a.seeds != SEEDS:
        print(f"WARNING: using non-frozen seeds {a.seeds} -- this run is NOT the confirmatory E4 result")

    df = pd.read_csv(a.table); df["week_start_utc"] = pd.to_datetime(df["week_start_utc"], utc=True)
    df["asset_id"] = df["event_id"].str.rsplit("__", n=1).str[0]
    df = df.sort_values(["asset_id", "week_start_utc"]).reset_index(drop=True)
    df["y_lag"] = df.groupby("asset_id")["y"].shift(a.lag_weeks)
    sup = df.dropna(subset=["y"]).reset_index(drop=True)
    X_all = normalise(sup)
    y_raw = sup["y"].to_numpy(dtype=np.float64)
    y01 = np.clip(y_raw / 100.0, 0.0, 1.0)   # HANFIS/matched models output in [0,1]; rescaled back for scoring

    n_groups = min(a.n_splits, sup["image_id"].nunique())
    sp = GroupTimeSplit(n_splits=n_groups, embargo_days=a.embargo_days, min_train_weeks=a.min_train_weeks)
    folds = sp.split(sup); sp.assert_no_leakage(sup, folds)

    all_rows = []
    meta = {"seeds": a.seeds, "n_splits": n_groups, "group_assignment": sp.group_assignment(sup),
           "fold_times_sec": {}, "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}

    for f in folds:
        t0 = time.time()
        tr_all, te = f.train_index, f.test_index
        n_val = max(1, int(0.15 * len(tr_all)))
        rng = np.random.default_rng(20260928 + f.index)
        val_idx = rng.choice(tr_all, size=n_val, replace=False)
        tr_idx = np.setdiff1d(tr_all, val_idx)

        # --- baselines (identical row definitions to scripts/e3_baselines.py) ---
        clim = float(y_raw[tr_idx].mean())
        pers_raw = sup["y_lag"].to_numpy()[te]
        y_pers = np.where(np.isnan(pers_raw), clim, pers_raw)
        beta1 = ridge_fit(X_all[tr_idx][:, :1], y_raw[tr_idx]); y_cvss = ridge_predict(beta1, X_all[te][:, :1])
        beta7 = ridge_fit(X_all[tr_idx], y_raw[tr_idx]); y_ridge = ridge_predict(beta7, X_all[te])

        # --- HANFIS: average predictions across the 5 frozen seeds' best-of-3-restarts model ---
        hanfis_preds = []
        for seed in a.seeds:
            model, val = train_best_of_restarts(
                fit_hybrid_lower_alternating, lambda: HANFIS(m_raw=2, m_intermediate=3, mf_family="gauss", monotone=True),
                X_all[tr_idx], y01[tr_idx], X_all[val_idx], y01[val_idx], a.n_restarts, seed,
                epochs=a.epochs, patience=100, min_epochs=200, ridge=None)
            hanfis_preds.append(hanfis_predict(model, X_all[te]))
            print(f"fold {f.index}  HANFIS seed={seed}  best_val_mse={val:.5f}")
        y_hanfis = np.mean(hanfis_preds, axis=0) * 100.0

        # --- FlatANFISMatched: radius searched fresh on THIS fold's training data ---
        matched_preds = []
        for seed in a.seeds:
            try:
                torch.manual_seed(seed)
                model, search = build_matched(X_all[tr_idx])
            except ClusterSearchError as exc:
                print(f"fold {f.index}  FlatANFISMatched seed={seed}  ABORT: {exc}"); continue
            hist = fit_matched(model, X_all[tr_idx], y01[tr_idx], X_all[val_idx], y01[val_idx],
                               epochs=a.epochs, patience=100, min_epochs=200)
            matched_preds.append(matched_predict(model, X_all[te]))
            print(f"fold {f.index}  FlatANFISMatched seed={seed}  rules={search['n_rules']} "
                  f"params={search['n_params']} within_tol={search['within_tolerance']} "
                  f"best_val_mse={hist['best_validation_loss']:.5f}")
        y_matched = np.mean(matched_preds, axis=0) * 100.0 if matched_preds else np.full(len(te), np.nan)

        # --- full flat ANFIS reference (H2', reported without criteria) ---
        flat_preds = []
        for seed in a.seeds:
            torch.manual_seed(seed)
            flat = hanfis_models.SugenoANFIS(n_inputs=7, n_mfs=2)
            hist = hanfis_models.fit_anfis(flat, X_all[tr_idx], y01[tr_idx], X_all[val_idx], y01[val_idx],
                                          epochs=a.epochs, patience=60)
            flat_preds.append(hanfis_models.predict(flat, X_all[te]))
        y_flat_full = np.mean(flat_preds, axis=0) * 100.0

        for i, row_idx in enumerate(te):
            all_rows.append({"event_id": sup.iloc[row_idx]["event_id"], "image_id": sup.iloc[row_idx]["image_id"],
                             "fold": f.index, "y_true": y_raw[row_idx], "y_hanfis": y_hanfis[i],
                             "y_cvss_only": y_cvss[i], "y_persistence": y_pers[i], "y_ridge_7inputs": y_ridge[i],
                             "y_matched": y_matched[i], "y_flat_full": y_flat_full[i]})
        meta["fold_times_sec"][f.index] = round(time.time() - t0, 1)
        print(f"fold {f.index} done in {meta['fold_times_sec'][f.index]}s  ({len(te)} test rows)")

    out = Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    pd.DataFrame(all_rows).to_csv(out / f"predictions_{stamp}.csv", index=False)
    (out / f"meta_{stamp}.json").write_text(json.dumps(meta, indent=2, default=str), encoding="utf-8")
    print(f"\nwrote {out}/predictions_{stamp}.csv ({len(all_rows)} rows)")
    print("STATUS=E4_RUN_DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())

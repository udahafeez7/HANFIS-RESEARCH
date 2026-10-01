#!/usr/bin/env python
"""Per-row parity check: does hanfis_bottleneck.py's k=1 path reproduce A-09/E4? (patch 0061)

hanfis_bottleneck.py's module docstring claims "a k=1 run through this path should reproduce
A-09's actual numbers" (patch 0058). The pooled-skill comparison (A-23: E5 k=1 clamp-on 0.3339
vs E4 H1b 0.300) is encouraging but is an AGGREGATE comparison across different model instances
(different restarts/seeds consumed in a different order by a different class hierarchy); it
cannot by itself confirm the claim. This merges the two predictions files on event_id and
reports, per event_id: the two models should be evaluated on near-identical folds (same
GroupTimeSplit, same seed) but are NOT expected to produce bit-identical point predictions --
only to agree on accuracy at the aggregate level that the sign of H1b hinges on.

Do not read "two models produce different point predictions" as a failure by itself: five seeds
x three restarts, each drawing from torch's global RNG in a different order depending on model
construction (MultiHeadSugenoPanel vs SugenoPanel have different parameter counts and thus
consume different numbers of random draws before `solve_lower_alternating`/Adam ever run), will
diverge even for a mathematically identical scheme. What matters here is whether the fold
assignment is identical (event_id -> fold must match; if it doesn't, the two runs are not
comparable at all) and whether the per-fold RMSE/skill gap stays within noise.

  python scripts/e5_e4_parity.py results_python/e5/e5_predictions_20261001T061220Z.csv \
      results_python/e4/predictions_20261001T040745Z.csv
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("e5_predictions", help="e5_predictions_<stamp>.csv, filtered internally to k=1")
    p.add_argument("e4_predictions", help="results_python/e4/predictions_<stamp>.csv")
    p.add_argument("--k", type=int, default=1, help="which k from the E5 file to compare (default 1)")
    p.add_argument("--out-dir", default=None)
    a = p.parse_args(argv)

    e5 = pd.read_csv(a.e5_predictions)
    e5 = e5[e5["k"] == a.k].copy()
    e4 = pd.read_csv(a.e4_predictions)
    for col, df, name in (("event_id", e5, "e5"), ("event_id", e4, "e4")):
        if col not in df.columns:
            raise SystemExit(f"{name} file has no '{col}' column -- cannot merge")

    n5, n4 = len(e5), len(e4)
    m = e5.merge(e4, on="event_id", suffixes=("_e5", "_e4"), how="inner")
    print(f"e5 (k={a.k}) rows: {n5}  e4 rows: {n4}  matched on event_id: {len(m)}")
    if len(m) == 0:
        raise SystemExit("no overlapping event_id between the two files -- different folds/inventory?")
    only_e5 = set(e5["event_id"]) - set(e4["event_id"])
    only_e4 = set(e4["event_id"]) - set(e5["event_id"])
    if only_e5 or only_e4:
        print(f"WARNING: {len(only_e5)} event_id only in e5, {len(only_e4)} only in e4 -- "
              f"the two sweeps did not test exactly the same rows. If this is large relative "
              f"to {len(m)} matched rows, the two runs used different folds and are not comparable.")

    y_col_e5 = "y" if "y" in m.columns else ("y_e5" if "y_e5" in m.columns else None)
    y_col_e4 = next((c for c in ("y_true", "y_e4") if c in m.columns), None)
    if y_col_e5 is None or y_col_e4 is None:
        raise SystemExit(f"could not find the label columns after merge; columns are {list(m.columns)}")
    y5, y4 = m[y_col_e5].to_numpy(dtype=float), m[y_col_e4].to_numpy(dtype=float)
    if not np.allclose(y5, y4, atol=1e-6):
        bad = int(np.sum(~np.isclose(y5, y4, atol=1e-6)))
        print(f"WARNING: labels disagree on {bad}/{len(m)} matched rows (max |diff| = {np.max(np.abs(y5 - y4)):.4f}) "
              f"-- the two files may be scoring different target definitions or snapshots.")

    yh_col_e5 = "y_hanfis" if "y_hanfis" in m.columns else "y_hanfis_e5"
    yh_col_e4 = "y_hanfis" if "y_hanfis" in m.columns else "y_hanfis_e4"
    yh5, yh4 = m[yh_col_e5].to_numpy(dtype=float), m[yh_col_e4].to_numpy(dtype=float)
    diff = yh5 - yh4
    corr = float(np.corrcoef(yh5, yh4)[0, 1]) if len(m) > 1 else float("nan")
    print("\npoint predictions (NOT expected to be identical -- different restarts/seeds consumed differently):")
    print(f"  pearson r = {corr:.4f}   mean diff = {diff.mean():.4f}   mean |diff| = {np.abs(diff).mean():.4f}   "
          f"rmse of diff = {np.sqrt(np.mean(diff ** 2)):.4f}")

    fold_col_e5 = "fold" if "fold" in m.columns else "fold_e5"
    fold_col_e4 = "fold" if "fold" in m.columns else "fold_e4"
    if fold_col_e5 in m.columns and fold_col_e4 in m.columns:
        mismatch = int((m[fold_col_e5] != m[fold_col_e4]).sum())
        print(f"\nfold assignment: {mismatch}/{len(m)} rows assigned to a DIFFERENT fold between e5 and e4"
              f"{'  <-- the two runs are NOT on the same splits' if mismatch else '  (identical)'}")

    rows = []
    for fold, g in m.groupby(fold_col_e4 if fold_col_e4 in m.columns else fold_col_e5):
        yy = g[y_col_e4].to_numpy(dtype=float)
        a5 = g[yh_col_e5].to_numpy(dtype=float); a4 = g[yh_col_e4].to_numpy(dtype=float)
        rmse5 = float(np.sqrt(np.mean((a5 - yy) ** 2))); rmse4 = float(np.sqrt(np.mean((a4 - yy) ** 2)))
        rows.append({"fold": fold, "n": len(g), "rmse_e5_k1": round(rmse5, 4), "rmse_e4": round(rmse4, 4),
                     "rmse_diff": round(rmse5 - rmse4, 4)})
    per_fold = pd.DataFrame(rows)
    print("\nper-fold RMSE, e5 (k=1, clamp on) vs e4:")
    print(per_fold.to_string(index=False))

    out = Path(a.out_dir) if a.out_dir else Path(a.e5_predictions).parent
    stem = Path(a.e5_predictions).stem.replace("e5_predictions_", "")
    per_fold.to_csv(out / f"e5_e4_parity_{stem}.csv", index=False)
    print(f"\nwrote {out}/e5_e4_parity_{stem}.csv")
    print("STATUS=E5_E4_PARITY_DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())

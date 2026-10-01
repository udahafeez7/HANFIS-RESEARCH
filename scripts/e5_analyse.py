#!/usr/bin/env python
"""E5 analysis (patch 0060): image-clustered bootstrap CIs for the bottleneck sweep.

e5_sweep.py reports point estimates. The E4 preregistration scores skill on the POOLED MSE
over all test rows with a bootstrap clustered by image (2,000 resamples); this script applies
the same machinery to the sweep's per-row predictions so the k=1 vs k=2 comparison gets an
interval instead of a per-fold vote, and so the sweep's k=1 number can be laid beside the
confirmatory E4 H1b number on the same scale.

Reported per k:
  ss_pers_pooled with a 95% CI, and rmse_pooled.
Reported per ordered pair of k values (paired on the SAME resampled images, so the two models
share their sampling noise):
  d_ss = ss(k_a) - ss(k_b) with a 95% CI, and the share of resamples with d_ss > 0.

The CI is the thing that decides whether "k=2 is worse in 4 of 5 folds" (sign test p = 0.375,
which cannot reach significance with five folds) is a finding or noise. Per-fold skill ratios
are NOT averaged here -- on near-static test blocks mse_pers approaches 0 and the ratio
explodes; see A-22.

  python scripts/e5_analyse.py results_python/e5/e5_predictions_20261001T063307Z.csv
  python scripts/e5_analyse.py A.csv --compare B.csv --label-a "clamp off" --label-b "clamp on"

--compare restricts BOTH files to their common event_ids at the same k and reports the paired
difference between files (e.g. clamp_intermediates off vs on at k=1), which is the clean way to
price a single code change rather than diffing two summary tables.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

N_BOOT = 2000
BOOT_SEED = 20260928


def _skill(y, y_hat, y_ref):
    mse = float(np.mean((y_hat - y) ** 2))
    mse_ref = float(np.mean((y_ref - y) ** 2))
    return (1 - mse / mse_ref) if mse_ref > 0 else float("nan"), float(np.sqrt(mse))


def _bootstrap_indices(groups: np.ndarray, n_boot: int, seed: int) -> list[np.ndarray]:
    """Resample IMAGES with replacement (clustered bootstrap), return row indices per resample."""
    uniq = np.unique(groups)
    by_group = {g: np.flatnonzero(groups == g) for g in uniq}
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(n_boot):
        drawn = rng.choice(uniq, size=len(uniq), replace=True)
        out.append(np.concatenate([by_group[g] for g in drawn]))
    return out


def _ci(samples: np.ndarray) -> tuple[float, float]:
    good = samples[np.isfinite(samples)]
    if good.size == 0:
        return float("nan"), float("nan")
    return float(np.percentile(good, 2.5)), float(np.percentile(good, 97.5))


def load(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    missing = {"event_id", "image_id", "k", "fold", "y", "y_pers", "y_hanfis"} - set(df.columns)
    if missing:
        raise SystemExit(f"{path}: missing columns {sorted(missing)} -- is this an e5_predictions file?")
    return df


def analyse_single(df: pd.DataFrame, n_boot: int, seed: int) -> pd.DataFrame:
    rows = []
    for k, g in df.groupby("k"):
        y, yh, yp, grp = g["y"].to_numpy(), g["y_hanfis"].to_numpy(), g["y_pers"].to_numpy(), g["image_id"].to_numpy()
        ss, rmse = _skill(y, yh, yp)
        boots = np.array([_skill(y[i], yh[i], yp[i])[0] for i in _bootstrap_indices(grp, n_boot, seed)])
        lo, hi = _ci(boots)
        rows.append({"k": int(k), "n_test": len(g), "n_images": int(g["image_id"].nunique()),
                     "rmse_pooled": round(rmse, 4), "rmse_pers_pooled": round(float(np.sqrt(np.mean((yp - y) ** 2))), 4),
                     "ss_pers_pooled": round(ss, 4), "ci_lo": round(lo, 4), "ci_hi": round(hi, 4),
                     "lower_bound_above_0": bool(lo > 0)})
    return pd.DataFrame(rows).set_index("k")


def analyse_pairs(df: pd.DataFrame, n_boot: int, seed: int) -> pd.DataFrame:
    ks = sorted(df["k"].unique())
    rows = []
    for a, b in [(x, y) for i, x in enumerate(ks) for y in ks[i + 1:]]:
        ga, gb = df[df["k"] == a], df[df["k"] == b]
        common = np.intersect1d(ga["event_id"].to_numpy(), gb["event_id"].to_numpy())
        ga = ga[ga["event_id"].isin(common)].sort_values("event_id")
        gb = gb[gb["event_id"].isin(common)].sort_values("event_id")
        if not np.array_equal(ga["event_id"].to_numpy(), gb["event_id"].to_numpy()):
            raise SystemExit(f"k={a} and k={b} do not line up on event_id after intersection")
        y, yp, grp = ga["y"].to_numpy(), ga["y_pers"].to_numpy(), ga["image_id"].to_numpy()
        if not (np.allclose(y, gb["y"].to_numpy()) and np.allclose(yp, gb["y_pers"].to_numpy())):
            raise SystemExit(f"k={a} and k={b} disagree on y or y_pers for the same event_ids -- the two "
                             f"sweeps did not use the same folds/labels, so they cannot be paired")
        ya, yb = ga["y_hanfis"].to_numpy(), gb["y_hanfis"].to_numpy()
        d = _skill(y, ya, yp)[0] - _skill(y, yb, yp)[0]
        boots = np.array([_skill(y[i], ya[i], yp[i])[0] - _skill(y[i], yb[i], yp[i])[0]
                          for i in _bootstrap_indices(grp, n_boot, seed)])
        lo, hi = _ci(boots)
        rows.append({"comparison": f"k={a} minus k={b}", "n_test": len(ga), "d_ss": round(d, 4),
                     "ci_lo": round(lo, 4), "ci_hi": round(hi, 4),
                     "share_d_gt_0": round(float(np.mean(boots[np.isfinite(boots)] > 0)), 4),
                     "separated_from_0": bool(lo > 0 or hi < 0)})
    return pd.DataFrame(rows)


def analyse_files(df_a: pd.DataFrame, df_b: pd.DataFrame, la: str, lb: str, n_boot: int, seed: int) -> pd.DataFrame:
    rows = []
    for k in sorted(set(df_a["k"]) & set(df_b["k"])):
        ga, gb = df_a[df_a["k"] == k], df_b[df_b["k"] == k]
        common = np.intersect1d(ga["event_id"].to_numpy(), gb["event_id"].to_numpy())
        ga = ga[ga["event_id"].isin(common)].sort_values("event_id")
        gb = gb[gb["event_id"].isin(common)].sort_values("event_id")
        y, yp, grp = ga["y"].to_numpy(), ga["y_pers"].to_numpy(), ga["image_id"].to_numpy()
        ya, yb = ga["y_hanfis"].to_numpy(), gb["y_hanfis"].to_numpy()
        if not np.allclose(y, gb["y"].to_numpy()):
            raise SystemExit(f"k={k}: the two files disagree on y for common event_ids")
        d = _skill(y, ya, yp)[0] - _skill(y, yb, yp)[0]
        boots = np.array([_skill(y[i], ya[i], yp[i])[0] - _skill(y[i], yb[i], yp[i])[0]
                          for i in _bootstrap_indices(grp, n_boot, seed)])
        lo, hi = _ci(boots)
        rows.append({"k": int(k), "comparison": f"{la} minus {lb}", "n_common": len(ga), "d_ss": round(d, 4),
                     "ci_lo": round(lo, 4), "ci_hi": round(hi, 4), "separated_from_0": bool(lo > 0 or hi < 0)})
    return pd.DataFrame(rows)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("predictions", help="e5_predictions_<stamp>.csv")
    p.add_argument("--compare", help="a second e5_predictions file to difference against, on common event_ids")
    p.add_argument("--label-a", default="A"); p.add_argument("--label-b", default="B")
    p.add_argument("--n-boot", type=int, default=N_BOOT); p.add_argument("--seed", type=int, default=BOOT_SEED)
    p.add_argument("--out-dir", default=None)
    a = p.parse_args(argv)

    df = load(Path(a.predictions))
    per_k = analyse_single(df, a.n_boot, a.seed)
    print(f"\nPer k -- pooled skill vs persistence, {a.n_boot} image-clustered resamples")
    print(per_k.to_string())
    pairs = analyse_pairs(df, a.n_boot, a.seed)
    if not pairs.empty:
        print("\nPaired differences between k values (same resampled images for both)")
        print(pairs.to_string(index=False))

    cmp_tbl = None
    if a.compare:
        cmp_tbl = analyse_files(df, load(Path(a.compare)), a.label_a, a.label_b, a.n_boot, a.seed)
        print(f"\nBetween files on common event_ids: {a.label_a} vs {a.label_b}")
        print(cmp_tbl.to_string(index=False))

    out = Path(a.out_dir) if a.out_dir else Path(a.predictions).parent
    stem = Path(a.predictions).stem.replace("e5_predictions_", "")
    per_k.to_csv(out / f"e5_skill_ci_{stem}.csv")
    if not pairs.empty:
        pairs.to_csv(out / f"e5_pairs_{stem}.csv", index=False)
    if cmp_tbl is not None:
        cmp_tbl.to_csv(out / f"e5_filediff_{stem}.csv", index=False)
    print(f"\nwrote {out}/e5_skill_ci_{stem}.csv")
    print("STATUS=E5_ANALYSE_DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())

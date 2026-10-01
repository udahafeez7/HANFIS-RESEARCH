#!/usr/bin/env python
"""E4 analysis (patch 0050): pooled skill scores with group-clustered bootstrap CIs and Holm
correction, per protocols/E4_preregistration_2026-09-29.md's "Analisis statistik" section.

Reads per-row predictions written by scripts/e4_run.py (one row per test observation, per
method, per seed -- seeds already averaged into one prediction per row before this stage) and
computes, on the raw label scale:

  SS_ref = 1 - MSE_HANFIS / MSE_ref   for ref in {cvss_only, persistence, ridge_7inputs, matched}

CI: group-clustered bootstrap -- resample IMAGES (not rows) with replacement, 2000 times, so
rows from the same image (which are highly correlated) are resampled as a unit rather than
independently, per the preregistration's explicit rationale.

Multiplicity: Holm-Bonferroni across the family {H1a: cvss, H1b: persistence, H1c: ridge_7inputs,
H2: matched}, on the one-sided p-value (share of bootstrap draws with SS_ref <= 0).

Input CSV columns required: image_id, y_true, y_hanfis, y_cvss_only, y_persistence,
y_ridge_7inputs, y_matched. Rows with any NaN prediction are dropped and reported, not silently
included.
"""
from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path

import numpy as np
import pandas as pd

REFS = ["cvss_only", "persistence", "ridge_7inputs", "matched"]
HYPOTHESIS_LABEL = {"cvss_only": "H1a", "persistence": "H1b", "ridge_7inputs": "H1c", "matched": "H2"}
SESOI = {"cvss_only": 0.10, "persistence": 0.05, "ridge_7inputs": 0.0, "matched": -0.05}  # non-inferiority margins per prereg


def mse_by_image(df: pd.DataFrame, pred_col: str) -> pd.Series:
    """Per-image mean squared error for one prediction column."""
    err2 = (df["y_true"] - df[pred_col]) ** 2
    return err2.groupby(df["image_id"]).mean()


def pooled_mse(df: pd.DataFrame, pred_col: str, image_weight: pd.Series | None = None) -> float:
    """Row-pooled MSE (every held-out row weighted equally), matching E3's convention."""
    return float(np.mean((df["y_true"] - df[pred_col]) ** 2))


def bootstrap_skill_scores(df: pd.DataFrame, n_boot: int = 2000, seed: int = 20260928) -> dict:
    images = df["image_id"].unique()
    rng = np.random.default_rng(seed)
    # Precompute, per image, the row indices -- resampling images means resampling these blocks.
    idx_by_image = {img: df.index[df["image_id"] == img].to_numpy() for img in images}
    boot_ss = {ref: [] for ref in REFS}
    point_mse = {"hanfis": pooled_mse(df, "y_hanfis"), **{r: pooled_mse(df, f"y_{r}") for r in REFS}}
    point_ss = {r: 1 - point_mse["hanfis"] / point_mse[r] for r in REFS}
    n_img = len(images)
    for b in range(n_boot):
        draw = rng.choice(images, size=n_img, replace=True)
        rows = np.concatenate([idx_by_image[img] for img in draw])
        sub = df.loc[rows]
        mse_h = float(np.mean((sub["y_true"] - sub["y_hanfis"]) ** 2))
        for ref in REFS:
            mse_r = float(np.mean((sub["y_true"] - sub[f"y_{ref}"]) ** 2))
            boot_ss[ref].append(1 - mse_h / mse_r if mse_r > 0 else np.nan)
    result = {}
    for ref in REFS:
        arr = np.array(boot_ss[ref]); arr = arr[np.isfinite(arr)]
        ci_lo, ci_hi = np.percentile(arr, [2.5, 97.5])
        # one-sided bootstrap p-value: share of draws at or below the non-inferiority margin
        margin = SESOI[ref]
        p_boot = float(np.mean(arr <= margin))
        result[ref] = {"hypothesis": HYPOTHESIS_LABEL[ref], "ss_point": point_ss[ref],
                      "ci_lo": float(ci_lo), "ci_hi": float(ci_hi), "sesoi_or_margin": margin,
                      "p_boot_at_margin": p_boot, "n_boot_valid": int(len(arr))}
    return result


def holm_correction(results: dict) -> dict:
    """Holm-Bonferroni step-down on p_boot_at_margin across the four-hypothesis family."""
    items = sorted(results.items(), key=lambda kv: kv[1]["p_boot_at_margin"])
    m = len(items)
    running_max = 0.0
    for rank, (ref, r) in enumerate(items):
        adj = (m - rank) * r["p_boot_at_margin"]
        running_max = max(running_max, adj)
        r["p_holm"] = min(1.0, running_max)
        r["confirmed"] = (r["ci_lo"] > r["sesoi_or_margin"]) and (r["p_holm"] < 0.05)
    return dict(items)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--predictions", required=True, help="CSV written by scripts/e4_run.py")
    p.add_argument("--n-boot", type=int, default=2000)
    p.add_argument("--out-dir", default="results_python/e4")
    a = p.parse_args(argv)

    df = pd.read_csv(a.predictions)
    need = {"image_id", "y_true", "y_hanfis", *[f"y_{r}" for r in REFS]}
    missing = need - set(df.columns)
    if missing:
        raise SystemExit(f"ABORT: predictions CSV missing columns: {sorted(missing)}")
    n0 = len(df)
    df = df.dropna(subset=list(need))
    if len(df) < n0:
        print(f"WARN: dropped {n0 - len(df)} row(s) with a missing prediction, out of {n0}")

    results = bootstrap_skill_scores(df, n_boot=a.n_boot)
    results = holm_correction(results)

    flat_full_mse = None
    if "y_flat_full" in df.columns and df["y_flat_full"].notna().any():
        mse_hanfis = pooled_mse(df, "y_hanfis")
        flat_full_mse = pooled_mse(df, "y_flat_full")
        flat_full_ss = 1 - mse_hanfis / flat_full_mse if flat_full_mse > 0 else float("nan")

    out = Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    summary_rows = [{"ref": ref, **r} for ref, r in results.items()]
    if flat_full_mse is not None:
        summary_rows.append({"ref": "flat_full", "hypothesis": "H2'", "ss_point": flat_full_ss,
                             "ci_lo": None, "ci_hi": None, "sesoi_or_margin": None,
                             "p_boot_at_margin": None, "n_boot_valid": None, "p_holm": None, "confirmed": None})
    pd.DataFrame(summary_rows).to_csv(out / f"E4_skill_scores_{stamp}.csv", index=False)

    lines = ["# E4 hasil (draf otomatis)", ""]
    for ref, r in results.items():
        verdict = "TERKONFIRMASI" if r["confirmed"] else "belum terkonfirmasi"
        lines.append(f"- **{r['hypothesis']}** ({ref}): SS = {r['ss_point']:.4f} "
                     f"[{r['ci_lo']:.4f}, {r['ci_hi']:.4f}], p_Holm = {r['p_holm']:.4f} -> {verdict}")
    if flat_full_mse is not None:
        lines.append(f"- **H2\u2032** (flat ANFIS penuh, referensi tanpa kriteria): SS = {flat_full_ss:.4f} "
                     f"(MSE flat penuh = {flat_full_mse:.4f}) -- dilaporkan, tidak diuji")
    (out / f"E4_report_{stamp}.md").write_text("\n".join(lines), encoding="utf-8")

    print("\n".join(lines))
    print(f"\nwrote {out}/E4_skill_scores_{stamp}.csv and E4_report_{stamp}.md")
    print("STATUS=E4_ANALYSE_DONE")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())

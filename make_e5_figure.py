#!/usr/bin/env python3
"""
Regenerate fig_e5_bottleneck_curve.pdf on the 120-asset E5 re-run (A-36),
reading directly from the analysed skill-CI CSV so the figure can't drift
from the actual numbers.

This ALSO fixes a pre-existing bug independent of today's 120-asset update:
the file previously at manuscript/fig_e5_bottleneck_curve.pdf showed raw
RMSE (2.5-20 range) titled "confounded, see text" -- it did not match its
own LaTeX caption at all, which describes a skill-score-vs-k plot with 95%
CIs. This script produces the figure the caption actually describes:
SS_pers for k=1 and k=2 with their 95% image-clustered bootstrap CIs.

Run from repo root (/mnt/c/Research/ANFIS), after copying this script there:
    python3 make_e5_figure.py
"""
import sys
from pathlib import Path

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

CI_CSV = Path("results_python/e5_120/e5_skill_ci_20261006T043146Z.csv")
OUT_PDF = Path("manuscript/fig_e5_bottleneck_curve.pdf")


def main() -> None:
    if not CI_CSV.exists():
        sys.exit(f"ERROR: {CI_CSV} not found -- run from repo root. "
                  f"No figure written.")

    df = pd.read_csv(CI_CSV).set_index("k")
    for k in (1, 2):
        if k not in df.index:
            sys.exit(f"ERROR: k={k} row missing from {CI_CSV}. No figure written.")

    ks = [1, 2]
    ss = [df.loc[k, "ss_pers_pooled"] for k in ks]
    lo = [df.loc[k, "ci_lo"] for k in ks]
    hi = [df.loc[k, "ci_hi"] for k in ks]
    err_lo = [s - l for s, l in zip(ss, lo)]
    err_hi = [h - s for h, s in zip(hi, ss)]

    fig, ax = plt.subplots(figsize=(6, 4.2))
    colors = ["#1f77b4" if l > 0 or h < 0 else "#7f7f7f" for l, h in zip(lo, hi)]
    # k=1 CI crosses zero (grey = not significant); k=2 CI entirely negative
    # (still colored to flag significance, but in the "bad" direction) --
    # use red specifically for an entirely-negative CI to visually flag harm.
    colors = []
    for l, h in zip(lo, hi):
        if l > 0:
            colors.append("#1f77b4")   # significant positive
        elif h < 0:
            colors.append("#d62728")   # significant negative
        else:
            colors.append("#7f7f7f")   # crosses zero, not significant

    ax.errorbar(ks, ss, yerr=[err_lo, err_hi], fmt="o", markersize=9,
                capsize=6, linewidth=2, ecolor="black", mfc="white",
                mec="black", zorder=3)
    for k, s, c in zip(ks, ss, colors):
        ax.plot(k, s, "o", markersize=9, color=c, zorder=4)

    ax.axhline(0, color="black", linewidth=0.8, linestyle="--", zorder=1)
    ax.set_xticks(ks)
    ax.set_xticklabels([f"$k={k}$" for k in ks])
    ax.set_xlim(0.5, 2.5)
    ax.set_xlabel("Bottleneck width $k$")
    ax.set_ylabel(r"Skill vs. persistence ($SS_{pers}$)")
    ax.set_title("E5: pooled skill vs. persistence, 120 assets\n"
                  "(95% image-clustered bootstrap CI)")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()

    OUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_PDF)
    print(f"OK: wrote {OUT_PDF} from {CI_CSV}")
    for k, s, l, h in zip(ks, ss, lo, hi):
        print(f"    k={k}: SS_pers={s:.3f} [{l:.3f}, {h:.3f}]")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Regenerate fig_e3_baselines.pdf on the 120-asset E3 re-run (A-35), matching
the visual style of the original 27-image-pilot figure (same layout, colors,
in-bar value labels) with updated numbers.

Run from repo root (/mnt/c/Research/ANFIS), after copying this script there:
    python3 make_e3_figure.py

Reads results_python/e3_120/baselines_20261005T104644Z_pooled.csv directly
(raw scale rows only, matching the manuscript table's scope) rather than
hardcoding numbers, so the figure can't drift from the actual CSV.
"""
import csv
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

POOLED_CSV = Path("results_python/e3_120/baselines_20261005T104644Z_pooled.csv")
OUT_PDF = Path("manuscript/fig_e3_baselines.pdf")

ORDER = ["climatology", "cvss_only", "persistence", "ridge_7inputs"]
LABELS = {
    "climatology": "Climatology",
    "cvss_only": "Single\nCVSS",
    "persistence": "Persistence\n(4-week)",
    "ridge_7inputs": "Ridge\n(7 inputs)",
}
COLORS = {
    "climatology": "#cccccc",
    "cvss_only": "#cccccc",
    "persistence": "#1f77b4",
    "ridge_7inputs": "#2ca02c",
}


def main() -> None:
    if not POOLED_CSV.exists():
        sys.exit(f"ERROR: {POOLED_CSV} not found -- run from repo root. "
                  f"No figure written.")

    ss_clim = {}
    with open(POOLED_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["scale"] == "raw":
                ss_clim[row["baseline"]] = float(row["ss_clim_pooled"])

    missing = [b for b in ORDER if b not in ss_clim]
    if missing:
        sys.exit(f"ERROR: pooled CSV is missing raw-scale rows for "
                  f"{missing} -- refusing to plot an incomplete figure.")

    labels = [LABELS[b] for b in ORDER]
    values = [ss_clim[b] for b in ORDER]
    colors = [COLORS[b] for b in ORDER]

    fig, ax = plt.subplots(figsize=(7, 4.2))
    y_pos = range(len(ORDER))
    bars = ax.barh(list(y_pos), values, color=colors, height=0.6)
    ax.set_yticks(list(y_pos))
    ax.set_yticklabels(labels)
    ax.invert_yaxis()
    ax.set_xlabel(r"Skill score vs. climatology ($SS_{clim}$)")
    ax.set_xlim(0, 1.08)
    ax.set_title("E3: mandatory baselines, pooled over 5 folds, 120 assets (raw scale)")

    for bar, val in zip(bars, values):
        x = bar.get_width()
        ax.text(x + 0.012, bar.get_y() + bar.get_height() / 2,
                f"{val:.3f}", va="center", ha="left", fontsize=10)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()

    OUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_PDF)
    print(f"OK: wrote {OUT_PDF} from {POOLED_CSV}")
    print(f"    SS_clim used: {dict(zip(ORDER, values))}")


if __name__ == "__main__":
    main()

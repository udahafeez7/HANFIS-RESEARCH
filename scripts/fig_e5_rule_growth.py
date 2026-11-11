#!/usr/bin/env python
"""Figure: rule and parameter growth with bottleneck width k (grid-partitioned integration tier).

Analytic figure, no data: counts come from python_hanfis.hanfis_bottleneck.estimate_params with the frozen m=2, m_I=3.
Replaces the earlier figure whose in-plot label carried the raw LaTeX text '2{,}000'. Output: manuscript/fig_e5_rule_growth.pdf.

  python scripts/fig_e5_rule_growth.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python_hanfis"))
from hanfis_bottleneck import estimate_params  # noqa: E402

OUT = ROOT / "manuscript" / "fig_e5_rule_growth.pdf"
MAX_PARAMS = 2000   # the --max-params default of scripts/e5_sweep.py


def main() -> int:
    ks = [1, 2, 3, 4]
    est = [estimate_params(2, 3, k) for k in ks]
    rules = [e["total_rules"] for e in est]; params = [e["total_params"] for e in est]
    refused = [k for k, e in zip(ks, est) if e["total_params"] > MAX_PARAMS]
    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    ax.plot(ks, rules, "o-", color="#5b2a86", lw=2, ms=8, label="Total rules")
    ax.plot(ks, params, "s--", color="#e4701e", lw=2, ms=8, label="Total parameters")
    if refused:
        ax.axvspan(min(refused) - 0.5, max(refused) + 0.3, color="#c0392b", alpha=0.08)
        ax.text(sum(refused) / len(refused), 3e4, f"refused\n(>{MAX_PARAMS:,}-param\nbudget)", ha="center", va="center", color="#c0392b", fontsize=9)
    ax.set_yscale("log"); ax.set_xticks(ks); ax.set_xlabel("Bottleneck width $k$"); ax.set_ylabel("Count (log scale)")
    ax.set_title("Rule and parameter growth under grid-partitioned integration", fontsize=11)
    ax.legend(loc="upper left", frameon=False); ax.set_xlim(0.8, 4.3)
    fig.tight_layout(); fig.savefig(OUT); print("written", OUT)
    for k, e in zip(ks, est):
        print(f"k={k}: rules {e['total_rules']}, params {e['total_params']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

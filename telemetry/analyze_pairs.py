#!/usr/bin/env python3
"""Paired ON-OFF analysis of tidy telemetry conditions (pre-registered plan, Run 17 preregistration).

Unit of analysis = complete run pair with both conditions gate_status == PASS.
For each metric: paired difference (ON - OFF) per pair, mean/median, bootstrap 95% CI
(10,000 resamples, seed fixed), exact two-sided sign-flip p-value, Cohen's dz.
Results are stratified by protocol; pairs from different protocols are never pooled
without the stratified table alongside (preregistration: "do not pool Run 17 with Runs 7-16").

p > 0.05 is reported as "failure to reject H0", never as equivalence.

Usage:
    python telemetry/analyze_pairs.py --tidy results_python/telemetry/tidy_conditions.csv \
        --output results_python/telemetry/paired_effects.csv
"""

from __future__ import annotations

import argparse
import itertools
from pathlib import Path

import numpy as np
import pandas as pd

METRICS = [
    "lat_mean_ms", "lat_median_ms", "lat_p95_ms", "lat_p99_ms",
    "cpu_utilization_percent_mean", "cpu_utilization_percent_p95_nearest_rank",
    "memory_utilization_percent_mean", "node_mean_cores",
    "mem_p0_mean_mib", "mem_monitoring_mean_mib", "tegra_cpu_pct_mean",
]


def exact_sign_flip_p(d: np.ndarray) -> float:
    """Exact two-sided permutation p-value for mean difference under sign symmetry."""
    d = d[~np.isnan(d)]
    n = len(d)
    if n == 0:
        return float("nan")
    observed = abs(d.mean())
    if n <= 20:
        count = 0
        for signs in itertools.product((1, -1), repeat=n):
            if abs((d * np.array(signs)).mean()) >= observed - 1e-12:
                count += 1
        return count / 2**n
    rng = np.random.default_rng(20260721)
    flips = rng.choice((1, -1), size=(20000, n))
    return float(((np.abs((flips * d).mean(1)) >= observed - 1e-12).mean()))


def bootstrap_ci(d: np.ndarray, n_boot: int = 10000, seed: int = 20260721) -> tuple[float, float]:
    d = d[~np.isnan(d)]
    if len(d) < 2:
        return float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(d), size=(n_boot, len(d)))
    means = d[idx].mean(1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def pair_table(tidy: pd.DataFrame) -> pd.DataFrame:
    ok = tidy[tidy["gate_status"] == "PASS"]
    on = ok[ok["condition"] == "ON"].set_index("pair_id")
    off = ok[ok["condition"] == "OFF"].set_index("pair_id")
    common = on.index.intersection(off.index)
    rows = []
    for pid in common:
        row = {"pair_id": pid, "run": on.loc[pid, "run"], "order": on.loc[pid, "order"], "protocol": on.loc[pid, "protocol"]}
        for m in METRICS:
            if m in on.columns and m in off.columns:
                row[f"{m}_on"] = on.loc[pid, m]
                row[f"{m}_off"] = off.loc[pid, m]
                row[f"{m}_diff"] = on.loc[pid, m] - off.loc[pid, m]
        rows.append(row)
    return pd.DataFrame(rows)


def effects(pairs: pd.DataFrame, label: str) -> list[dict]:
    out = []
    for m in METRICS:
        col = f"{m}_diff"
        if col not in pairs.columns:
            continue
        d = pairs[col].to_numpy(dtype=float)
        d = d[~np.isnan(d)]
        if len(d) == 0:
            continue
        lo, hi = bootstrap_ci(d)
        sd = d.std(ddof=1) if len(d) > 1 else float("nan")
        base = pairs[f"{m}_off"].to_numpy(dtype=float)
        rel = float(np.nanmean(d) / np.nanmean(base) * 100) if np.nanmean(base) else float("nan")
        out.append({
            "stratum": label, "metric": m, "n_pairs": int(len(d)),
            "diff_mean": float(d.mean()), "diff_median": float(np.median(d)), "diff_sd": float(sd),
            "ci95_low": lo, "ci95_high": hi, "relative_pct": rel,
            "sign_flip_p": exact_sign_flip_p(d), "p_floor": 2 / 2**len(d),
            "cohen_dz": float(d.mean() / sd) if sd and not np.isnan(sd) and sd > 0 else float("nan"),
            "verdict": "reject_H0" if exact_sign_flip_p(d) <= 0.05 else "fail_to_reject_H0",
        })
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tidy", type=Path, required=True)
    ap.add_argument("--output", type=Path, default=Path("results_python/telemetry/paired_effects.csv"))
    args = ap.parse_args()
    tidy = pd.read_csv(args.tidy)
    pairs = pair_table(tidy)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    pairs.to_csv(args.output.with_name("paired_table.csv"), index=False)
    rows = []
    for proto, grp in pairs.groupby("protocol"):
        rows += effects(grp, f"protocol={proto}")
    rows += effects(pairs, "ALL_protocols_pooled_(sensitivity_only)")
    res = pd.DataFrame(rows)
    res.to_csv(args.output, index=False)
    pd.set_option("display.width", 220)
    print(f"pairs analysed={len(pairs)} (conditions PASS both sides)")
    if len(res):
        print(res[["stratum", "metric", "n_pairs", "diff_mean", "ci95_low", "ci95_high", "relative_pct", "sign_flip_p", "p_floor", "verdict"]].round(4).to_string(index=False))
    print("NOTE: n_pairs < 6 cannot reach p <= 0.05 under exact sign-flip (p_floor); report as descriptive only.")


if __name__ == "__main__":
    main()

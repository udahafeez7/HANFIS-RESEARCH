#!/usr/bin/env python3
"""Aggregate independent HANFIS external-v3.0 ON/OFF run pairs.

The inferential unit is one complete counterbalanced run pair, never an
individual HTTP request or telemetry sample.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd


PAIR_RE = re.compile(r"^run(?P<run>\d+)-(?P<order>on-off|off-on)-")
PRIMARY_STATS = ("mean", "median", "p95", "p99")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def bootstrap_ci(values: np.ndarray, seed: int, repetitions: int) -> tuple[float, float]:
    """Deterministic percentile CI over independent run-level effects."""
    if len(values) < 2:
        return (math.nan, math.nan)
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, len(values), size=(repetitions, len(values)))
    means = values[indices].mean(axis=1)
    low, high = np.quantile(means, [0.025, 0.975])
    return float(low), float(high)


def exact_sign_flip_p(values: np.ndarray) -> float:
    """Two-sided exact randomization p-value for the mean paired effect."""
    clean = values[np.isfinite(values)]
    if len(clean) == 0 or len(clean) > 20:
        return math.nan
    observed = abs(float(clean.mean()))
    exceed = 0
    total = 2 ** len(clean)
    for signs in itertools.product((-1.0, 1.0), repeat=len(clean)):
        statistic = abs(float(np.mean(clean * np.asarray(signs))))
        if statistic >= observed - 1e-15:
            exceed += 1
    return exceed / total


def resolve_pairs(root: Path, requested_runs: list[int]) -> list[tuple[int, str, Path]]:
    candidates: dict[int, list[tuple[str, Path]]] = {}
    for directory in sorted(root.iterdir()):
        if not directory.is_dir():
            continue
        match = PAIR_RE.match(directory.name)
        if not match:
            continue
        run = int(match.group("run"))
        if requested_runs and run not in requested_runs:
            continue
        required = [
            directory / "analysis" / "pair_effects.csv",
            directory / "analysis" / "workload_summary.csv",
            directory / "analysis" / "analysis_summary.json",
        ]
        if all(path.is_file() for path in required):
            candidates.setdefault(run, []).append((match.group("order").upper(), directory))

    expected = requested_runs or sorted(candidates)
    resolved: list[tuple[int, str, Path]] = []
    for run in expected:
        matches = candidates.get(run, [])
        if not matches:
            raise SystemExit(f"Run {run}: no analyzed pair found beneath {root}")
        if len(matches) != 1:
            paths = ", ".join(str(item[1]) for item in matches)
            raise SystemExit(f"Run {run}: multiple analyzed pairs found; resolve ambiguity: {paths}")
        order, directory = matches[0]
        resolved.append((run, order, directory))
    if not resolved:
        raise SystemExit(f"No analyzed external-v3.0 pairs found beneath {root}")
    return resolved


def summarize_effects(frame: pd.DataFrame, seed: int, repetitions: int) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    groups = frame.groupby(["domain", "metric", "statistic"], sort=True)
    for (domain, metric, statistic), group in groups:
        differences = group["difference_on_minus_off"].to_numpy(dtype=float)
        percentages = group["percentage_change"].to_numpy(dtype=float)
        finite_percentages = percentages[np.isfinite(percentages)]
        ci_low, ci_high = bootstrap_ci(differences, seed, repetitions)
        rows.append(
            {
                "domain": domain,
                "metric": metric,
                "statistic": statistic,
                "n_pairs": len(group),
                "mean_off": float(group["off"].mean()),
                "mean_on": float(group["on"].mean()),
                "mean_difference_on_minus_off": float(np.mean(differences)),
                "median_difference_on_minus_off": float(np.median(differences)),
                "sd_difference": float(np.std(differences, ddof=1)) if len(group) > 1 else math.nan,
                "bootstrap_95_ci_low": ci_low,
                "bootstrap_95_ci_high": ci_high,
                "mean_percentage_change": (
                    float(np.mean(finite_percentages))
                    if len(finite_percentages)
                    else math.nan
                ),
                "positive_effect_runs": int(np.sum(differences > 0)),
                "negative_effect_runs": int(np.sum(differences < 0)),
                "zero_effect_runs": int(np.sum(differences == 0)),
                "exact_sign_flip_p": exact_sign_flip_p(differences),
            }
        )
    return pd.DataFrame(rows)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Aggregate analyzed external-v3.0 ON/OFF run pairs."
    )
    parser.add_argument("runs_root", type=Path)
    parser.add_argument("--runs", type=int, nargs="*", default=[])
    parser.add_argument("--output", type=Path)
    parser.add_argument("--bootstrap", type=int, default=20_000)
    parser.add_argument("--seed", type=int, default=20260829)
    args = parser.parse_args()

    root = args.runs_root.resolve()
    if not root.is_dir():
        raise SystemExit(f"Runs root does not exist: {root}")
    requested = list(dict.fromkeys(args.runs))
    if requested != sorted(requested):
        raise SystemExit("--runs must be unique and ascending")
    pairs = resolve_pairs(root, requested)
    output = (args.output or root / "cumulative_analysis_v3").resolve()
    output.mkdir(parents=True, exist_ok=True)

    effect_frames: list[pd.DataFrame] = []
    workload_frames: list[pd.DataFrame] = []
    source_rows: list[dict[str, object]] = []

    for run, order, pair_dir in pairs:
        analysis = pair_dir / "analysis"
        summary = json.loads((analysis / "analysis_summary.json").read_text())
        if summary.get("protocol") != "external-v3.0":
            raise SystemExit(f"Run {run}: unexpected protocol {summary.get('protocol')!r}")
        if summary.get("http_off_rows") != 300 or summary.get("http_on_rows") != 300:
            raise SystemExit(f"Run {run}: HTTP completeness gate failed")
        if summary.get("server_off_node_rows") != 64 or summary.get("server_on_node_rows") != 64:
            raise SystemExit(f"Run {run}: server node completeness gate failed")

        effects = pd.read_csv(analysis / "pair_effects.csv")
        effects.insert(0, "order", order)
        effects.insert(0, "run", run)
        effects["pair_dir"] = str(pair_dir)
        effect_frames.append(effects)

        workload = pd.read_csv(analysis / "workload_summary.csv")
        workload.insert(0, "order", order)
        workload.insert(0, "run", run)
        workload_frames.append(workload)
        source_rows.append(
            {
                "run": run,
                "order": order,
                "pair_dir": str(pair_dir),
                "analysis_summary_sha256": sha256(analysis / "analysis_summary.json"),
                "pair_effects_sha256": sha256(analysis / "pair_effects.csv"),
            }
        )

    all_effects = pd.concat(effect_frames, ignore_index=True)
    all_workloads = pd.concat(workload_frames, ignore_index=True)
    cumulative = summarize_effects(all_effects, args.seed, args.bootstrap)
    primary_runs = all_effects[
        (all_effects["domain"] == "client_http")
        & (all_effects["metric"] == "latency_ms")
        & (all_effects["statistic"].isin(PRIMARY_STATS))
    ].copy()
    primary_summary = cumulative[
        (cumulative["domain"] == "client_http")
        & (cumulative["metric"] == "latency_ms")
        & (cumulative["statistic"].isin(PRIMARY_STATS))
    ].copy()

    all_effects.to_csv(output / "all_pair_effects.csv", index=False)
    primary_runs.to_csv(output / "primary_latency_by_run.csv", index=False)
    cumulative.to_csv(output / "cumulative_effect_summary.csv", index=False)
    primary_summary.to_csv(output / "primary_latency_cumulative_summary.csv", index=False)
    all_workloads.to_csv(output / "workload_summary_by_run.csv", index=False)
    pd.DataFrame(source_rows).to_csv(output / "source_manifest.csv", index=False)

    figure_files: list[str] = []
    try:
        import matplotlib.pyplot as plt

        figure_stats = ("mean", "p95", "p99")
        fig, axes = plt.subplots(1, 3, figsize=(13, 4.2), sharey=False)
        for axis, statistic in zip(axes, figure_stats):
            subset = primary_runs[primary_runs["statistic"] == statistic].sort_values("run")
            for row in subset.itertuples():
                axis.plot([0, 1], [row.off, row.on], marker="o", alpha=0.8)
            axis.set_xticks([0, 1], ["OFF", "ON"])
            axis.set_title(statistic.upper())
            axis.set_ylabel("Latency (ms)")
            axis.grid(axis="y", alpha=0.25)
        fig.suptitle(f"Paired latency across {len(pairs)} independent runs")
        fig.tight_layout()
        fig.savefig(output / "figure_paired_latency.png", dpi=220)
        plt.close(fig)
        figure_files.append("figure_paired_latency.png")

        fig, axis = plt.subplots(figsize=(8.5, 4.8))
        offsets = {"mean": -0.18, "p95": 0.0, "p99": 0.18}
        colors = {"mean": "#2563eb", "p95": "#d4a017", "p99": "#dc2626"}
        runs = sorted(primary_runs["run"].unique())
        for statistic in figure_stats:
            subset = primary_runs[primary_runs["statistic"] == statistic].set_index("run")
            axis.scatter(
                np.asarray(runs) + offsets[statistic],
                [subset.loc[run, "difference_on_minus_off"] for run in runs],
                label=statistic.upper(), color=colors[statistic], s=50,
            )
        axis.axhline(0, color="black", linewidth=1)
        axis.set_xticks(runs)
        axis.set_xlabel("Independent run pair")
        axis.set_ylabel("ON - OFF latency (ms)")
        axis.set_title("Run-level monitoring latency effects")
        axis.legend()
        axis.grid(axis="y", alpha=0.25)
        fig.tight_layout()
        fig.savefig(output / "figure_run_level_effects.png", dpi=220)
        plt.close(fig)
        figure_files.append("figure_run_level_effects.png")

        monitor = all_workloads[
            (all_workloads["component"] == "monitoring")
            & (all_workloads["condition"] == "ON")
            & (all_workloads["metric"].isin(["cpu_mcores", "memory_mib"]))
        ]
        fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.2))
        for axis, metric, label in [
            (axes[0], "cpu_mcores", "Mean CPU (millicores)"),
            (axes[1], "memory_mib", "Mean memory (MiB)"),
        ]:
            subset = monitor[monitor["metric"] == metric].sort_values("run")
            axis.bar(subset["run"].astype(str), subset["mean"], color="#d4a017")
            axis.set_xlabel("Independent run pair")
            axis.set_ylabel(label)
            axis.grid(axis="y", alpha=0.25)
        fig.suptitle("Monitoring workload footprint")
        fig.tight_layout()
        fig.savefig(output / "figure_monitoring_footprint.png", dpi=220)
        plt.close(fig)
        figure_files.append("figure_monitoring_footprint.png")
    except Exception as exc:
        (output / "figure_warning.txt").write_text(f"{type(exc).__name__}: {exc}\n")

    result = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "protocol": "external-v3.0",
        "inferential_unit": "complete ON/OFF run pair",
        "runs": [run for run, _, _ in pairs],
        "orders": {str(run): order for run, order, _ in pairs},
        "n_pairs": len(pairs),
        "bootstrap_repetitions": args.bootstrap,
        "bootstrap_seed": args.seed,
        "figures": figure_files,
        "interpretation_level": (
            "exploratory; fewer than five independent pairs"
            if len(pairs) < 5
            else "multi-pair cumulative analysis"
        ),
    }
    (output / "cumulative_analysis_summary.json").write_text(
        json.dumps(result, indent=2, allow_nan=True)
    )

    files_to_hash = sorted(
        path for path in output.iterdir()
        if path.is_file() and path.name != "cumulative_analysis_sha256.txt"
    )
    with (output / "cumulative_analysis_sha256.txt").open("w") as handle:
        for path in files_to_hash:
            handle.write(f"{sha256(path)}  {path.name}\n")

    print("\n=== ELIGIBLE PAIRS ===")
    print(pd.DataFrame(source_rows)[["run", "order", "pair_dir"]].to_string(index=False))
    print("\n=== PRIMARY CUMULATIVE LATENCY EFFECTS: ON - OFF ===")
    columns = [
        "statistic", "n_pairs", "mean_off", "mean_on",
        "mean_difference_on_minus_off", "mean_percentage_change",
        "bootstrap_95_ci_low", "bootstrap_95_ci_high", "exact_sign_flip_p",
    ]
    print(primary_summary[columns].round(4).to_string(index=False))
    print("\n=== MONITORING FOOTPRINT BY RUN ===")
    monitor_print = all_workloads[
        (all_workloads["component"] == "monitoring")
        & (all_workloads["condition"] == "ON")
        & (all_workloads["metric"].isin(["cpu_mcores", "memory_mib"]))
    ][["run", "order", "metric", "mean", "p95", "max"]]
    print(monitor_print.round(4).to_string(index=False))
    print(f"\nCUMULATIVE_ANALYSIS_DIR={output}")
    print(f"ELIGIBLE_PAIRS={len(pairs)}")
    print("STATUS=PASS_CUMULATIVE_ANALYSIS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

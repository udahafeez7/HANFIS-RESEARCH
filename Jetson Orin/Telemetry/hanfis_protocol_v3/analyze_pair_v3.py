#!/usr/bin/env python3
"""Analyze one synchronized HANFIS external-v3.0 ON/OFF pair."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd


def cpu_to_mcores(value: object) -> float:
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return np.nan
    if text.endswith("m"):
        return float(text[:-1])
    return float(text) * 1000.0


def memory_to_mib(value: object) -> float:
    text = str(value).strip()
    match = re.fullmatch(r"([\d.]+)(Ki|Mi|Gi|Ti|K|M|G|T)?", text)
    if not match:
        return np.nan
    number = float(match.group(1))
    unit = match.group(2) or ""
    factors = {
        "": 1.0 / (1024.0 * 1024.0),
        "Ki": 1.0 / 1024.0,
        "Mi": 1.0,
        "Gi": 1024.0,
        "Ti": 1024.0 * 1024.0,
        "K": 1000.0 / (1024.0 * 1024.0),
        "M": 1_000_000.0 / (1024.0 * 1024.0),
        "G": 1_000_000_000.0 / (1024.0 * 1024.0),
        "T": 1_000_000_000_000.0 / (1024.0 * 1024.0),
    }
    return number * factors[unit]


def percent_value(value: object) -> float:
    text = str(value).strip().rstrip("%")
    return float(text) if text else np.nan


def descriptive(values: pd.Series) -> dict[str, float]:
    clean = pd.to_numeric(values, errors="coerce").dropna()
    return {
        "n": int(len(clean)),
        "mean": float(clean.mean()),
        "median": float(clean.median()),
        "std": float(clean.std(ddof=1)),
        "p95": float(clean.quantile(0.95)),
        "p99": float(clean.quantile(0.99)),
        "min": float(clean.min()),
        "max": float(clean.max()),
    }


def parse_tegrastats(path: Path, condition: str) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for line in path.read_text().splitlines():
        ram = re.search(r"RAM\s+(\d+)/(\d+)MB", line)
        cpu = re.search(r"CPU\s+\[([^\]]+)\]", line)
        gpu = re.search(r"GR3D_FREQ\s+(\d+)%", line)
        cpu_values: list[float] = []
        if cpu:
            for token in cpu.group(1).split(","):
                token = token.strip()
                if token.lower() == "off":
                    cpu_values.append(0.0)
                else:
                    match = re.search(r"(\d+)%@", token)
                    if match:
                        cpu_values.append(float(match.group(1)))
        temperatures = {
            key: float(value)
            for key, value in re.findall(
                r"\b(cpu|gpu|tj)@([\d.]+)C", line
            )
        }
        power = re.search(r"VDD_IN\s+(\d+)mW/(\d+)mW", line)
        rows.append(
            {
                "condition": condition,
                "ram_used_mb": float(ram.group(1)) if ram else np.nan,
                "cpu_mean_pct": np.mean(cpu_values) if cpu_values else np.nan,
                "gpu_pct": float(gpu.group(1)) if gpu else np.nan,
                "cpu_temp_c": temperatures.get("cpu", np.nan),
                "gpu_temp_c": temperatures.get("gpu", np.nan),
                "tj_temp_c": temperatures.get("tj", np.nan),
                "vdd_in_mw": float(power.group(1)) if power else np.nan,
            }
        )
    return pd.DataFrame(rows)


def add_effect(
    rows: list[dict[str, object]],
    domain: str,
    metric: str,
    statistic: str,
    off: float,
    on: float,
) -> None:
    difference = on - off
    percentage = difference / off * 100.0 if off != 0 else np.nan
    rows.append(
        {
            "domain": domain,
            "metric": metric,
            "statistic": statistic,
            "off": off,
            "on": on,
            "difference_on_minus_off": difference,
            "percentage_change": percentage,
        }
    )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("pair_dir", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    pair_dir = args.pair_dir.resolve()
    output = (args.output or pair_dir / "analysis").resolve()
    output.mkdir(parents=True, exist_ok=True)

    conditions = {"OFF": pair_dir / "off", "ON": pair_dir / "on"}
    for condition, directory in conditions.items():
        if not directory.is_dir():
            raise SystemExit(f"Missing condition directory: {directory}")

    effects: list[dict[str, object]] = []
    http_frames: dict[str, pd.DataFrame] = {}
    http_summary_rows: list[dict[str, object]] = []

    for condition, directory in conditions.items():
        frame = pd.read_csv(directory / "client" / "http.csv")
        for column in ["http_code", "time_connect", "time_total", "size_bytes"]:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
        frame["condition"] = condition
        frame["latency_ms"] = frame["time_total"] * 1000.0
        frame["connect_ms"] = frame["time_connect"] * 1000.0
        http_frames[condition] = frame

        latency = descriptive(frame["latency_ms"])
        connection = descriptive(frame["connect_ms"])
        http_summary_rows.append(
            {
                "condition": condition,
                "requests": len(frame),
                "http_200": int((frame["http_code"] == 200).sum()),
                "failure_rate_pct": float((frame["http_code"] != 200).mean() * 100),
                **{f"latency_{key}": value for key, value in latency.items()},
                **{f"connect_{key}": value for key, value in connection.items()},
            }
        )

    http_summary = pd.DataFrame(http_summary_rows).set_index("condition")
    for metric in ["latency", "connect"]:
        for statistic in ["mean", "median", "p95", "p99"]:
            column = f"{metric}_{statistic}"
            add_effect(
                effects,
                "client_http",
                f"{metric}_ms",
                statistic,
                float(http_summary.loc["OFF", column]),
                float(http_summary.loc["ON", column]),
            )

    node_frames: list[pd.DataFrame] = []
    p0_samples: dict[str, pd.DataFrame] = {}
    monitoring_samples: dict[str, pd.DataFrame] = {}

    for condition, directory in conditions.items():
        nodes = pd.read_csv(directory / "server" / "nodes.csv")
        nodes["condition"] = condition
        nodes["cpu_mcores"] = nodes["cpu_cores"].map(cpu_to_mcores)
        nodes["cpu_pct_value"] = nodes["cpu_pct"].map(percent_value)
        nodes["memory_mib"] = nodes["memory_bytes"].map(memory_to_mib)
        nodes["memory_pct_value"] = nodes["memory_pct"].map(percent_value)
        node_frames.append(nodes)

        p0 = pd.read_csv(directory / "server" / "p0_containers.csv")
        p0["cpu_mcores"] = p0["cpu"].map(cpu_to_mcores)
        p0["memory_mib"] = p0["memory"].map(memory_to_mib)
        p0_samples[condition] = (
            p0.groupby("seq", as_index=False)[["cpu_mcores", "memory_mib"]].sum()
        )

        monitor_path = directory / "server" / "monitoring_containers.csv"
        monitor = pd.read_csv(monitor_path)
        if monitor.empty:
            monitoring_samples[condition] = pd.DataFrame(
                {"seq": range(1, 33), "cpu_mcores": 0.0, "memory_mib": 0.0}
            )
        else:
            monitor["cpu_mcores"] = monitor["cpu"].map(cpu_to_mcores)
            monitor["memory_mib"] = monitor["memory"].map(memory_to_mib)
            monitoring_samples[condition] = (
                monitor.groupby("seq", as_index=False)[["cpu_mcores", "memory_mib"]].sum()
            )

    nodes_all = pd.concat(node_frames, ignore_index=True)
    node_summary_rows: list[dict[str, object]] = []
    for (condition, node), frame in nodes_all.groupby(["condition", "node"]):
        for metric in ["cpu_mcores", "cpu_pct_value", "memory_mib", "memory_pct_value"]:
            stats = descriptive(frame[metric])
            node_summary_rows.append(
                {"condition": condition, "node": node, "metric": metric, **stats}
            )
    node_summary = pd.DataFrame(node_summary_rows)

    for node in sorted(nodes_all["node"].unique()):
        for metric in ["cpu_mcores", "memory_mib"]:
            subset = node_summary[(node_summary["node"] == node) & (node_summary["metric"] == metric)]
            for statistic in ["mean", "p95"]:
                off = float(subset.loc[subset["condition"] == "OFF", statistic].iloc[0])
                on = float(subset.loc[subset["condition"] == "ON", statistic].iloc[0])
                add_effect(effects, f"kubernetes_node:{node}", metric, statistic, off, on)

    workload_summary_rows: list[dict[str, object]] = []
    for component, samples in [("p0", p0_samples), ("monitoring", monitoring_samples)]:
        for condition, frame in samples.items():
            for metric in ["cpu_mcores", "memory_mib"]:
                stats = descriptive(frame[metric])
                workload_summary_rows.append(
                    {"component": component, "condition": condition, "metric": metric, **stats}
                )
        for metric in ["cpu_mcores", "memory_mib"]:
            for statistic in ["mean", "p95"]:
                off = descriptive(samples["OFF"][metric])[statistic]
                on = descriptive(samples["ON"][metric])[statistic]
                add_effect(effects, f"kubernetes_workload:{component}", metric, statistic, off, on)
    workload_summary = pd.DataFrame(workload_summary_rows)

    tegra_frames = {
        condition: parse_tegrastats(directory / "client" / "tegrastats.log", condition)
        for condition, directory in conditions.items()
    }
    tegra_all = pd.concat(tegra_frames.values(), ignore_index=True)
    tegra_summary_rows: list[dict[str, object]] = []
    tegra_metrics = [
        "ram_used_mb",
        "cpu_mean_pct",
        "gpu_pct",
        "cpu_temp_c",
        "gpu_temp_c",
        "tj_temp_c",
        "vdd_in_mw",
    ]
    for condition, frame in tegra_all.groupby("condition"):
        for metric in tegra_metrics:
            tegra_summary_rows.append(
                {"condition": condition, "metric": metric, **descriptive(frame[metric])}
            )
    tegra_summary = pd.DataFrame(tegra_summary_rows)
    for metric in tegra_metrics:
        subset = tegra_summary[tegra_summary["metric"] == metric]
        for statistic in ["mean", "p95"]:
            off = float(subset.loc[subset["condition"] == "OFF", statistic].iloc[0])
            on = float(subset.loc[subset["condition"] == "ON", statistic].iloc[0])
            add_effect(effects, "jetson_client", metric, statistic, off, on)

    effects_frame = pd.DataFrame(effects)
    http_combined = pd.concat(http_frames.values(), ignore_index=True)
    http_summary.to_csv(output / "http_summary.csv")
    effects_frame.to_csv(output / "pair_effects.csv", index=False)
    node_summary.to_csv(output / "node_summary.csv", index=False)
    workload_summary.to_csv(output / "workload_summary.csv", index=False)
    tegra_summary.to_csv(output / "jetson_summary.csv", index=False)

    figure_files: list[str] = []
    try:
        import matplotlib.pyplot as plt

        fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
        axes[0].boxplot(
            [http_frames["OFF"]["latency_ms"], http_frames["ON"]["latency_ms"]],
            labels=["OFF", "ON"],
            showfliers=True,
        )
        axes[0].set_title("Run latency distribution")
        axes[0].set_ylabel("Latency (ms)")

        for condition, color in [("OFF", "#64748b"), ("ON", "#d4a017")]:
            values = np.sort(http_frames[condition]["latency_ms"].to_numpy())
            probability = np.arange(1, len(values) + 1) / len(values)
            axes[1].plot(values, probability, label=condition, color=color)
        axes[1].set_title("Empirical CDF")
        axes[1].set_xlabel("Latency (ms)")
        axes[1].set_ylabel("Cumulative probability")
        axes[1].legend()
        fig.tight_layout()
        fig.savefig(output / "figure_latency.png", dpi=220)
        plt.close(fig)
        figure_files.append("figure_latency.png")

        fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
        labels = ["P0", "Monitoring"]
        off_cpu = [p0_samples["OFF"]["cpu_mcores"].mean(), monitoring_samples["OFF"]["cpu_mcores"].mean()]
        on_cpu = [p0_samples["ON"]["cpu_mcores"].mean(), monitoring_samples["ON"]["cpu_mcores"].mean()]
        off_mem = [p0_samples["OFF"]["memory_mib"].mean(), monitoring_samples["OFF"]["memory_mib"].mean()]
        on_mem = [p0_samples["ON"]["memory_mib"].mean(), monitoring_samples["ON"]["memory_mib"].mean()]
        x = np.arange(len(labels))
        width = 0.36
        axes[0].bar(x - width / 2, off_cpu, width, label="OFF", color="#64748b")
        axes[0].bar(x + width / 2, on_cpu, width, label="ON", color="#d4a017")
        axes[0].set_xticks(x, labels)
        axes[0].set_ylabel("Mean CPU (millicores)")
        axes[0].legend()
        axes[1].bar(x - width / 2, off_mem, width, label="OFF", color="#64748b")
        axes[1].bar(x + width / 2, on_mem, width, label="ON", color="#d4a017")
        axes[1].set_xticks(x, labels)
        axes[1].set_ylabel("Mean memory (MiB)")
        axes[1].legend()
        fig.tight_layout()
        fig.savefig(output / "figure_workload_resources.png", dpi=220)
        plt.close(fig)
        figure_files.append("figure_workload_resources.png")
    except Exception as exc:  # figures are useful but should not invalidate numeric analysis
        (output / "figure_warning.txt").write_text(f"{type(exc).__name__}: {exc}\n")

    primary = effects_frame[
        (effects_frame["domain"] == "client_http")
        & (effects_frame["metric"] == "latency_ms")
    ]
    result = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "pair_dir": str(pair_dir),
        "protocol": "external-v3.0",
        "http_off_rows": int(len(http_frames["OFF"])),
        "http_on_rows": int(len(http_frames["ON"])),
        "server_off_node_rows": int(len(nodes_all[nodes_all["condition"] == "OFF"])),
        "server_on_node_rows": int(len(nodes_all[nodes_all["condition"] == "ON"])),
        "primary_latency_effects": primary.to_dict(orient="records"),
        "figures": figure_files,
        "interpretation_level": "single-pair descriptive effect",
    }
    (output / "analysis_summary.json").write_text(json.dumps(result, indent=2, allow_nan=True))

    files_to_hash = sorted(path for path in output.iterdir() if path.is_file() and path.name != "analysis_sha256.txt")
    with (output / "analysis_sha256.txt").open("w") as handle:
        for path in files_to_hash:
            handle.write(f"{sha256(path)}  {path.name}\n")

    print("\n=== HTTP SUMMARY ===")
    print(http_summary.round(4).to_string())
    print("\n=== PRIMARY LATENCY EFFECTS: ON - OFF ===")
    print(primary.round(4).to_string(index=False))
    print("\n=== WORKLOAD RESOURCE SUMMARY ===")
    print(workload_summary.round(4).to_string(index=False))
    print(f"\nANALYSIS_DIR={output}")
    print("STATUS=PASS_PAIR_ANALYSIS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

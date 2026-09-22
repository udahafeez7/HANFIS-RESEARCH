#!/usr/bin/env python3
"""Consolidate HANFIS telemetry run pairs into one tidy table (one row per condition).

Reads the directory layout produced by run_pair_v4.sh:

    <root>/<pair_id>/{on,off}/server/{metadata.txt, utilization_summary.csv, utilization_samples.csv,
                                     cpu_summary.csv, memory_summary.csv, node_cpu_counter_delta.csv, sha256.txt}
    <root>/<pair_id>/{on,off}/client/{metadata.txt, http.csv, tegrastats.log, sha256.txt}

Fail-closed: a condition whose sha256.txt does not verify, whose http.csv is missing rows,
or whose metadata lacks RUN/CONDITION is kept in the table with gate_status != PASS and is
excluded from analysis by analyze_pairs.py. Nothing is imputed.

Usage:
    python telemetry/tidy_pairs.py --root "/mnt/c/Research/ANFIS/Jetson Orin/Telemetry/RunsV4" \
        --output results_python/telemetry/tidy_conditions.csv
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import re
import statistics
from pathlib import Path

import pandas as pd


def read_metadata(path: Path) -> dict:
    meta = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                meta[k.strip()] = v.strip()
    return meta


def verify_sha256(directory: Path) -> tuple[bool, str]:
    manifest = directory / "sha256.txt"
    if not manifest.exists():
        return False, "MISSING_SHA256"
    for line in manifest.read_text(encoding="utf-8").splitlines():
        parts = line.strip().split()
        if len(parts) < 2:
            continue
        digest, name = parts[0], parts[-1].lstrip("*")
        target = directory / name
        if not target.exists():
            return False, f"MISSING_FILE:{name}"
        actual = hashlib.sha256(target.read_bytes()).hexdigest()
        if actual != digest:
            return False, f"MISMATCH:{name}"
    return True, "OK"


def percentile_nearest_rank(values: list[float], q: float) -> float:
    if not values:
        return float("nan")
    s = sorted(values)
    k = max(1, int(round(q * len(s) + 0.5)))
    return s[min(k, len(s)) - 1]


def latency_stats(http_csv: Path) -> dict:
    out = {"http_rows": 0, "http_200": 0, "lat_mean_ms": float("nan"), "lat_median_ms": float("nan"),
           "lat_p95_ms": float("nan"), "lat_p99_ms": float("nan"), "connect_median_ms": float("nan")}
    if not http_csv.exists():
        return out
    df = pd.read_csv(http_csv)
    out["http_rows"] = int(len(df))
    out["http_200"] = int((df["http_code"] == 200).sum()) if "http_code" in df else 0
    ok = df[df["http_code"] == 200] if "http_code" in df else df
    if len(ok):
        t = (ok["time_total"].astype(float) * 1000).tolist()
        out.update(lat_mean_ms=statistics.fmean(t), lat_median_ms=statistics.median(t),
                   lat_p95_ms=percentile_nearest_rank(t, 0.95), lat_p99_ms=percentile_nearest_rank(t, 0.99),
                   connect_median_ms=statistics.median((ok["time_connect"].astype(float) * 1000).tolist()))
    return out


def utilization_stats(server: Path) -> dict:
    out = {}
    summ = server / "utilization_summary.csv"
    if summ.exists():
        df = pd.read_csv(summ)
        for _, row in df.iterrows():
            metric = str(row["metric"])
            for col in ("mean", "median", "p95_nearest_rank", "max"):
                val = row.get(col)
                if pd.notna(val) and str(val) != "":
                    out[f"{metric}_{col}"] = float(val)
    samples = server / "utilization_samples.csv"
    out["utilization_samples"] = int(len(pd.read_csv(samples))) if samples.exists() else 0
    return out


def memory_stats(server: Path) -> dict:
    out = {}
    path = server / "memory_summary.csv"
    if path.exists():
        df = pd.read_csv(path)
        for _, row in df.iterrows():
            g = str(row["group"])
            out[f"mem_{g}_mean_mib"] = float(row["mean_bytes"]) / 2**20
            out[f"mem_{g}_p95_mib"] = float(row["p95_bytes"]) / 2**20
    return out


def cpu_stats(server: Path) -> dict:
    out = {}
    path = server / "cpu_summary.csv"
    if path.exists():
        df = pd.read_csv(path)
        group_col = "group" if "group" in df.columns else df.columns[0]
        for _, row in df.iterrows():
            g = str(row[group_col])
            for col in df.columns:
                if col != group_col and pd.api.types.is_numeric_dtype(df[col]):
                    out[f"cpu_{g}_{col}"] = float(row[col])
    node = server / "node_cpu_counter_delta.csv"
    if node.exists():
        df = pd.read_csv(node)
        if len(df):
            out["node_cpu_delta_seconds"] = float(df["delta_cpu_seconds"].iloc[0])
            out["node_elapsed_seconds"] = float(df["elapsed_seconds"].iloc[0])
            out["node_mean_cores"] = out["node_cpu_delta_seconds"] / out["node_elapsed_seconds"] if out["node_elapsed_seconds"] else float("nan")
    return out


def tegrastats_stats(log: Path) -> dict:
    """Very small parser: RAM used MiB and mean CPU % across cores from tegrastats lines."""
    out = {"tegra_rows": 0, "tegra_ram_used_mib_mean": float("nan"), "tegra_cpu_pct_mean": float("nan")}
    if not log.exists():
        return out
    ram, cpu = [], []
    for line in log.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.search(r"RAM (\d+)/(\d+)MB", line)
        if m:
            ram.append(float(m.group(1)))
        c = re.search(r"CPU \[([^\]]+)\]", line)
        if c:
            pcts = [float(p.split("%")[0]) for p in c.group(1).split(",") if "%" in p and p.split("%")[0].strip().isdigit()]
            if pcts:
                cpu.append(statistics.fmean(pcts))
    out["tegra_rows"] = len(ram) or len(cpu)
    if ram:
        out["tegra_ram_used_mib_mean"] = statistics.fmean(ram)
    if cpu:
        out["tegra_cpu_pct_mean"] = statistics.fmean(cpu)
    return out


def infer_order(pair_id: str, meta: dict) -> str:
    if meta.get("ORDER"):
        return meta["ORDER"]
    m = re.search(r"(on-off|off-on)", pair_id, re.IGNORECASE)
    return m.group(1).upper() if m else ""


def tidy(root: Path, source_label: str = "") -> pd.DataFrame:
    rows = []
    for pair_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        for condition in ("on", "off"):
            cdir = pair_dir / condition
            if not cdir.exists():
                continue
            server, client = cdir / "server", cdir / "client"
            if not server.exists() and (cdir / "metadata.txt").exists():   # older layout: files directly in the condition dir
                server = client = cdir
            meta_s, meta_c = read_metadata(server / "metadata.txt"), read_metadata(client / "metadata.txt")
            ok_s, why_s = verify_sha256(server)
            ok_c, why_c = verify_sha256(client)
            row = {
                "source_root": source_label or root.name,
                "pair_id": pair_dir.name,
                "run": meta_s.get("RUN") or meta_c.get("RUN"),
                "attempt": meta_s.get("RUN_ATTEMPT", ""),
                "condition": condition.upper(),
                "order": infer_order(pair_dir.name, meta_s),
                "protocol": meta_s.get("PROTOCOL") or meta_c.get("PROTOCOL", ""),
                "environment": meta_s.get("ENVIRONMENT_NAME", ""),
                "start_epoch_utc": meta_s.get("START_EPOCH_UTC") or meta_c.get("START_EPOCH_UTC"),
                "requests_expected": meta_c.get("HTTP_REQUESTS", meta_s.get("REQUESTS", "")),
                "server_status": meta_s.get("SERVER_STATUS", meta_s.get("STATUS", "")),
                "client_status": meta_s.get("CLIENT_STATUS", ""),
                "ntp_synchronized_client": meta_c.get("NTP_SYNCHRONIZED", ""),
                "utilization_regime": meta_s.get("UTILIZATION_REGIME", ""),
                "sha256_server": why_s,
                "sha256_client": why_c,
            }
            row.update(latency_stats(client / "http.csv"))
            row.update(tegrastats_stats(client / "tegrastats.log"))
            row.update(utilization_stats(server))
            row.update(memory_stats(server))
            row.update(cpu_stats(server))
            gates = []
            if not (ok_s and ok_c):
                gates.append("SHA256")
            try:
                if row["http_rows"] < int(row["requests_expected"] or 0) or row["http_200"] < row["http_rows"]:
                    gates.append("HTTP")
            except ValueError:
                gates.append("META")
            if not row["run"]:
                gates.append("META")
            if row.get("utilization_samples", 0) < 64:
                gates.append("SAMPLES")
            row["gate_status"] = "PASS" if not gates else "HOLD:" + "+".join(gates)
            rows.append(row)
    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, action="append", required=True, help="RunsV3/RunsV4 root; repeat for several roots")
    ap.add_argument("--output", type=Path, default=Path("results_python/telemetry/tidy_conditions.csv"))
    args = ap.parse_args()
    df = pd.concat([tidy(r, r.name) for r in args.root], ignore_index=True) if len(args.root) > 1 else tidy(args.root[0])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.output, index=False)
    digest = hashlib.sha256(args.output.read_bytes()).hexdigest()
    (args.output.with_suffix(".csv.sha256")).write_text(f"{digest}  {args.output.name}\n", encoding="utf-8")
    n_pass = int((df["gate_status"] == "PASS").sum()) if len(df) else 0
    print(f"conditions={len(df)} pass={n_pass} hold={len(df) - n_pass}")
    print(df[["source_root", "pair_id", "run", "condition", "order", "protocol", "lat_p95_ms", "gate_status"]].to_string(index=False) if len(df) else "no conditions found")
    print(f"STATUS={'PASS_TIDY' if len(df) and n_pass == len(df) else 'HOLD_TIDY'}")


if __name__ == "__main__":
    main()

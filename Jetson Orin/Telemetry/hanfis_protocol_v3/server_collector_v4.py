#!/usr/bin/env python3
"""Fail-closed HANFIS collector using the out-of-treatment Prometheus API."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import statistics
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


IDENTITY_LABELS = ("job", "instance", "namespace", "pod", "container", "id", "image", "name")
CPU_METRIC = "container_cpu_usage_seconds_total"
MEM_METRIC = "container_memory_working_set_bytes"
MACHINE_CPU_METRIC = "machine_cpu_cores"
MACHINE_MEMORY_METRIC = "machine_memory_bytes"
P0_MATCHER = 'namespace="hanfis-research",pod=~"p0-baseline-.*",container!="",container!="POD"'
MON_MATCHER = 'namespace="monitoring",pod!="",container!="",container!="POD"'


class GateError(RuntimeError):
    pass


@dataclass(frozen=True)
class Sample:
    labels: Dict[str, str]
    timestamp: float
    value: float

    @property
    def key(self) -> Tuple[str, ...]:
        return tuple(self.labels.get(label, "") for label in IDENTITY_LABELS)


def utc_iso(epoch: float) -> str:
    return datetime.fromtimestamp(epoch, timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def percentile_nearest_rank(values: Sequence[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, math.ceil(fraction * len(ordered)) - 1)
    return ordered[index]


def utilization_regime(percent_values: Sequence[float]) -> str:
    """Pre-registered low-utilization classification using observed samples."""
    if not percent_values:
        raise GateError("No CPU utilization samples available for regime classification")
    p95 = percentile_nearest_rank(percent_values, 0.95)
    maximum = max(percent_values)
    if maximum <= 1.0:
        return "STRICT_LOW_0_TO_1_PERCENT"
    if p95 <= 1.0:
        return "PREDOMINANTLY_LOW_0_TO_1_PERCENT"
    return "ABOVE_LOW_REGIME"


def finite_nonnegative(value: float, description: str) -> None:
    if not math.isfinite(value) or value < 0:
        raise GateError(f"Invalid {description}: {value}")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class Prometheus:
    def __init__(self, base_url: str, timeout: float = 10.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def ready(self) -> None:
        with urllib.request.urlopen(f"{self.base_url}/-/ready", timeout=self.timeout) as response:
            body = response.read().decode("utf-8", "replace")
            if response.status != 200 or "ready" not in body.lower():
                raise GateError(f"Prometheus not ready: HTTP {response.status}: {body[:160]}")

    def query(self, expression: str, query_time: float | None = None) -> List[Sample]:
        params = {"query": expression}
        if query_time is not None:
            params["time"] = f"{query_time:.3f}"
        url = f"{self.base_url}/api/v1/query?{urllib.parse.urlencode(params)}"
        with urllib.request.urlopen(url, timeout=self.timeout) as response:
            payload = json.load(response)
        if payload.get("status") != "success":
            raise GateError(f"Prometheus query failed: {payload}")
        result = payload.get("data", {}).get("result", [])
        samples: List[Sample] = []
        for row in result:
            value = row.get("value")
            if not isinstance(value, list) or len(value) != 2:
                raise GateError(f"Unexpected Prometheus result: {row}")
            samples.append(Sample(dict(row.get("metric", {})), float(value[0]), float(value[1])))
        return samples

    def scalar(self, expression: str, query_time: float | None = None) -> float:
        values = self.query(expression, query_time)
        if len(values) != 1:
            raise GateError(f"Expected one scalar series, got {len(values)} for {expression}")
        return values[0].value


def to_map(samples: Iterable[Sample], description: str) -> Dict[Tuple[str, ...], Sample]:
    mapped: Dict[Tuple[str, ...], Sample] = {}
    for sample in samples:
        if sample.key in mapped:
            raise GateError(f"Duplicate identity in {description}: {sample.key}")
        mapped[sample.key] = sample
    return mapped


def require_same_keys(expected: set, observed: set, description: str) -> None:
    if expected != observed:
        missing = sorted(expected - observed)
        added = sorted(observed - expected)
        raise GateError(f"Series continuity failed for {description}; missing={missing}; added={added}")


def require_close(expected: float, observed: float, abs_tol: float, rel_tol: float, description: str) -> float:
    difference = abs(expected - observed)
    tolerance = max(abs_tol, rel_tol * max(abs(expected), abs(observed)))
    if difference > tolerance:
        raise GateError(
            f"{description} failed; expected={expected:.12g}; observed={observed:.12g}; "
            f"difference={difference:.12g}; tolerance={tolerance:.12g}"
        )
    return difference


def write_series_csv(path: Path, rows: Iterable[Tuple[str, int, float, Sample]]) -> int:
    count = 0
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(("group", "seq", "requested_timestamp_utc", "sample_timestamp_utc", *IDENTITY_LABELS, "value"))
        for group, seq, requested, sample in rows:
            writer.writerow((group, seq, utc_iso(requested), utc_iso(sample.timestamp), *(sample.labels.get(x, "") for x in IDENTITY_LABELS), f"{sample.value:.12f}"))
            count += 1
    return count


def git_value(directory: Path, *args: str, default: str) -> str:
    try:
        return subprocess.check_output(("git", "-C", str(directory), *args), stderr=subprocess.DEVNULL, text=True).strip() or default
    except (OSError, subprocess.CalledProcessError):
        return default


def self_test() -> int:
    assert percentile_nearest_rank([1, 2, 3, 4], 0.95) == 4
    a = Sample({"pod": "p", "container": "c"}, 1.0, 10.0)
    b = Sample({"pod": "p", "container": "c"}, 2.0, 11.0)
    assert a.key == b.key and b.value - a.value == 1.0
    try:
        require_same_keys({a.key}, {("different",)}, "self-test")
    except GateError:
        pass
    else:
        raise AssertionError("continuity gate did not fail")
    assert require_close(1.0, 1.0000001, 1e-6, 1e-6, "close self-test") > 0
    try:
        require_close(1.0, 1.1, 1e-6, 1e-6, "mismatch self-test")
    except GateError:
        pass
    else:
        raise AssertionError("numerical crosscheck did not fail closed")
    print("STATUS=PASS_SERVER_COLLECTOR_V4_SELF_TEST")
    return 0


def main(argv: Sequence[str]) -> int:
    if list(argv) == ["--self-test"]:
        return self_test()
    if len(argv) != 4:
        print("Usage: server_collector_v4.py RUN CONDITION START_EPOCH OUTPUT_DIR", file=sys.stderr)
        return 2

    run_no, condition, start_text, out_text = argv
    condition = condition.lower()
    if not run_no.isdigit() or condition not in {"on", "off"}:
        print("RUN must be numeric and CONDITION must be on or off", file=sys.stderr)
        return 2

    start_epoch = float(start_text)
    out = Path(out_text)
    out.mkdir(parents=True, exist_ok=False) if not out.exists() else None
    errors_path = out / "errors.log"
    errors_path.write_text("", encoding="utf-8")

    prom_url = os.environ.get("PROM_URL", "http://127.0.0.1:29090")
    samples_requested = int(os.environ.get("SAMPLES", "64"))
    interval = float(os.environ.get("INTERVAL_SECONDS", "5"))
    timeout = float(os.environ.get("PROM_TIMEOUT_SECONDS", "10"))
    max_staleness = float(os.environ.get("MAX_SAMPLE_STALENESS_SECONDS", "12"))
    expected_targets = int(os.environ.get("EXPECTED_EXTERNAL_TARGETS", "2"))
    snapshot_abs_tol = float(os.environ.get("SNAPSHOT_ABS_TOL_CPU_SECONDS", "0.000001"))
    snapshot_rel_tol = float(os.environ.get("SNAPSHOT_REL_TOL", "0.000001"))
    rate_abs_tol = float(os.environ.get("RATE_INCREASE_ABS_TOL_CPU_SECONDS", "0.000001"))
    rate_rel_tol = float(os.environ.get("RATE_INCREASE_REL_TOL", "0.000001"))
    query_settle_seconds = float(os.environ.get("PROM_QUERY_SETTLE_SECONDS", "5"))
    server_instance_regex = os.environ.get("SERVER_INSTANCE_REGEX", "desktop-worker.*")
    node_rate_window = int(os.environ.get("NODE_RATE_WINDOW_SECONDS", "30"))
    off_activity_window = int(os.environ.get("OFF_ACTIVITY_WINDOW_SECONDS", "30"))
    off_activity_abs_tol = float(os.environ.get("OFF_ACTIVITY_ABS_TOL_CPU_SECONDS", "0.000001"))
    if samples_requested < 2 or interval <= 0:
        raise GateError("SAMPLES must be >=2 and INTERVAL_SECONDS must be >0")
    if query_settle_seconds < 0:
        raise GateError("PROM_QUERY_SETTLE_SECONDS must be >=0")
    if node_rate_window < max(15, math.ceil(2 * interval)):
        raise GateError("NODE_RATE_WINDOW_SECONDS must cover at least two collection intervals and be >=15s")
    if off_activity_window < max(15, math.ceil(2 * interval)):
        raise GateError("OFF_ACTIVITY_WINDOW_SECONDS must cover at least two collection intervals and be >=15s")
    if off_activity_abs_tol < 0:
        raise GateError("OFF_ACTIVITY_ABS_TOL_CPU_SECONDS must be non-negative")

    prom = Prometheus(prom_url, timeout)
    script_dir = Path(__file__).resolve().parent
    p0_cpu_expr = f"{CPU_METRIC}{{{P0_MATCHER}}}"
    mon_cpu_expr = f"{CPU_METRIC}{{{MON_MATCHER}}}"
    p0_mem_expr = f"{MEM_METRIC}{{{P0_MATCHER}}}"
    mon_mem_expr = f"{MEM_METRIC}{{{MON_MATCHER}}}"
    up_expr = 'count(up{job=~"external-cadvisor-.*"} == 1)'
    root_matcher = f'instance=~"{server_instance_regex}",id="/"'
    root_cpu_expr = f"{CPU_METRIC}{{{root_matcher}}}"
    root_mem_sum_expr = f"sum({MEM_METRIC}{{{root_matcher}}})"
    machine_cpu_expr = f'sum({MACHINE_CPU_METRIC}{{instance=~"{server_instance_regex}"}})'
    machine_mem_expr = f'sum({MACHINE_MEMORY_METRIC}{{instance=~"{server_instance_regex}"}})'
    root_rate_expr = f"sum(rate({CPU_METRIC}{{{root_matcher}}}[{node_rate_window}s]))"
    mon_activity_expr = (
        f"sum(increase({CPU_METRIC}{{{MON_MATCHER}}}[{off_activity_window}s])) "
        "or on() vector(0)"
    )

    try:
        prom.ready()
        delay = max(0.0, start_epoch - time.time())
        if delay:
            time.sleep(delay)

        cpu_start_requested = start_epoch
        initial_p0_cpu_start = to_map(prom.query(p0_cpu_expr, cpu_start_requested), "initial P0 CPU start")
        initial_mon_cpu_observed = to_map(prom.query(mon_cpu_expr, cpu_start_requested), "initial monitoring CPU start")
        initial_root_cpu_start = to_map(prom.query(root_cpu_expr, cpu_start_requested), "initial node root CPU start")
        if not initial_p0_cpu_start:
            raise GateError("No P0 CPU counter series at start")
        if condition == "on" and not initial_mon_cpu_observed:
            raise GateError("No monitoring CPU counter series while condition=ON")
        off_retained_cpu_series_start = len(initial_mon_cpu_observed) if condition == "off" else 0
        off_activity_values: List[float] = []
        if condition == "off":
            initial_off_activity = prom.scalar(mon_activity_expr, cpu_start_requested)
            finite_nonnegative(initial_off_activity, "OFF monitoring CPU increase")
            if initial_off_activity > off_activity_abs_tol:
                raise GateError(
                    f"Monitoring CPU activity present while condition=OFF: "
                    f"increase={initial_off_activity}; tolerance={off_activity_abs_tol}"
                )
            off_activity_values.append(initial_off_activity)
        if not initial_root_cpu_start:
            raise GateError("No node root CPU counter series at start")

        p0_keys = set(initial_p0_cpu_start)
        mon_keys = set(initial_mon_cpu_observed) if condition == "on" else set()
        raw_memory: List[Tuple[str, int, float, Sample]] = []
        aggregate_memory: List[Tuple[int, float, float, float]] = []
        target_rows: List[Tuple[int, float, int]] = []
        utilization_rows: List[Tuple[int, float, float, float, float, float, float, float]] = []
        machine_cpu_cores_reference: float | None = None
        machine_memory_bytes_reference: float | None = None

        for seq in range(1, samples_requested + 1):
            target_time = start_epoch + (seq - 1) * interval
            delay = max(0.0, target_time - time.time())
            if delay:
                time.sleep(delay)
            up = int(prom.scalar(up_expr, target_time))
            target_rows.append((seq, target_time, up))
            if up != expected_targets:
                raise GateError(f"External target continuity failed at seq={seq}: {up}/{expected_targets}")
            if condition == "off":
                off_activity = prom.scalar(mon_activity_expr, target_time)
                finite_nonnegative(off_activity, f"OFF monitoring CPU increase seq={seq}")
                if off_activity > off_activity_abs_tol:
                    raise GateError(
                        f"Monitoring CPU activity present while condition=OFF at seq={seq}: "
                        f"increase={off_activity}; tolerance={off_activity_abs_tol}"
                    )
                off_activity_values.append(off_activity)

            machine_cpu_cores = prom.scalar(machine_cpu_expr, target_time)
            machine_memory_bytes = prom.scalar(machine_mem_expr, target_time)
            root_busy_cores = prom.scalar(root_rate_expr, target_time)
            root_memory_bytes = prom.scalar(root_mem_sum_expr, target_time)
            for value, description in (
                (machine_cpu_cores, "machine CPU capacity"),
                (machine_memory_bytes, "machine memory capacity"),
                (root_busy_cores, "node root busy cores"),
                (root_memory_bytes, "node root memory working set"),
            ):
                finite_nonnegative(value, description)
            if machine_cpu_cores <= 0 or machine_memory_bytes <= 0:
                raise GateError("Machine capacity metrics must be positive")
            if machine_cpu_cores_reference is None:
                machine_cpu_cores_reference = machine_cpu_cores
                machine_memory_bytes_reference = machine_memory_bytes
            require_close(machine_cpu_cores_reference, machine_cpu_cores, 0.0, 0.0, "Machine CPU capacity continuity")
            require_close(machine_memory_bytes_reference, machine_memory_bytes, 0.0, 0.0, "Machine memory capacity continuity")
            cpu_factor = root_busy_cores / machine_cpu_cores
            memory_factor = root_memory_bytes / machine_memory_bytes
            if cpu_factor > 1.05 or memory_factor > 1.0:
                raise GateError(f"Out-of-range utilization factor: cpu={cpu_factor}; memory={memory_factor}")
            utilization_rows.append((
                seq, target_time, machine_cpu_cores, root_busy_cores,
                cpu_factor, cpu_factor * 100.0, memory_factor, memory_factor * 100.0,
            ))

            p0_mem = to_map(prom.query(p0_mem_expr, target_time), f"P0 memory seq={seq}")
            mon_mem_observed = to_map(prom.query(mon_mem_expr, target_time), f"monitoring memory seq={seq}")
            require_same_keys(p0_keys, set(p0_mem), f"P0 memory seq={seq}")
            if condition == "on":
                require_same_keys(mon_keys, set(mon_mem_observed), f"monitoring memory seq={seq}")
                mon_mem = mon_mem_observed
            else:
                # Prometheus/cAdvisor may retain labels and gauges for terminated
                # containers. OFF is defined by the zero-pod Kubernetes gate and
                # zero CPU-counter increase, not by historical label absence.
                mon_mem = {}

            for group, series in (("p0", p0_mem), ("monitoring", mon_mem)):
                for sample in series.values():
                    if target_time - sample.timestamp > max_staleness:
                        raise GateError(f"Stale {group} memory sample at seq={seq}: age={target_time-sample.timestamp:.3f}s")
                    raw_memory.append((group, seq, target_time, sample))
            aggregate_memory.append((seq, target_time, sum(x.value for x in p0_mem.values()), sum(x.value for x in mon_mem.values())))

        end_requested = start_epoch + (samples_requested - 1) * interval

        # Wait beyond the configured scrape timeout before re-querying both
        # historical boundaries. This prevents a scrape completing exactly at
        # START/END from becoming visible only to the later aggregate query.
        settlement_deadline = end_requested + query_settle_seconds
        delay = max(0.0, settlement_deadline - time.time())
        if delay:
            time.sleep(delay)

        p0_cpu_start = to_map(prom.query(p0_cpu_expr, cpu_start_requested), "settled P0 CPU start")
        mon_cpu_start_observed = to_map(prom.query(mon_cpu_expr, cpu_start_requested), "settled monitoring CPU start")
        p0_cpu_end = to_map(prom.query(p0_cpu_expr, end_requested), "P0 CPU end")
        mon_cpu_end_observed = to_map(prom.query(mon_cpu_expr, end_requested), "monitoring CPU end")
        if condition == "on":
            mon_cpu_start = mon_cpu_start_observed
            mon_cpu_end = mon_cpu_end_observed
        else:
            mon_cpu_start = {}
            mon_cpu_end = {}
        off_retained_cpu_series_end = len(mon_cpu_end_observed) if condition == "off" else 0
        root_cpu_start = to_map(prom.query(root_cpu_expr, cpu_start_requested), "settled node root CPU start")
        root_cpu_end = to_map(prom.query(root_cpu_expr, end_requested), "node root CPU end")
        require_same_keys(p0_keys, set(p0_cpu_start), "P0 CPU settled start")
        require_same_keys(mon_keys, set(mon_cpu_start), "monitoring CPU settled start")
        require_same_keys(p0_keys, set(p0_cpu_end), "P0 CPU end")
        require_same_keys(mon_keys, set(mon_cpu_end), "monitoring CPU end")
        require_same_keys(set(initial_root_cpu_start), set(root_cpu_start), "node root CPU settled start")
        require_same_keys(set(initial_root_cpu_start), set(root_cpu_end), "node root CPU end")

        elapsed = max(x.timestamp for x in p0_cpu_end.values()) - min(x.timestamp for x in p0_cpu_start.values())
        if elapsed <= 0:
            raise GateError(f"Non-positive CPU counter elapsed time: {elapsed}")

        cpu_rows = []
        cpu_summary = []
        exact_crosscheck_differences = []
        rate_increase_differences = []
        for group, starts, ends, matcher in (
            ("p0", p0_cpu_start, p0_cpu_end, P0_MATCHER),
            ("monitoring", mon_cpu_start, mon_cpu_end, MON_MATCHER),
        ):
            total_delta = 0.0
            for key in sorted(starts):
                delta = ends[key].value - starts[key].value
                if delta < 0:
                    raise GateError(f"Counter reset detected for {group}: {key}; delta={delta}")
                total_delta += delta
                cpu_rows.append((group, starts[key], ends[key], delta, elapsed, delta / elapsed))
            window = max(15, math.ceil(elapsed))
            if starts:
                snapshot_start = prom.scalar(
                    f"sum({CPU_METRIC}{{{matcher}}} @ {cpu_start_requested:.3f})",
                    end_requested,
                )
                snapshot_end = prom.scalar(
                    f"sum({CPU_METRIC}{{{matcher}}} @ {end_requested:.3f})",
                    end_requested,
                )
                snapshot_delta = snapshot_end - snapshot_start
                if snapshot_delta < 0:
                    raise GateError(f"PromQL exact snapshot counter reset for {group}: delta={snapshot_delta}")
                snapshot_difference = require_close(
                    total_delta,
                    snapshot_delta,
                    snapshot_abs_tol,
                    snapshot_rel_tol,
                    f"Exact snapshot crosscheck for {group}",
                )
                increase = prom.scalar(f"sum(increase({CPU_METRIC}{{{matcher}}}[{window}s]))", end_requested)
                rate = prom.scalar(f"sum(rate({CPU_METRIC}{{{matcher}}}[{window}s]))", end_requested)
                rate_implied_increase = rate * window
                rate_increase_difference = require_close(
                    increase,
                    rate_implied_increase,
                    rate_abs_tol,
                    rate_rel_tol,
                    f"rate/increase coherence for {group}",
                )
                window_relative_difference = abs(total_delta - increase) / max(abs(total_delta), 1e-12)
            else:
                snapshot_start = snapshot_end = snapshot_delta = snapshot_difference = 0.0
                increase = rate = rate_implied_increase = rate_increase_difference = window_relative_difference = 0.0
            exact_crosscheck_differences.append(snapshot_difference)
            rate_increase_differences.append(rate_increase_difference)
            cpu_summary.append((
                group, len(starts), total_delta, elapsed,
                total_delta / elapsed if starts else 0.0,
                snapshot_start, snapshot_end, snapshot_delta, snapshot_difference,
                increase, rate, rate_implied_increase, rate_increase_difference,
                window_relative_difference,
            ))

        root_elapsed = max(x.timestamp for x in root_cpu_end.values()) - min(x.timestamp for x in root_cpu_start.values())
        if root_elapsed <= 0:
            raise GateError(f"Non-positive node root CPU elapsed time: {root_elapsed}")
        root_delta = 0.0
        node_counter_rows = []
        for key in sorted(root_cpu_start):
            delta = root_cpu_end[key].value - root_cpu_start[key].value
            if delta < 0:
                raise GateError(f"Node root CPU counter reset detected: {key}; delta={delta}")
            root_delta += delta
            node_counter_rows.append((root_cpu_start[key], root_cpu_end[key], delta))
        assert machine_cpu_cores_reference is not None
        assert machine_memory_bytes_reference is not None
        explicit_node_cpu_factor = root_delta / (root_elapsed * machine_cpu_cores_reference)
        finite_nonnegative(explicit_node_cpu_factor, "explicit node CPU utilization factor")

        with (out / "cpu_counter_delta.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(("group", *IDENTITY_LABELS, "start_timestamp_utc", "end_timestamp_utc", "start_cpu_seconds", "end_cpu_seconds", "delta_cpu_seconds", "elapsed_seconds", "mean_cores"))
            for group, start, end, delta, duration, mean_cores in cpu_rows:
                writer.writerow((group, *(start.labels.get(x, "") for x in IDENTITY_LABELS), utc_iso(start.timestamp), utc_iso(end.timestamp), f"{start.value:.12f}", f"{end.value:.12f}", f"{delta:.12f}", f"{duration:.6f}", f"{mean_cores:.12f}"))

        with (out / "cpu_summary.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow((
                "group", "series", "explicit_delta_cpu_seconds", "elapsed_seconds", "explicit_mean_cores",
                "promql_snapshot_start_cpu_seconds", "promql_snapshot_end_cpu_seconds",
                "promql_snapshot_delta_cpu_seconds", "snapshot_absolute_difference_cpu_seconds",
                "promql_increase_cpu_seconds", "promql_rate_cores", "rate_implied_increase_cpu_seconds",
                "rate_increase_absolute_difference_cpu_seconds", "window_estimator_relative_difference",
            ))
            writer.writerows(cpu_summary)

        with (out / "node_cpu_counter_delta.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow((*IDENTITY_LABELS, "start_timestamp_utc", "end_timestamp_utc", "start_cpu_seconds", "end_cpu_seconds", "delta_cpu_seconds", "elapsed_seconds"))
            for start, end, delta in node_counter_rows:
                writer.writerow((*(start.labels.get(x, "") for x in IDENTITY_LABELS), utc_iso(start.timestamp), utc_iso(end.timestamp), f"{start.value:.12f}", f"{end.value:.12f}", f"{delta:.12f}", f"{root_elapsed:.6f}"))

        cpu_percent_values = [row[5] for row in utilization_rows]
        memory_percent_values = [row[7] for row in utilization_rows]
        regime = utilization_regime(cpu_percent_values)
        with (out / "utilization_samples.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(("seq", "requested_timestamp_utc", "machine_cpu_cores", "root_cpu_busy_cores", "cpu_utilization_factor", "cpu_utilization_percent", "memory_utilization_factor", "memory_utilization_percent"))
            for seq, requested, cores, busy, cpu_factor, cpu_percent, mem_factor, mem_percent in utilization_rows:
                writer.writerow((seq, utc_iso(requested), f"{cores:.6f}", f"{busy:.12f}", f"{cpu_factor:.12f}", f"{cpu_percent:.9f}", f"{mem_factor:.12f}", f"{mem_percent:.9f}"))

        with (out / "utilization_summary.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(("metric", "mean", "median", "p95_nearest_rank", "max"))
            for name, values in (
                ("cpu_utilization_percent", cpu_percent_values),
                ("memory_utilization_percent", memory_percent_values),
            ):
                writer.writerow((name, f"{statistics.fmean(values):.12f}", f"{statistics.median(values):.12f}", f"{percentile_nearest_rank(values, 0.95):.12f}", f"{max(values):.12f}"))
            writer.writerow(("explicit_window_cpu_utilization_factor", f"{explicit_node_cpu_factor:.12f}", "", "", ""))

        memory_rows = write_series_csv(out / "memory_samples.csv", raw_memory)
        with (out / "memory_aggregate_samples.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(("seq", "requested_timestamp_utc", "p0_total_bytes", "monitoring_total_bytes"))
            for seq, requested, p0_total, mon_total in aggregate_memory:
                writer.writerow((seq, utc_iso(requested), f"{p0_total:.3f}", f"{mon_total:.3f}"))

        with (out / "memory_summary.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(("group", "samples", "mean_bytes", "median_bytes", "p95_bytes", "max_bytes"))
            for group, index in (("p0", 2), ("monitoring", 3)):
                values = [row[index] for row in aggregate_memory]
                writer.writerow((group, len(values), f"{statistics.fmean(values):.3f}", f"{statistics.median(values):.3f}", f"{percentile_nearest_rank(values, 0.95):.3f}", f"{max(values):.3f}"))

        with (out / "target_samples.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(("seq", "requested_timestamp_utc", "external_targets_up"))
            for seq, requested, up in target_rows:
                writer.writerow((seq, utc_iso(requested), up))

        monitoring_rows = sum(1 for group, *_ in raw_memory if group == "monitoring")
        p0_rows = sum(1 for group, *_ in raw_memory if group == "p0")
        metadata = {
            "RUN": run_no,
            "CONDITION": condition.upper(),
            "PROTOCOL": "external-prometheus-v4.2.2-retained-series-aware",
            "COLLECTOR": "server_collector_v4.2.2",
            "PROMETHEUS_URL": prom_url,
            "SCRAPE_INTERVAL_SECONDS": interval,
            "REQUESTED_SAMPLES": samples_requested,
            "START_EPOCH_UTC": start_text,
            "END_EPOCH_UTC": f"{end_requested:.3f}",
            "CPU_COUNTER": CPU_METRIC,
            "MEMORY_GAUGE": MEM_METRIC,
            "SERVER_INSTANCE_REGEX": server_instance_regex,
            "NODE_RATE_WINDOW_SECONDS": node_rate_window,
            "OFF_ACTIVITY_WINDOW_SECONDS": off_activity_window,
            "OFF_ACTIVITY_ABS_TOL_CPU_SECONDS": off_activity_abs_tol,
            "OFF_RETAINED_MONITORING_CPU_SERIES_START": off_retained_cpu_series_start,
            "OFF_RETAINED_MONITORING_CPU_SERIES_END": off_retained_cpu_series_end,
            "OFF_MONITORING_MAX_CPU_INCREASE_WINDOW_SECONDS": max(off_activity_values, default=0.0),
            "OFF_RETAINED_SERIES_POLICY": "ZERO_ACTIVITY_ACCEPTED_AFTER_KUBERNETES_ZERO_POD_GATE",
            "OFF_MONITORING_ACTIVITY_GATE": "PASS" if condition == "off" else "NOT_APPLICABLE",
            "MACHINE_CPU_CORES": machine_cpu_cores_reference,
            "MACHINE_MEMORY_BYTES": machine_memory_bytes_reference,
            "NODE_CPU_EXPLICIT_DELTA_SECONDS": root_delta,
            "NODE_CPU_EXPLICIT_ELAPSED_SECONDS": root_elapsed,
            "NODE_CPU_EXPLICIT_UTILIZATION_FACTOR": explicit_node_cpu_factor,
            "CPU_UTILIZATION_PERCENT_MEAN": statistics.fmean(cpu_percent_values),
            "CPU_UTILIZATION_PERCENT_P95": percentile_nearest_rank(cpu_percent_values, 0.95),
            "CPU_UTILIZATION_PERCENT_MAX": max(cpu_percent_values),
            "MEMORY_UTILIZATION_PERCENT_MEAN": statistics.fmean(memory_percent_values),
            "UTILIZATION_REGIME": regime,
            "NODE_UTILIZATION_STATUS": "PASS",
            "VIRTUAL_ENV_PATH": os.environ.get("VIRTUAL_ENV", "unknown"),
            "ENVIRONMENT_NAME": Path(os.environ["VIRTUAL_ENV"]).name if os.environ.get("VIRTUAL_ENV") else "unknown",
            "EXPECTED_EXTERNAL_TARGETS": expected_targets,
            "P0_SERIES": len(p0_keys),
            "MONITORING_SERIES": len(mon_keys),
            "P0_MEMORY_ROWS": p0_rows,
            "MONITORING_MEMORY_ROWS": monitoring_rows,
            "TARGET_CONTINUITY": "PASS",
            "SERIES_CONTINUITY": "PASS",
            "COUNTER_RESET_CHECK": "PASS",
            "BOUNDARY_SETTLEMENT": "PASS",
            "PROM_QUERY_SETTLE_SECONDS": query_settle_seconds,
            "SNAPSHOT_EXACT_CROSSCHECK": "PASS",
            "SNAPSHOT_ABS_TOL_CPU_SECONDS": snapshot_abs_tol,
            "SNAPSHOT_REL_TOL": snapshot_rel_tol,
            "SNAPSHOT_MAX_ABS_DIFFERENCE_CPU_SECONDS": max(exact_crosscheck_differences, default=0.0),
            "RATE_INCREASE_COHERENCE": "PASS",
            "RATE_INCREASE_ABS_TOL_CPU_SECONDS": rate_abs_tol,
            "RATE_INCREASE_REL_TOL": rate_rel_tol,
            "RATE_INCREASE_MAX_ABS_DIFFERENCE_CPU_SECONDS": max(rate_increase_differences, default=0.0),
            "WINDOW_ESTIMATOR_DIFFERENCE": "RECORDED_NOT_GATED",
            "PROMQL_CROSSCHECK": "PASS_STRICT",
            "RUN17_EXECUTED": "NO",
            "COLLECTOR_SHA256": sha256(Path(__file__)),
            "WRAPPER_SHA256": sha256(script_dir / "server_collector_v4.sh"),
            "GIT_COMMIT": git_value(script_dir, "rev-parse", "HEAD", default="NOT_A_GIT_CHECKOUT"),
            "GIT_DIRTY_FILES": git_value(script_dir, "status", "--porcelain", default="").count("\n") + (1 if git_value(script_dir, "status", "--porcelain", default="") else 0),
            "STATUS": "PASS",
        }
        (out / "metadata.txt").write_text("".join(f"{key}={value}\n" for key, value in metadata.items()), encoding="utf-8")

        artifacts = ["metadata.txt", "errors.log", "cpu_counter_delta.csv", "cpu_summary.csv", "node_cpu_counter_delta.csv", "utilization_samples.csv", "utilization_summary.csv", "memory_samples.csv", "memory_aggregate_samples.csv", "memory_summary.csv", "target_samples.csv"]
        with (out / "sha256.txt").open("w", encoding="utf-8") as handle:
            for name in artifacts:
                handle.write(f"{sha256(out / name)}  {name}\n")

        print(f"SERVER_NODE_ROWS={len(target_rows)}")
        print(f"SERVER_P0_ROWS={p0_rows}")
        print(f"SERVER_MONITORING_ROWS={monitoring_rows}")
        print(f"SERVER_CPU_DELTA_ROWS={len(cpu_rows)}")
        print("SERVER_TARGET_CONTINUITY=PASS")
        print("SERVER_SERIES_CONTINUITY=PASS")
        print("SERVER_COUNTER_RESET_CHECK=PASS")
        print("SERVER_BOUNDARY_SETTLEMENT=PASS")
        print("SERVER_SNAPSHOT_EXACT_CROSSCHECK=PASS")
        print("SERVER_RATE_INCREASE_COHERENCE=PASS")
        print("SERVER_WINDOW_ESTIMATOR_DIFFERENCE=RECORDED_NOT_GATED")
        print("SERVER_PROMQL_CROSSCHECK=PASS_STRICT")
        print("SERVER_NODE_UTILIZATION_STATUS=PASS")
        print(f"SERVER_OFF_RETAINED_MONITORING_CPU_SERIES_START={off_retained_cpu_series_start}")
        print(f"SERVER_OFF_RETAINED_MONITORING_CPU_SERIES_END={off_retained_cpu_series_end}")
        print(f"SERVER_OFF_MONITORING_MAX_CPU_INCREASE_WINDOW_SECONDS={max(off_activity_values, default=0.0):.12f}")
        print(f"SERVER_OFF_MONITORING_ACTIVITY_GATE={'PASS' if condition == 'off' else 'NOT_APPLICABLE'}")
        print(f"SERVER_UTILIZATION_REGIME={regime}")
        print(f"SERVER_CPU_UTILIZATION_PERCENT_MEAN={statistics.fmean(cpu_percent_values):.9f}")
        print(f"SERVER_CPU_UTILIZATION_PERCENT_P95={percentile_nearest_rank(cpu_percent_values, 0.95):.9f}")
        print(f"SERVER_CPU_UTILIZATION_PERCENT_MAX={max(cpu_percent_values):.9f}")
        print(f"SERVER_UTILIZATION_SAMPLES={len(utilization_rows)}")
        print(f"SERVER_OUTPUT={out}")
        print("SERVER_STATUS=PASS")
        return 0
    except Exception as exc:
        with errors_path.open("a", encoding="utf-8") as handle:
            handle.write(f"{type(exc).__name__}: {exc}\n")
        print(f"GATE_FAIL={type(exc).__name__}:{exc}")
        print(f"SERVER_OUTPUT={out}")
        print("SERVER_STATUS=HOLD")
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

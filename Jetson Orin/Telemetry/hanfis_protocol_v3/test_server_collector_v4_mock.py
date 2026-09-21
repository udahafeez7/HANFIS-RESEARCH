#!/usr/bin/env python3
"""Fast end-to-end mock test for server_collector_v4.py."""

import json
import os
import re
import subprocess
import tempfile
import threading
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


def vector(metric, timestamp, value):
    return {"metric": metric, "value": [timestamp, str(value)]}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_args):
        return

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/-/ready":
            body = b"Prometheus Server is Ready."
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if parsed.path != "/api/v1/query":
            self.send_error(404)
            return

        params = urllib.parse.parse_qs(parsed.query)
        query = params.get("query", [""])[0]
        timestamp = float(params.get("time", [str(time.time())])[0])
        at_match = re.search(r"@\s*([0-9]+(?:\.[0-9]+)?)", query)
        evaluation_timestamp = float(at_match.group(1)) if at_match else timestamp
        result = []
        if query.startswith("count(up"):
            result = [vector({}, timestamp, 2)]
        elif query.startswith("sum(machine_cpu_cores"):
            result = [vector({}, timestamp, 16)]
        elif query.startswith("sum(machine_memory_bytes"):
            result = [vector({}, timestamp, 16_000_000_000)]
        elif query.startswith("sum(increase"):
            if 'namespace="monitoring"' in query and getattr(self.server, "off_mode", False):
                result = [vector({}, timestamp, getattr(self.server, "off_monitoring_increase", 0.0))]
            else:
                result = [vector({}, timestamp, 0.6)]
        elif query.startswith("sum(rate"):
            if 'id="/"' in query:
                result = [vector({}, timestamp, 0.112)]
            else:
                result = [vector({}, timestamp, 0.05 if getattr(self.server, "rate_mismatch", False) else 0.04)]
        elif query.startswith("sum(container_memory_working_set_bytes") and 'id="/"' in query:
            result = [vector({}, timestamp, 750_000_000)]
        elif query.startswith("sum(container_cpu_usage_seconds_total"):
            slope = 0.03 if getattr(self.server, "snapshot_mismatch", False) else 0.02
            result = [vector({}, timestamp, 201 + evaluation_timestamp * slope * 2)]
        else:
            if 'id="/"' in query:
                self.server.root_cpu_queries += 1
                labels = {
                    "__name__": "container_cpu_usage_seconds_total",
                    "job": "external-cadvisor-worker",
                    "instance": "desktop-worker:10250",
                    "namespace": "",
                    "pod": "",
                    "container": "",
                    "id": "/",
                    "image": "",
                    "name": "",
                }
                value = 1.0 if getattr(self.server, "root_reset", False) and self.server.root_cpu_queries >= 3 else 50 + timestamp * 0.112
                result = [vector(labels, timestamp, value)]
                body = json.dumps({"status": "success", "data": {"resultType": "vector", "result": result}}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            group = "monitoring" if 'namespace="monitoring"' in query else "p0"
            metric_name = "container_memory_working_set_bytes" if "memory_working_set" in query else "container_cpu_usage_seconds_total"
            cpu_slope = 0.02
            if metric_name == "container_cpu_usage_seconds_total":
                self.server.raw_cpu_queries += 1
                if getattr(self.server, "boundary_race", False) and self.server.raw_cpu_queries <= 2:
                    cpu_slope = 0.019
            pods = ("prometheus-0", "operator-0") if group == "monitoring" else ("p0-baseline-a", "p0-baseline-b")
            for index, pod in enumerate(pods):
                labels = {
                    "__name__": metric_name,
                    "job": "external-cadvisor-worker",
                    "instance": "desktop-worker:10250",
                    "namespace": "monitoring" if group == "monitoring" else "hanfis-research",
                    "pod": pod,
                    "container": "app",
                    "id": f"/kubepods/{pod}",
                    "image": "mock:v1",
                    "name": pod,
                }
                value = (100_000_000 + index * 1_000_000 + timestamp * 100) if metric_name.startswith("container_memory") else (100 + index + timestamp * cpu_slope)
                result.append(vector(labels, timestamp, value))

        body = json.dumps({"status": "success", "data": {"resultType": "vector", "result": result}}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.snapshot_mismatch = False
    server.rate_mismatch = False
    server.boundary_race = True
    server.raw_cpu_queries = 0
    server.root_cpu_queries = 0
    server.root_reset = False
    server.off_mode = False
    server.off_monitoring_increase = 0.0
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with tempfile.TemporaryDirectory(prefix="hanfis-collector-v4-test-") as temp:
            output = Path(temp) / "result"
            script = Path(__file__).with_name("server_collector_v4.py")
            env = os.environ.copy()
            env.update({
                "PROM_URL": f"http://127.0.0.1:{server.server_port}",
                "SAMPLES": "3",
                "INTERVAL_SECONDS": "0.05",
                "MAX_SAMPLE_STALENESS_SECONDS": "1",
                "PROM_QUERY_SETTLE_SECONDS": "0",
                "SERVER_INSTANCE_REGEX": "desktop-worker.*",
                "NODE_RATE_WINDOW_SECONDS": "30",
                "VIRTUAL_ENV": "/home/hafiz/.venvs/anfis",
            })
            start = time.time() + 0.1
            completed = subprocess.run(
                ["python3", str(script), "99", "on", f"{start:.3f}", str(output)],
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=15,
                check=False,
            )
            print(completed.stdout, end="")
            assert completed.returncode == 0
            assert "SERVER_STATUS=PASS" in completed.stdout
            assert "SERVER_SNAPSHOT_EXACT_CROSSCHECK=PASS" in completed.stdout
            assert "SERVER_RATE_INCREASE_COHERENCE=PASS" in completed.stdout
            assert "SERVER_BOUNDARY_SETTLEMENT=PASS" in completed.stdout
            assert "SERVER_NODE_UTILIZATION_STATUS=PASS" in completed.stdout
            assert "SERVER_UTILIZATION_REGIME=STRICT_LOW_0_TO_1_PERCENT" in completed.stdout
            assert "TARGET_CONTINUITY=PASS" in (output / "metadata.txt").read_text()
            assert "COUNTER_RESET_CHECK=PASS" in (output / "metadata.txt").read_text()
            assert "SNAPSHOT_EXACT_CROSSCHECK=PASS" in (output / "metadata.txt").read_text()
            assert "RATE_INCREASE_COHERENCE=PASS" in (output / "metadata.txt").read_text()
            required = {
                "cpu_counter_delta.csv", "cpu_summary.csv", "memory_samples.csv",
                "memory_aggregate_samples.csv", "memory_summary.csv",
                "target_samples.csv", "node_cpu_counter_delta.csv",
                "utilization_samples.csv", "utilization_summary.csv",
                "metadata.txt", "sha256.txt", "errors.log",
            }
            assert required.issubset({path.name for path in output.iterdir()})
            subprocess.run(["sha256sum", "-c", "sha256.txt"], cwd=output, check=True, stdout=subprocess.DEVNULL)

            # OFF must accept retained monitoring labels when their CPU counter
            # does not increase. This reproduces the Run 17 attempt-1 failure.
            server.boundary_race = False
            server.raw_cpu_queries = 0
            server.off_mode = True
            server.off_monitoring_increase = 0.0
            off_output = Path(temp) / "off-retained-zero-activity"
            off_start = time.time() + 0.1
            off_completed = subprocess.run(
                ["python3", str(script), "99", "off", f"{off_start:.3f}", str(off_output)],
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=15,
                check=False,
            )
            print(off_completed.stdout, end="")
            assert off_completed.returncode == 0
            assert "SERVER_OFF_RETAINED_MONITORING_CPU_SERIES_START=2" in off_completed.stdout
            assert "SERVER_OFF_MONITORING_ACTIVITY_GATE=PASS" in off_completed.stdout
            assert "MONITORING_SERIES=0" in (off_output / "metadata.txt").read_text()
            assert "MONITORING_MEMORY_ROWS=0" in (off_output / "metadata.txt").read_text()
            subprocess.run(["sha256sum", "-c", "sha256.txt"], cwd=off_output, check=True, stdout=subprocess.DEVNULL)

            # OFF must still fail closed when retained labels show CPU activity.
            server.off_monitoring_increase = 0.01
            active_output = Path(temp) / "off-active-monitoring"
            active_start = time.time() + 0.1
            active_held = subprocess.run(
                ["python3", str(script), "99", "off", f"{active_start:.3f}", str(active_output)],
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=15,
                check=False,
            )
            print(active_held.stdout, end="")
            assert active_held.returncode != 0
            assert "Monitoring CPU activity present while condition=OFF" in active_held.stdout
            assert "SERVER_STATUS=HOLD" in active_held.stdout
            server.off_mode = False
            server.off_monitoring_increase = 0.0

            server.boundary_race = False
            server.raw_cpu_queries = 0
            server.snapshot_mismatch = True
            hold_output = Path(temp) / "mismatch"
            hold_start = time.time() + 0.1
            held = subprocess.run(
                ["python3", str(script), "99", "on", f"{hold_start:.3f}", str(hold_output)],
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=15,
                check=False,
            )
            print(held.stdout, end="")
            assert held.returncode != 0
            assert "Exact snapshot crosscheck" in held.stdout
            assert "SERVER_STATUS=HOLD" in held.stdout

            server.snapshot_mismatch = False
            server.rate_mismatch = True
            rate_hold_output = Path(temp) / "rate-mismatch"
            rate_hold_start = time.time() + 0.1
            rate_held = subprocess.run(
                ["python3", str(script), "99", "on", f"{rate_hold_start:.3f}", str(rate_hold_output)],
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=15,
                check=False,
            )
            print(rate_held.stdout, end="")
            assert rate_held.returncode != 0
            assert "rate/increase coherence" in rate_held.stdout
            assert "SERVER_STATUS=HOLD" in rate_held.stdout

            server.rate_mismatch = False
            server.root_reset = True
            server.root_cpu_queries = 0
            reset_output = Path(temp) / "root-reset"
            reset_start = time.time() + 0.1
            reset_held = subprocess.run(
                ["python3", str(script), "99", "on", f"{reset_start:.3f}", str(reset_output)],
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=15,
                check=False,
            )
            print(reset_held.stdout, end="")
            assert reset_held.returncode != 0
            assert "Node root CPU counter reset detected" in reset_held.stdout
            assert "SERVER_STATUS=HOLD" in reset_held.stdout
    finally:
        server.shutdown()
        server.server_close()
    print("STATUS=PASS_SERVER_COLLECTOR_V4_MOCK_TEST")


if __name__ == "__main__":
    main()

import hashlib
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "telemetry"))

import analyze_pairs  # noqa: E402
import tidy_pairs  # noqa: E402


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _manifest(directory: Path, names: list[str]) -> None:
    lines = [f"{hashlib.sha256((directory / n).read_bytes()).hexdigest()}  {n}" for n in names]
    (directory / "sha256.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def make_condition(cdir: Path, run: int, condition: str, latency_ms: float, requests: int = 20, samples: int = 64, corrupt: bool = False) -> None:
    server, client = cdir / "server", cdir / "client"
    rng = np.random.default_rng(run * 10 + (1 if condition == "on" else 0))
    _write(server / "metadata.txt", f"RUN={run}\nRUN_ATTEMPT=1\nCONDITION={condition.upper()}\nORDER=ON-OFF\nPROTOCOL=external-prometheus-v4.2\nENVIRONMENT_NAME=test\nSTART_EPOCH_UTC=1700000000\nREQUESTS={requests}\nUTILIZATION_REGIME=STRICT_LOW_0_TO_1_PERCENT\nSERVER_STATUS=PASS\n")
    util = pd.DataFrame({"seq": range(samples), "requested_timestamp_utc": ["t"] * samples, "machine_cpu_cores": 8.0,
                         "root_cpu_busy_cores": rng.uniform(0.02, 0.06, samples), "cpu_utilization_factor": 0.005,
                         "cpu_utilization_percent": rng.uniform(0.3, 0.8, samples), "memory_utilization_factor": 0.2, "memory_utilization_percent": 20.0})
    util.to_csv(server / "utilization_samples.csv", index=False)
    pd.DataFrame({"metric": ["cpu_utilization_percent", "memory_utilization_percent"], "mean": [0.55, 20.0], "median": [0.5, 20.0],
                  "p95_nearest_rank": [0.75, 20.5], "max": [0.8, 21.0]}).to_csv(server / "utilization_summary.csv", index=False)
    pd.DataFrame({"group": ["p0", "monitoring"], "samples": [samples, samples], "mean_bytes": [200 * 2**20, 220 * 2**20],
                  "median_bytes": [200 * 2**20, 220 * 2**20], "p95_bytes": [205 * 2**20, 230 * 2**20], "max_bytes": [210 * 2**20, 240 * 2**20]}).to_csv(server / "memory_summary.csv", index=False)
    pd.DataFrame({"pod": ["node"], "start_timestamp_utc": ["a"], "end_timestamp_utc": ["b"], "start_cpu_seconds": [100.0],
                  "end_cpu_seconds": [112.0], "delta_cpu_seconds": [12.0], "elapsed_seconds": [300.0]}).to_csv(server / "node_cpu_counter_delta.csv", index=False)
    _manifest(server, ["metadata.txt", "utilization_samples.csv", "utilization_summary.csv", "memory_summary.csv", "node_cpu_counter_delta.csv"])
    _write(client / "metadata.txt", f"RUN={run}\nCONDITION={condition.upper()}\nPROTOCOL=external-v4-nodeport\nHTTP_REQUESTS={requests}\nNTP_SYNCHRONIZED=yes\n")
    lat = rng.normal(latency_ms, 0.2, requests) / 1000.0
    http = pd.DataFrame({"seq": range(1, requests + 1), "timestamp_utc": ["t"] * requests, "http_code": 200, "time_namelookup": 0.0,
                         "time_connect": 0.0005, "time_starttransfer": lat * 0.9, "time_total": lat, "size_bytes": 615})
    http.to_csv(client / "http.csv", index=False)
    _write(client / "tegrastats.log", "\n".join("RAM 1500/7620MB (lfb 10x4MB) CPU [12%@1510,8%@1510,10%@1510,9%@1510,off,off]" for _ in range(5)) + "\n")
    _manifest(client, ["metadata.txt", "http.csv", "tegrastats.log"])
    if corrupt:
        (client / "http.csv").write_text("seq,timestamp_utc,http_code\n1,t,500\n", encoding="utf-8")


class TestTelemetryPipeline(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmp = Path(tempfile.mkdtemp())
        for run in range(7, 13):
            pair = self.tmp / f"run{run}"
            make_condition(pair / "on", run, "on", latency_ms=2.4 + 0.1 * (run % 3))
            make_condition(pair / "off", run, "off", latency_ms=2.0)
        make_condition(self.tmp / "run13" / "on", 13, "on", 2.5, corrupt=True)
        make_condition(self.tmp / "run13" / "off", 13, "off", 2.0)

    def test_tidy_marks_corrupt_condition_hold_and_others_pass(self):
        df = tidy_pairs.tidy(self.tmp)
        self.assertEqual(len(df), 14)
        held = df[df["pair_id"] == "run13"]
        self.assertTrue(held[held["condition"] == "ON"]["gate_status"].str.startswith("HOLD").all())
        self.assertEqual(int((df["gate_status"] == "PASS").sum()), 13)
        self.assertTrue((df.loc[df["gate_status"] == "PASS", "http_200"] == 20).all())

    def test_paired_analysis_excludes_hold_and_detects_effect(self):
        df = tidy_pairs.tidy(self.tmp)
        pairs = analyze_pairs.pair_table(df)
        self.assertEqual(len(pairs), 6)  # run13 excluded (ON side HOLD)
        eff = pd.DataFrame(analyze_pairs.effects(pairs, "test"))
        row = eff[eff["metric"] == "lat_mean_ms"].iloc[0]
        self.assertGreater(row["diff_mean"], 0.3)
        self.assertAlmostEqual(row["p_floor"], 2 / 64)
        self.assertLessEqual(row["sign_flip_p"], 0.05)

    def test_v3_protocol_not_gated_on_utilization_samples(self):
        pair = self.tmp / "v3pair"
        make_condition(pair / "on", 30, "on", 2.3, samples=0)
        make_condition(pair / "off", 30, "off", 2.0, samples=0)
        for c in ("on", "off"):
            meta = pair / c / "server" / "metadata.txt"
            meta.write_text(meta.read_text().replace("PROTOCOL=external-prometheus-v4.2", "PROTOCOL=external-v3.0"), encoding="utf-8")
            _manifest(pair / c / "server", ["metadata.txt", "utilization_samples.csv", "utilization_summary.csv", "memory_summary.csv", "node_cpu_counter_delta.csv"])
        df = tidy_pairs.tidy(self.tmp)
        v3 = df[df["pair_id"] == "v3pair"]
        self.assertTrue((v3["gate_status"] == "PASS").all())

    def test_v3_collector_csv_parsing(self):
        import tempfile
        d = Path(tempfile.mkdtemp())
        pd.DataFrame({"seq": [1, 1, 2, 2], "timestamp_utc": ["t"] * 4, "node": ["a", "b", "a", "b"],
                      "cpu_cores": ["40m", "60m", "44m", "56m"], "cpu_pct": ["1%", "2%", "1%", "2%"],
                      "memory_bytes": ["1Gi", "1Gi", "1Gi", "1Gi"], "memory_pct": ["10%"] * 4}).to_csv(d / "nodes.csv", index=False)
        pd.DataFrame({"seq": [1, 1, 2, 2], "timestamp_utc": ["t"] * 4, "pod": ["p1", "p2", "p1", "p2"],
                      "container": ["c"] * 4, "cpu": ["1m", "2m", "1m", "1m"],
                      "memory": ["15Mi", "15Mi", "14Mi", "16Mi"]}).to_csv(d / "p0_containers.csv", index=False)
        pd.DataFrame(columns=["seq", "timestamp_utc", "pod", "container", "cpu", "memory"]).to_csv(d / "monitoring_containers.csv", index=False)
        out = tidy_pairs.v3_resource_stats(d)
        self.assertAlmostEqual(out["node_cpu_mcores_mean"], 100.0)   # per-sample sum over nodes, then mean
        self.assertAlmostEqual(out["mem_p0_mean_mib"], 30.0)
        self.assertAlmostEqual(out["cpu_monitoring_mcores_mean"], 0.0)
        self.assertAlmostEqual(tidy_pairs._cpu_to_mcores("250000n"), 0.25)
        self.assertAlmostEqual(tidy_pairs._memory_to_mib("512Ki"), 0.5)

    def test_sign_flip_floor_small_n(self):
        d = np.array([0.3, 0.4, 0.2, 0.5])
        self.assertAlmostEqual(analyze_pairs.exact_sign_flip_p(d), 2 / 16)


if __name__ == "__main__":
    unittest.main()

# HANFIS Stage 3C — External Prometheus Collector v4.1.1

This package integrates the independently validated external Prometheus at
`http://127.0.0.1:29090` into the NodePort pair runner. It does **not** execute
Run 17.

## Measurement design

- CPU is read from `container_cpu_usage_seconds_total` as synchronized start
  and end snapshots. Per-series deltas are divided by observed elapsed time.
- Memory is read from `container_memory_working_set_bytes` every five seconds
  and summarized as mean, median, P95, and maximum.
- An exact PromQL snapshot delta (`sum(counter @ end) - sum(counter @ start)`)
  is compared numerically with the Python per-series explicit delta. Any
  mismatch outside the configured absolute/relative tolerance fails closed.
- Both explicit per-series boundaries are re-queried after a default five-second
  settlement window. This avoids scrape-ingestion races where a boundary sample
  becomes visible only to the later aggregate query. The tolerance remains
  strict; this revision does not hide mismatches by relaxing it.
- PromQL `increase()` and `rate()` remain window estimators. Their mathematical
  coherence (`rate * window == increase`) is gated separately.
- The difference between explicit snapshots and `increase()` is retained as
  `WINDOW_ESTIMATOR_DIFFERENCE=RECORDED_NOT_GATED`, because range-vector
  boundary extrapolation can legitimately differ from exact snapshots.
- Collection fails closed on target loss, series addition/removal, stale
  samples, missing P0/monitoring evidence, or negative CPU delta (counter reset).
- All raw data, summaries, metadata, and hashes are retained per condition.

## Install and validate — WSL in VS Code

Extract the ZIP into:

`/mnt/c/Research/ANFIS/Jetson Orin/Telemetry/hanfis_protocol_v3`

Then run:

```bash
cd "/mnt/c/Research/ANFIS/Jetson Orin/Telemetry/hanfis_protocol_v3"
source /home/hafiz/.venvs/anfis/bin/activate
chmod +x run_pair_v4.sh jetson_capture_v4.sh server_collector_v4.sh server_collector_v4.py test_server_collector_v4_mock.py test_run_pair_v4_static.sh
sha256sum -c SHA256SUMS_STAGE3C_COLLECTOR_V4_1_1.txt
./test_run_pair_v4_static.sh
```

Expected final line:

`STATUS=PASS_STAGE3C_COLLECTOR_V4_1_1_STATIC_TESTS`

The mock suite contains both a positive path and an injected snapshot mismatch.
The injected mismatch must return `SERVER_STATUS=HOLD`; otherwise validation
fails.

## Required health gate before any experimental run

- NodePort local and Jetson HTTP status: 200.
- Internal Prometheus restored and Running.
- External Prometheus API Ready at port 29090.
- `EXTERNAL_ACTIVE_TARGETS=2`.

Keep `CONFIRM_RUN17=NO`. After installation, run a non-Run-17 315-second dry
validation with 1,500 requests. Do not start the official paired experiment.

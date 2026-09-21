# HANFIS Stage 3C v4.2 — Utilization-Gated Collector

## Purpose

This revision integrates node-level utilization measurement into every synchronized condition window while retaining the existing external-Prometheus, NodePort, explicit CPU-counter, memory-gauge, continuity, reset, and numerical cross-check gates.

Run 17 remains prohibited unless it is separately authorized after the v4.2 live-dry validation and preregistration freeze.

## New outputs per condition

- `node_cpu_counter_delta.csv`: exact root-cgroup CPU counter delta over the condition window.
- `utilization_samples.csv`: 5-second node CPU and memory utilization observations.
- `utilization_summary.csv`: mean, median, nearest-rank P95, maximum, and exact-window CPU utilization factor.
- `metadata.txt`: virtual environment, machine capacity, utilization statistics, regime classification, and gate status.

## Pre-registered utilization definitions

- CPU factor: root-cgroup busy CPU cores divided by logical CPU cores.
- Memory factor: root-cgroup working-set bytes divided by machine memory bytes.
- Primary utilization variable: CPU utilization factor.
- Memory utilization: contextual covariate; it is not combined with CPU using an arbitrary weighted index.
- `STRICT_LOW_0_TO_1_PERCENT`: maximum observed CPU utilization is at most 1%.
- `PREDOMINANTLY_LOW_0_TO_1_PERCENT`: P95 is at most 1%, but the maximum exceeds 1%.
- `ABOVE_LOW_REGIME`: P95 exceeds 1%.

Classification is descriptive and does not discard an otherwise valid condition. Missing samples, capacity changes, stale/missing series, target discontinuity, or a counter reset fail closed.

## Installation

From WSL inside the extracted package directory:

```bash
./install_stage3c_v4_2.sh
```

Expected final status:

```text
RUN17_EXECUTED=NO
STATUS=PASS_STAGE3C_V4_2_INSTALLATION
```

## Live-dry validation

After installation, from the project directory with the external Prometheus and NodePort gateway running:

```bash
./run_stage3c_v4_2_live_dry.sh
```

This uses `RUN=0`, sends 1,500 diagnostic requests over approximately 315 seconds, and collects 64 utilization samples at 5-second intervals. It does not toggle the treatment and does not execute Run 17.

Expected final status:

```text
RUN17_EXECUTED=NO
STATUS=PASS_STAGE3C_V4_2_LIVE_DRY_VALIDATION
```

Do not execute `run_pair_v4.sh 17 ...` until the live-dry output has been reviewed and the analysis protocol has been frozen.

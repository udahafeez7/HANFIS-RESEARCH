# HANFIS External Protocol v3.0

This package runs a complete counterbalanced monitoring pair from WSL while
collecting synchronized measurements on the Mini PC/Kubernetes cluster and the
Jetson external client.

## Collected evidence

- Jetson HTTP latency, connection time, status code, and response size.
- Jetson `tegrastats` CPU/GPU/RAM/temperature/power telemetry.
- Kubernetes node CPU and memory.
- P0 container CPU and memory.
- Monitoring container CPU and memory when monitoring is ON.
- Relative SHA-256 manifests for portable verification.

## Prerequisites

- Run from the VS Code WSL Ubuntu terminal with the ANFIS environment active.
- Docker Desktop/Kubernetes must be available.
- WSL port-forward `127.0.0.1:18080` must return HTTP 200.
- Windows portproxy/firewall must allow the Jetson to reach the target URL.
- The Jetson must have `curl`, `tegrastats`, `timeout`, and synchronized NTP.

## Install on the Mini PC

Extract this package inside:

```text
C:\Research\ANFIS\Jetson Orin\Telemetry
```

Then, in WSL:

```bash
cd "/mnt/c/Research/ANFIS/Jetson Orin/Telemetry/hanfis_protocol_v3"
chmod +x run_pair_v3.sh server_collector_v3.sh jetson_capture_v3.sh
bash -n run_pair_v3.sh server_collector_v3.sh jetson_capture_v3.sh
```

## Run 7 (ON then OFF)

```bash
JETSON_HOST=jetson@10.176.68.250 TARGET_URL=http://10.176.68.28:18080/ ./run_pair_v3.sh 7 on-off
```

Enter the Jetson password once when the persistent SSH connection opens. The
script then performs condition changes, health checks, 120-second washouts,
synchronized acquisition, checksum verification, copying, and pair archiving.

If a condition aborts before `PASS_RUN...PAIR_ARCHIVED`, preserve its raw files
as an incident/partial attempt and repeat the complete pair. Never combine a
client-only attempt with server data from another attempt.

## Subsequent counterbalanced runs

```bash
./run_pair_v3.sh 8 off-on
./run_pair_v3.sh 9 on-off
./run_pair_v3.sh 10 off-on
```

Set `JETSON_HOST` and `TARGET_URL` again if the device addresses change.

## Output

The default output root is:

```text
C:\Research\ANFIS\Jetson Orin\Telemetry\RunsV3
```

Each pair contains separate `on` and `off` directories, and each condition
contains `server` and `client` evidence plus manifests and SHA-256 files.

## Scientific interpretation

The independent unit is the complete run pair, not each request or two-second
sample. Request and telemetry samples are repeated observations nested within a
run. Do not claim causal overhead from one pair.

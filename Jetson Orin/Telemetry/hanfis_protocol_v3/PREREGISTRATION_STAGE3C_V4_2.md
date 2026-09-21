# HANFIS Stage 3C v4.2 — Measurement Preregistration Freeze

## Status and scope

This document freezes the server-side observability measurement protocol after a successful live-dry validation. It does not authorize, start, or label Run 17. A future confirmatory acquisition requires a separate run-specific record containing the treatment order and the exact authorization token `CONFIRM_RUN17=YES_RUN17`.

Protocol identifier: `HANFIS_STAGE3C_V4_2_UTILIZATION_GATED`

## Frozen topology and preflight requirements

- Jetson endpoint host: `jetson@10.176.68.96`.
- Workload target: `http://10.176.68.126:30080/` through the Windows/Docker gateway and Kubernetes NodePort.
- Local gateway check: `http://127.0.0.1:30080/` must return HTTP 200.
- Internal Prometheus pod must be Running and all containers Ready.
- External Prometheus endpoint: `http://127.0.0.1:29090` must be Ready.
- External cAdvisor targets: exactly 2 of 2 must be healthy.
- Python environment name: `anfis`.

Any failed preflight condition places acquisition on HOLD.

## Frozen workload and collection window

- Requests: 1,500.
- Request interval: 0.21 seconds, scheduled from an absolute start epoch.
- Intended workload span: 314.79 seconds.
- Collector samples: 64.
- Collector interval: 5 seconds.
- Collection span: 315 seconds.
- PromQL CPU rate window: 30 seconds.
- PromQL settlement delay: 5 seconds before boundary queries.

## Frozen metrics and estimands

- CPU counter: `container_cpu_usage_seconds_total`.
- Memory gauge: `container_memory_working_set_bytes`.
- Capacity denominators: `machine_cpu_cores` and `machine_memory_bytes`.
- Primary node utilization: root-cgroup CPU busy cores divided by logical machine cores.
- Memory utilization is contextual telemetry and is not a treatment-effect endpoint.
- Explicit start/end counter deltas are primary for auditability. PromQL `increase()` and `rate()` are independent numerical cross-checks.

## Utilization regime classification

- `STRICT_LOW_0_TO_1_PERCENT`: maximum CPU utilization is at most 1%.
- `PREDOMINANTLY_LOW_0_TO_1_PERCENT`: P95 is at most 1%, but maximum exceeds 1%.
- `ABOVE_LOW_UTILIZATION_REGIME`: P95 exceeds 1%.

The regime is descriptive. It must not be used post hoc to delete observations or redefine the primary endpoint.

## Fail-closed acceptance gates

All of the following must pass:

1. Target availability and continuity for every expected series.
2. Stable series identity across the measurement boundaries.
3. No negative counter delta or detected CPU counter reset.
4. Boundary settlement completeness.
5. Exact snapshot cross-check within the frozen numerical tolerance.
6. `rate()`/`increase()` coherence within the frozen numerical tolerance.
7. Strict PromQL cross-check.
8. Node-utilization metric availability and valid denominators.
9. Exactly 64 utilization samples and 64 target-health samples.
10. Exactly 1,500 workload records, all HTTP 200, with zero workload failures.
11. Empty collector error log and valid SHA-256 manifest.

A failed or missing gate makes the acquisition invalid and places the run on HOLD; it must not be silently imputed or accepted.

## Planned analysis and interpretation

For a separately authorized paired run, report latency mean, median, P95, P99, bootstrap 95% confidence interval, exact sign-flip p-value, failure rate, and CPU/memory footprint. Use the preregistered condition order and paired identifiers. If `p > 0.05`, state only that H0 was not rejected; do not claim equivalence or universal absence of effect.

The live-dry result validates the measurement pipeline and gates. It is not evidence for an ON-versus-OFF treatment effect.

## Change control

Changes to metric definitions, labels, windows, tolerances, sample counts, request pacing, gates, or estimands require a new protocol version, a new static/mock test, and a new live-dry validation before any confirmatory acquisition.

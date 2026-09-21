# HANFIS Run 17 — Stage 3C v4.2.1 preregistration amendment

Date: 2026-09-11 (Asia/Jakarta)

## Reason

The first authorized Run 17 invocation stopped before treatment assignment and
before any workload request. The runner reported `ENDPOINTS=0` although both
local and Jetson NodePort probes returned HTTP 200 and the final preflight had
already found two ready EndpointSlice endpoints. This was a false negative in
the runner's JSONPath/awk endpoint-count implementation.

## Change

Only `preflight_nodeport()` in `run_pair_v4.sh` changes:

- parse EndpointSlice JSON with Python and count ready addresses;
- independently parse classic Endpoints JSON as a compatibility fallback;
- use the larger non-negative count as `EFFECTIVE_ENDPOINTS`;
- require endpoint count >= 1, gateway Running, and HTTP 200 from WSL and Jetson;
- retry the complete metadata-and-traffic gate up to three times, two seconds apart.

## Unchanged protocol

Run number 17, ON-OFF order, 1,500 requests per condition, 0.21-second request
interval, 5-second telemetry interval, 120-second washout, Prometheus queries,
collector algorithms, numerical tolerances, output schemas, and all fail-closed
resource gates remain unchanged.

## Prior-attempt disposition

The failed invocation is classified as a pre-acquisition infrastructure-gate
failure. It produced no condition dataset and does not count as an experimental
attempt. Any invocation that has created a condition manifest is treated as a
partial acquisition and blocks this recovery script.

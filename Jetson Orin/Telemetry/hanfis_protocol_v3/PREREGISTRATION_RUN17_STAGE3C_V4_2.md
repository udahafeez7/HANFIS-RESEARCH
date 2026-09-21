# HANFIS Run 17 Run Specific Preregistration

## Status

This record fixes the Run 17 acquisition design before execution. It does not authorize or execute Run 17.

- Protocol: `external-prometheus-v4.2-utilization-gated`
- Run number: 17
- Treatment order: `ON-OFF`
- First condition: monitoring ON
- Second condition: monitoring OFF
- Washout between treatment changes: 120 seconds
- Requests per condition: 1,500
- Request interval: 0.21 seconds using absolute-deadline pacing
- Expected workload span: 314.79 seconds per condition
- Server sampling interval: 5 seconds
- Expected server samples: 64 per condition
- PromQL CPU rate window: 30 seconds
- External observer: `http://127.0.0.1:29090`
- Expected external cAdvisor targets: exactly 2 of 2 healthy
- Access path: Jetson to Windows Docker gateway to Kubernetes NodePort
- Workload target: `http://10.176.68.126:30080/`

The ON-OFF order follows the OFF-ON order used for Run 16. If a Run 18 extension is approved, its planned complementary order is OFF-ON to restore order balance across the two new-protocol runs.

## Acceptance gates

Each condition and the final pair are accepted only when all frozen Stage 3C v4.2 gates pass, all 1,500 workload requests return HTTP 200, the error log is empty, all 64 utilization and target samples exist, and all SHA-256 checks succeed.

Any unavailable target, missing series, series identity change, counter reset, boundary failure, PromQL disagreement, incomplete workload, time-synchronization failure, or checksum mismatch produces HOLD. Failed observations are not silently imputed or accepted.

## Analysis plan

Report paired latency mean, median, P95 and P99; failure rate; CPU and memory footprint; bootstrap 95 percent confidence intervals; and exact paired sign-flip p-values. Preserve event identifiers and timestamps. Analyze Run 17 first as a protocol-v4.2 acquisition. Do not pool it directly with Runs 7 to 16 without protocol-stratified and sensitivity analyses.

If a hypothesis test returns p greater than 0.05, report failure to reject H0. Do not claim equivalence or universal absence of an effect.

## Authorization boundary

The preflight tool must finish with `STATUS=PASS_RUN17_FINAL_PREFLIGHT`. Run 17 remains locked until the researcher separately sets the exact authorization token `CONFIRM_RUN17=YES_RUN17`.

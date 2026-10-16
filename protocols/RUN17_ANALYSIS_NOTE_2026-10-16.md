# Run 17 (protocol v4.2.2) — analysis-unit note

Date: 2026-10-16 (Asia/Jakarta)
Status: APPROVED 2026-10-16 by the researcher.

## Purpose and scope

This note records interpretation choices for the analysis of the Run 17 attempt-2 pair
(`RunsV4/run17-on-off-20260911T145755+0700`, pair archive `O5-V4-run17-on-off-20260911T145755+0700-pair.tar.gz`,
`STATUS=PASS_RUN17_PAIR_ARCHIVED`, manifest `STATUS=LOCKED_VALID_PAIR`).
It does not change `PREREGISTRATION_RUN17_STAGE3C_V4_2.md`, `PREREGISTRATION_STAGE3C_V4_2.md`,
the v4.2.2 amendment, or any frozen code. It fixes how the wording "exact paired sign-flip p-value" and
"bootstrap 95% confidence interval" is read for a single pair.

## What has been inspected before this note (to be confirmed by the researcher before commit)

- The attempt-2 console log: gate statuses, row counts, utilization summaries (CPU utilization mean, P95, maximum per condition).
- `pair-manifest.txt` and the archive checksum.
- Not inspected: per-request latency values, tegrastats content, or any ON-versus-OFF difference.

[x] The researcher confirms that no per-request latency or ON-OFF difference has been looked at.

## Decisions

1. Inferential unit. One complete run pair, never an individual request or telemetry sample
   (the same rule as the docstring of `analyze_cumulative_v3.py`).
2. Run 17 alone is one pair (n = 1). At run level the bootstrap interval is undefined
   (`bootstrap_ci` in the v3 code returns NaN for fewer than two values) and the exact sign-flip p-value is 1.0.
   Both are reported as such. No hypothesis test is run on Run 17 alone.
3. Run 17 is analyzed first and separately as a protocol-v4.2 acquisition, descriptively:
   per condition mean, median, P95, P99 and failure rate of latency; ON minus OFF point differences paired by
   sequence identifier; CPU and memory footprint from the pre-registered files; the utilization regime as
   labeled by the collector (both conditions `STRICT_LOW_0_TO_1_PERCENT`), used only descriptively and never to exclude data.
4. An optional request-level bootstrap interval may be shown only as within-run descriptive precision, with a
   fixed seed and a label saying it is not inferential and not a test of the registered hypothesis.
5. Pooling. Run 17 is not pooled directly with Runs 7 to 16. Any combined analysis is protocol-stratified
   (stratum external-v3.0 with its 10 pairs; stratum v4.2.x with Run 17 and any approved extension) with a
   sensitivity analysis, as the run-specific preregistration requires. The exact sign-flip test is applied within
   a stratum only.
6. Attainable precision. The smallest two-sided exact sign-flip p-value for n pairs is 2/2^n:
   n = 1: 1.0; n = 2: 0.5; n = 5: 0.0625; n = 6: 0.03125. The v4.2.x stratum cannot reach p < 0.05 before six pairs.
   Run 17 plus a Run 18 therefore cannot support a test by themselves.
7. Order. Run 17 is ON-OFF only, so treatment order and period are confounded in this pair.
   The preregistration names OFF-ON as the planned complementary order of a Run 18 extension, which is not approved.
8. Interpretation. If a test later returns p > 0.05, report only that H0 was not rejected; make no claim of
   equivalence or of absence of an effect. Claims remain within guard P11 (no causal claim about observability overhead).
9. Code. The v3 pair analyzer appears to assume 32 samples per condition (`range(1, 33)`) and the v3 directory
   layout, while v4.2 has 64 samples and a different layout. A v4.2 pair analyzer must be written, tested on the
   `RUN=0` live-dry output (which is not treatment evidence) and committed before it is run on Run 17.
   Bootstrap defaults follow the v3 cumulative script (20,000 repetitions, seed 20260829) unless stated otherwise here.

## Open items

- Whether to approve a Run 18 (OFF-ON) extension, and, if so, how to record the topology change
  (the frozen v4.2 topology lists the old 10.176.68.x network; the current testbed uses 10.44.x).
- Utilization scope: the Run 17 primary instance regex is `desktop-worker.*`; the 1.4% and 2.1% figures quoted
  elsewhere are two-node sums from another campaign. The manuscript sentence that cites them needs the campaign and definition stated.

Approved by: Hafiz   Date: 2026-10-16

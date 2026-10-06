# HANFIS Comparison Protocol — checkpoint 14 September 2026

## Objective

Produce a defensible progress report by 22 September 2026 comparing:

1. FuzzyFortify as a frozen, expert-defined Mamdani baseline;
2. flat ANFIS with full rules and a parameter-matched variant;
3. HANFIS with the approved 3–3–3 hierarchical architecture.

The report is a progress report, not a precommitted claim that HANFIS is superior.

## Frozen evidence checkpoint

- Run 17 Attempt 2 is the valid ON–OFF telemetry pair and is archived.
- Run 17 Attempt 1 is excluded because an instrumentation gate failed.
- Monitoring was restored to ON.
- Run 17 must not be repeated merely to improve an observed result.
- Runs 7–16 (protocol v3) and Run 17 (protocol v4.2) remain separate until a
  documented bridge analysis establishes comparability.

## Two evidence tracks

### A. Predictive comparison

The unit of analysis is an `event_id`. Every model receives the same eligible
events, target, preprocessing, outer split, and evaluation metric.

Required columns for the common evaluation table:

- `event_id`, `asset_id`, `timestamp_utc`;
- the seven approved HANFIS features;
- `dynamic_risk_target` and its provenance;
- native FuzzyFortify inputs: `complexity_resilience_index`, `impact`,
  `base_score`, and `exploitability`.

No unreported proxy mapping is permitted. If native FuzzyFortify inputs cannot
be produced for an event, that event is not eligible for the strict three-model
comparison. Any extended/adapted FuzzyFortify model is a sensitivity analysis,
not the frozen baseline.

Primary predictive metrics: RMSE, MAE, and R² on the 0–100 target scale.
Report seed/fold-level values, central tendency, dispersion, and uncertainty.

### B. Observability comparison

The unit of inference is the paired ON/OFF run, never an individual HTTP request
or a five-second telemetry sample. Report latency paired differences, explicit
CPU counter delta/utilization, five-second memory gauge summaries, monitoring
footprint, continuity/reset gates, and acquisition failures. Raw samples may be
plotted but must not be treated as independent replicates.

## Fairness controls

| Control | Requirement |
|---|---|
| Data | Exact same eligible `event_id` set for all three models |
| Split | Grouped by asset or chronological with embargo; no random real-data split |
| Scale | Inputs documented; target evaluated on 0–100 for all models |
| ANFIS capacity | Report full flat ANFIS and parameter-matched flat ANFIS |
| Training | Same seeds, folds, stopping policy, and optimization budget |
| HANFIS leakage | Out-of-fold tier-one predictions only |
| FuzzyFortify | Frozen published FIS; no training on evaluation labels |
| Efficiency | Rules, parameters, training/inference time, CPU, and memory |
| Failure policy | Non-convergence, missing events, counter reset, or incomplete telemetry is HOLD |

## Reproduction gate discovered today

The published FuzzyFortify paper specifies four input membership-function sets,
four output sets, six rules, Mamdani min/max inference, maximum aggregation, and
discrete-centroid defuzzification. A literal implementation of those printed
specifications does not reproduce the five risk scores in the paper's results
table. This is a reproducibility gap, not permission to tune the baseline.

Until the original FuzzyFortify source or missing rule details are recovered:

- use the literal implementation for transparency;
- publish the five-case reproduction audit;
- do not claim its RMSE comparison is a definitive replication of the original;
- report both the published table values and the literal-reproduction values.

## Milestones to 22 September

| Date | Deliverable | Exit gate |
|---|---|---|
| 14 Sep | Freeze comparison protocol and audit FuzzyFortify reproduction | Inputs/rules/source citation recorded; gap quantified |
| 15 Sep | Build canonical event-level comparison table | Unique `event_id`; units and target provenance pass |
| 16 Sep | Run smoke tests and scale/leakage checks | No target ÷100 defect; no real-data random split |
| 17 Sep | Execute repeated grouped/temporal model comparison | All ANFIS submodels converge |
| 18 Sep | Complexity and efficiency measurements | Same hardware/process protocol documented |
| 19 Sep | Telemetry bridge analysis v3 versus v4.2 | Pool or stratify decision documented |
| 20 Sep | Matplotlib manuscript figures | Figures generated only from validated artifacts |
| 21 Sep | Draft progress report and internal QA | Tables, figures, claims, limitations cross-checked |
| 22 Sep | Release progress report | Reproducibility bundle, checksums, and report frozen |

## Required figures

1. Per-model predictive error with uncertainty.
2. Predicted versus observed dynamic risk by model.
3. Rule count and parameter count versus RMSE.
4. Training and inference time by model.
5. Paired latency ON minus OFF by run and order.
6. CPU explicit delta/utilization and five-second memory footprint.
7. Telemetry continuity/reset gate matrix.
8. Sensitivity plot stratified by telemetry protocol version.

## Claim boundary

By 22 September, success means a reproducible comparison pipeline and an
evidence-backed progress report. A Q1-level superiority claim requires a valid
attack-labelled event dataset, sufficient independent groups/time windows,
external or nested validation, and a resolved FuzzyFortify reproduction gap.

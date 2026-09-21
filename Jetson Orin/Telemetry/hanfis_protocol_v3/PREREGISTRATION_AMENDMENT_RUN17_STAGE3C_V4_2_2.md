# HANFIS Run 17 — Stage 3C v4.2.2 preregistration amendment

Date: 2026-09-11 (Asia/Jakarta)

## Trigger and disposition

Run 17 attempt 1 reached both ON and OFF workloads. The OFF client completed
1,500/1,500 HTTP 200 requests, but the server collector stopped before OFF
sampling because six historical monitoring CPU series remained queryable.
Kubernetes reported zero monitoring resources. At both OFF boundaries,
`rate()`-active series were zero and the 30-second CPU counter increase was
zero; the retained series disappeared by the end boundary. Attempt 1 is an
instrumentation-gate failure and is excluded from confirmatory paired analysis.

## Root cause

The v4.2 collector equated presence of a cumulative Prometheus/cAdvisor series
with a live monitoring process. Prometheus lookback and cAdvisor retention can
return labels for terminated containers. Therefore presence alone is not a
valid activity test.

## v4.2.2 gate definition

- Kubernetes must show exactly zero ready monitoring pods before and after the
  OFF workload.
- During every five-second OFF sample, the 30-second `increase()` of monitoring
  CPU counters must be no greater than 0.000001 CPU-seconds.
- Retained monitoring CPU labels and memory gauges are recorded as provenance
  but excluded from OFF resource totals when the activity gate is zero.
- Any positive activity above tolerance fails closed.
- ON continues to require monitoring series continuity and complete resource
  sampling.
- P0 readiness, NodePort HTTP 200, two external targets, node utilization,
  snapshot, rate/increase, counter-reset, continuity, and checksum gates remain.

## Repeat rule

A fresh complete ON-OFF pair may be designated Run 17 attempt 2 only after the
v4.2.2 static/mock suite and a 315-second OFF live-dry validation both pass, the
attempt-1 evidence archive is preserved, and a new immutable freeze is created.
No attempt-1 observation may enter the confirmatory paired dataset.

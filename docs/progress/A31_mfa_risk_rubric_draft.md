# A-31 (draft) — MFA Risk (x4) Scoring Rubric for New Candidate Assets

Status: **DRAFT — awaiting Hafiz's confirmation**, not yet frozen, not yet
referenced by the manuscript (consistent with A-30's decision that
manuscript §3.1/§3.7 updates are deferred until final 120-asset values
and the E4 rerun are complete).

Layer: Mathematical Scheme §3 (definition of x4) + data contract v2.
Context: A-30 closed the telemetry-vs-static-metadata debate for x5
(Kubernetes Exposure) and x6 (Asset Criticality) with explicit, auditable
rubrics, but left x4 (MFA Risk) unscored — "cannot be telemetered at
present (requires IAM/OIDC integration not yet in the testbed); stays
static, rubric not yet written." This fills that gap, using the same
discrete-value house style already established for x5 (0 / 0.5 / 1)
rather than introducing a third scoring format alongside x5's discrete
scale and x6's three-factor sum.

## Rubric: `mfa_risk` (scale 0 / 0.5 / 1)

| Value | Criteria |
|---|---|
| **0** | Component has no role in any authentication or credential-handling path; compromising it exposes no credential material and does not affect any authentication decision. |
| **0.5** | Component indirectly touches credential-adjacent material (e.g., stores or transmits secrets without itself making an authentication decision), OR its output informs — but does not itself enforce — an authentication/authorization decision elsewhere. |
| **1** | Component directly enforces an authentication/authorization decision (gates pass/fail), OR compromising it could expose or forge credentials usable against other cluster components. |

## Draft scores for the 11 candidates (mechanical application, NOT final)

| asset_id | mfa_risk (draft) | Rationale |
|---|---|---|
| gatekeeper-3-17 | 0 | Policy evaluation only; does not touch credentials or authN decisions. |
| cilium-1-16 | 0 | Network-layer (CNI); no credential or authN role. |
| istio-proxy-1-23 | 0.5 | Can carry mTLS identity context per-request but does not itself issue/verify end-user credentials. |
| kafka-3-8 | 0 | Message transport; no credential custody by default. |
| velero-1-15 | 0.5 | Backup payloads may contain credential material (Secrets) at rest, without Velero itself making authN decisions. |
| metrics-server-0-7 | 0 | Read-only metrics; no credential path. |
| cosign-2-4 | 0.5 | Verifies signing identity (adjacent to authN) but does not gate user/service authentication directly. |
| external-secrets-0-10 | **1** | Directly retrieves and materializes credentials from an external vault into cluster Secrets — a credential-handling component by definition. |
| kube-state-metrics-2-13 | 0 | Read-only observability; no credential path. |

This table is a mechanical first pass, same caveat as A-30's draft table:
**Hafiz reviews/revises before anything is written to
`configs/assets_candidates_toward120.csv`.**

## Next steps (unchanged from A-30's open checklist)

1. Hafiz reviews/revises this draft (and A-30's existing draft for
   `kubernetes_exposure` + `asset_criticality`).
2. Once all three columns are final → run
   `scripts/apply_rubric_draft_values.py` (extend it to also cover
   `mfa_risk`, or add a companion script) then
   `scripts/merge_candidates_into_assets.py --dry-run`.
3. After a clean merge → rerun `build_asset_weeks.py`, rerun E4.
4. **Only then** update manuscript §3.1/§3.7 — per A-30, not before.

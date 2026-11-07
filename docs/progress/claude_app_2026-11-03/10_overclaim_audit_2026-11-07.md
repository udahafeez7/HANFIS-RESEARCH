# Over-claim audit of hypotheses and contributions (7 November 2026)

Source: reading of `sn-article_2026-11-03.pdf` (48 pages) and `additional_file_1_2026-11-03.pdf`. This is judgment, not measurement. The frozen protocol text (`protocols/E4_preregistration_2026-09-29*.md`) was not checked and must be read before any hypothesis is renamed.

> Storage note (7 November, repository session): saved as received from the Claude app, where it was named `08_overclaim_audit_2026-11-07.md`; renamed 10 here because file 08 already holds the repository cross-check of the benchmark review. The cross-check of this audit is in `11_hasil_E26_E27_dan_verifikasi_audit_2026-11-07.md`.

## Rules that still apply to every experiment below

1. E7 is locked (tag `e7-results-2026-11-02`). No `--redo`, no `--today`, no re-evaluation, no tuning on E7 outcomes.
2. Registered decisions (H1a, H1b, H1c, H2 as labelled in Table 4, P7a to P7f) do not change. Anything new is post hoc and descriptive, written into a protocol file and committed before it runs, with seeds fixed and every outcome reported.
3. Post hoc results carry no multiplicity correction and go in Additional file 1 unless they replace a claim the body cannot support.
4. A claim the body cannot support is first narrowed in wording (no experiment needed). An experiment is run only if the author wants the stronger claim back.

## Audit table

| # | Item | Problem | Risk | Wording fix (no experiment) | Experiment if the claim is to be kept (post hoc, descriptive) |
|---|---|---|---|---|---|
| 1 | C2 and H2 (efficiency) | Training time, peak memory, throughput and inference latency are promised in Section 1, C2 and H2, but only rule and parameter counts (Table 1) appear. The reduction m^7 to 2m^3+m_I^2 m is the hierarchical-fuzzy arithmetic of Raju (1991) and Wang (1998), not a new strategy. | High | Narrow C2 and the Section 1 sentence to "rule and parameter counts (Table 1)". Report H2 as confirmed for counts by construction; state that time, memory and latency were not measured. | First read the durations already logged by E4-bis (5 folds x 5 seeds x 3 restarts); if present, tabulate them. If absent, time training and inference of the 25 saved models and of the flat ANFIS variants on one machine, same data, fixed seeds, several repetitions, report median and range, no hypothesis test. |
| 2 | C3 | The label (Eq. 7) uses only EPSS, KEV and reachability. MFA, Kubernetes exposure and asset criticality never enter it. It defines near-term exploitability exposure, not cybersecurity risk (no impact term). | High | Use "exploitability exposure" in C3 and the Abstract. Title kept by author decision on 3 November; remains a reviewer risk. | None. This is a definition, not a testable claim. A risk claim would need an outcome that depends on the environment (incident or impact data). |
| 3 | C1 | Panel E has no demonstrated role: environment inputs carry 3.3% of Shapley attribution and the label ignores them. The Discussion already says the decomposition is unsupported. | Medium-high | Present C1 as an architecture design, not as a demonstrated benefit. Keep "continuously recalculated" only if described as weekly recalculation from sealed EPSS and KEV snapshots. | None needed. Any test of the environmental panel requires an environment-dependent outcome that this inventory does not have. |
| 4 | H3 | Defined in Section 1, never decided. Table 4 labels the matched-flat comparison "H2". | High | After reading the frozen protocol, make the labels match it. Either rename Table 4 and every matched-flat "H2" to H3 and report H2 separately, or redefine H3 in the text to match what was registered. | None. The decision comes from existing E4-bis output (SS 0.665 [0.269, 0.844] against FlatANFISMatched). |
| 5 | H4 | Defined as HANFIS with versus without x7. E9 removes x2 and x7 together. Not tested as stated, and no sentence says so. | High | Add one sentence in 4.8 or Limitations: H4 was not tested as stated; E9 removes x2 and x7 together. | A retrain without x7 only, on the E4-bis folds, seeds, embargo and hyperparameters used in E9, compared with full HANFIS. Label post hoc. The result cannot confirm H4 as a registered hypothesis. |
| 6 | H2/H3 against matched flat ANFIS | The margin comes mostly from fold 0 (91% of the gap; SS 0.183 against matched and 0.084 against full flat without it). The matched model predicts from -6.679 to 11.059 on a label that sits near zero, which suggests a weak baseline. Section 1 pre-commits to reading a flat-ANFIS plateau as evidence for the mechanism. | Medium-high | Put the fold-0 caveat in the Abstract beside the 66.5%. Delete the sentence that treats a plateau as evidence for the mechanism. | Optional: a sensitivity run of the matched model with a different number of subtractive-clustering centres, on existing folds. Report as post hoc. It would show how much the result depends on the baseline configuration. |
| 7 | H1a | Confirmed, but CVSS does not receive x2 or x7, and E9 shows HANFIS has no skill over CVSS without them. | Medium | State beside Table 4 that the CVSS comparator has no access to the two inputs that carry the skill. | None. |
| 8 | H1c | Ridge on all seven inputs is itself worse than persistence (SS -2.293), and the interaction ridge on x2, x7 beats HANFIS (E11, skill -0.529). "69.6% against a linear model" in the Abstract overstates. | Medium | Name the comparator: "ridge on all seven inputs". | None. E11 already contains the stronger linear comparator. |
| 9 | "Two further contributions are established" (Conclusion) | The monotonicity ablation uses two synthetic scenarios and five seeds. | Medium | Replace "established" with "indicated" for the ablation. | Optional: more seeds on the same two scenarios. Not needed if the wording is changed. |
| 10 | Discussion and Conclusion: "readable rule base", "documented response surface" | No trained rule or response surface is shown; E6 attribution failed its criterion. | Medium | Soften, or support. | Documentation only: print the 34 rules of one seed from the 25 saved models in Additional file 1, and plot r over (x2, x7) from the five-seed ensemble. Describe as descriptive. No training. |
| 11 | P7a "supported" | The hypothesis is that HANFIS is not better than persistence, so "supported" can be read as the opposite. | Low | Write "supported (HANFIS not better)" in Table 10 and the text. | None. |

## Best-supported contribution

C4: tagged and registered protocol, a single forward run, disclosed post hoc origin of P7e and P7f, negative results reported. Lead with it in the cover letter.

## Order suggested

1. Rows 4 and 1 first (they decide wording in Section 1, Table 4, 4.3, 4.5 and the Conclusion).
2. Rows 5, 2, 3, 7, 8, 9, 11 are wording only.
3. Rows 10 and 6 are optional presentation or sensitivity work.
4. Row 1 timing and row 5 retrain are the only items that need computation; write their protocol first.

---
Prepared with AI assistance (Claude, Anthropic) from the uploaded manuscript PDFs in the 7 November 2026 session. Numbers are quoted from the PDF; risk labels are judgment.

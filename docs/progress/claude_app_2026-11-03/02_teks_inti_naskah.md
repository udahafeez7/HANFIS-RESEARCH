# Teks inti naskah (kutipan verbatim, 3 November 2026)

Semua blok di bawah berbentuk LaTeX karena disalin dari `manuscript/sn-article.tex`. Jangan menyunting di sini lalu menempelkan balik; kirim usulan perubahan sebagai pasangan teks lama dan teks baru agar bisa diterapkan lewat skrip.

## Judul

```latex
HANFIS: A Hierarchical Adaptive Neuro-Fuzzy Inference System for Evidence-Based Dynamic Cybersecurity Risk Scoring in Cloud-Native Kubernetes Deployments
```

## Abstrak

```latex
Static, expert-weighted fuzzy risk scores go stale between elicitations, while a flat Adaptive Neuro-Fuzzy Inference System (ANFIS) over seven risk inputs requires 128 rules and 1{,}052 parameters. We propose a hierarchical ANFIS (HANFIS) that separates vulnerability and environmental reasoning before an integration tier adds threat intelligence, reducing the model to 34 rules and 176 parameters (73.4\% and 83.3\% fewer). We build a temporal exploitability-exposure target from sealed weekly Exploit Prediction Scoring System (EPSS) and Known Exploited Vulnerabilities (KEV) snapshots for 120 container images (6{,}357 asset-weeks), evaluated with grouped, embargoed splits. A 4-week persistence baseline lowers mean squared error relative to climatology by 97\%; a single Common Vulnerability Scoring System (CVSS) score, by 22\%. Under a protocol frozen before training, HANFIS reduces mean squared error by 96.7\% against CVSS, 69.6\% against a linear model and 66.5\% against a parameter-matched flat ANFIS (95\% bootstrap intervals excluding zero), but is not distinguishable from persistence. Post hoc analyses qualify these gains. Exact Shapley attribution puts 78.9\% on exploitability and the KEV indicator, ingredients of the label, and without them HANFIS has no skill over CVSS (skill $-0.14$, interval $-0.34$ to $0.05$). A four-parameter formula of those two inputs, $100\max(x_2,0.1\,x_7)$, has a lower error than HANFIS at four weeks (skill $-0.53$, interval $-1.44$ to $-0.21$); the gap narrows at longer horizons only through weeks around an EPSS model change. In a pre-registered forward evaluation, the formula beat persistence and HANFIS did not beat the formula. The data cannot show whether environmental context helps.
```

## Kontribusi

```latex
The principal contributions of this study are stated as follows:
\begin{enumerate}
    \item[\textbf{C1.}] A domain-informed HANFIS architecture that separates vulnerability and environmental reasoning before integrating their outputs with dynamic threat intelligence to produce a continuously recalculated Dynamic Risk Score.
    \item[\textbf{C2.}] A computational optimization strategy that changes exhaustive rule growth from $m^{7}$ to $2m^{3}+m_I^{2}m$, accompanied by empirical measurements of parameter count, training cost, memory consumption, throughput, and inference latency.
    \item[\textbf{C3.}] An operational definition of dynamic cybersecurity risk that combines CVSS Base severity, patch condition, MFA weakness, Kubernetes exposure, asset criticality, and time-varying threat evidence without duplicating CVSS threat metrics.
    \item[\textbf{C4.}] A reproducible evaluation against persistence, single-CVSS, ridge and flat ANFIS baselines (full and parameter-matched), using predictive and computational metrics under common grouped, embargoed temporal partitions. Post hoc information-minimal and formula baselines, an ablation of the label-ingredient inputs and a horizon sweep complement it (Sections~\ref{subsec:e9} and~\ref{subsec:e14}). A pre-registered forward evaluation on six weeks after the protocol freeze tests the formula and HANFIS against persistence (Section~\ref{subsec:e7-results}). A Fuzzyfortify comparison is not claimed (Section~\ref{subssec4.3}).
\end{enumerate}
```

## Hipotesis

```latex
The empirical analysis is guided by the following hypotheses:
\begin{description}
    \item[\textbf{H1a: Improvement over static expert scoring.}] HANFIS will produce significantly lower risk-estimation error than a single CVSS score, the current-practice baseline.
    \item[\textbf{H1b: Improvement over naive persistence.}] HANFIS will reduce mean squared error relative to a causal 4-week persistence forecast by at least a smallest-effect-size-of-interest of 5\%, with the lower bound of its 95\% confidence interval above zero. Persistence, not a single CVSS score, is the empirically strongest baseline observed on the pilot dataset (Section~\ref{subssec4.3}) and is therefore the bar HANFIS must clear, not an optional comparator.
    \item[\textbf{H1c: Value of hierarchical structure over a linear model.}] HANFIS will be non-inferior to a ridge-regularised linear model on the same seven inputs, with superiority reported when the confidence interval excludes zero.
    \item[\textbf{H2: Computational efficiency.}] For an equivalent input set and membership-function configuration, HANFIS will require significantly fewer fuzzy rules and adaptive parameters and will reduce training time, peak memory, and inference latency relative to flat grid-partitioned ANFIS.
    \item[\textbf{H3: Performance preservation.}] The predictive performance of HANFIS will be non-inferior to a parameter-matched flat ANFIS (FlatANFISMatched, $\pm 5\%$ parameters) within a prespecified margin, despite the reduction in rule-base complexity. A flat ANFIS's plateau below the full-capacity reference is treated as evidence for the mechanism this decomposition trades away (cross-subsystem interaction discarded by the scalar inter-tier bottleneck) rather than as a falsification of H2/H3 by itself.
    \item[\textbf{H4: Threat responsiveness.}] Including time-varying Threat Intelligence will improve the prioritization of actively exploited or high-probability vulnerabilities compared with an otherwise identical HANFIS without this input.
\end{description}
\textbf{H5 (edge execution)}, originally framed as a fifth hypothesis, is demoted to future work: the Jetson Orin Nano node in the present testbed is a telemetry client only, and HANFIS inference runs cluster-side, so no edge-execution timing evidence exists to test it against.
```

H5 (eksekusi di edge) diturunkan ke pekerjaan lanjutan; H1a sampai H5 tidak boleh diubah kata per kata.

## Discussion: kalimat hasil maju

```latex
The post hoc analyses of Sections~\ref{subsec:e8} and~\ref{subsec:e9} limit how far these findings generalise. Exact Shapley attribution places 78.9\% of the model's attribution on exploitability and the KEV indicator, which are ingredients of the realised label, and only 3.3\% on the three environmental inputs. Without those two inputs the model shows no demonstrable skill over a single CVSS score, and it is not demonstrably better than gradient boosting restricted to them. What the data support is therefore narrower. A 34-rule hierarchical model estimates near-term exploitability exposure from current EPSS and KEV signals about as accurately as a persistence forecast that needs past labels (the two are not distinguishable), and more accurately than generic linear and boosted models. It is not more accurate than a four-parameter formula of the same two signals (Section~\ref{subsec:e9}); this formula, together with the interaction ridge, has the lowest error of all predictors we compared at the four-week horizon. At eight and twelve weeks the gap to the formula narrows, but only through weeks around the EPSS model change (Sections~\ref{subsec:e14} and~\ref{subsec:e16}). The ranking of assets by predicted risk is almost the same for all predictors at four weeks (Section~\ref{subsec:e15}). The data do not support the claim that the vulnerability--environment decomposition, or the environmental inputs, improve prediction. Because the target is built from EPSS, KEV and reachability alone and does not depend on the three environmental inputs, this inventory is not designed to show a benefit of those inputs even if one exists; testing that benefit requires an outcome that depends on the environment, such as incident or impact data. Forward weeks confirm the earlier finding: a max-form formula in the exploitability and threat-intelligence inputs matches or beats the trained model, and HANFIS adds structure and a readable rule base, not accuracy (Section~\ref{subsec:e7-results}). In those weeks HANFIS was not better than persistence (P7a) and its blend with persistence was worse than persistence alone (P7b). We did not test why the trained model transferred worse than the formula.
```

## Conclusion

```latex
\section{Conclusion and Future Work}\label{sec6}

This paper proposes HANFIS, a domain-informed hierarchical ANFIS. It reduces a 128-rule, 1{,}052-parameter flat Sugeno system over seven cloud-native risk inputs to 34 rules and 176 parameters (Section~\ref{subsec:hanfis-architecture}) by separating vulnerability and environmental reasoning into two first-tier panels before an integration tier combines them with dynamic threat intelligence. Under a protocol frozen and dated before training began (Table~\ref{tab:e4-results}), HANFIS confirms a substantial reduction in estimation error against a single CVSS score (H1a), a linear model over the same seven inputs (H1c), and a parameter-matched flat ANFIS initialised by subtractive clustering (H2). It is not distinguishable from a causal 4-week persistence forecast (H1b), which the study's own mandatory baselines (Section~\ref{subssec4.3}) show to be a far harder bar than static expert scoring. The pooled margin over the matched model is dominated by the first block, where training is thinnest, so it is read as suggestive of a structural advantage of the vulnerability/environmental/threat decomposition, not as evidence for one (Section~\ref{subssec4.5}).

Post hoc analyses qualify this further. The model's skill rests on exploitability and KEV (78.9\% of the exact Shapley attribution; without them it has no skill over CVSS), and a four-parameter formula of those two inputs has a lower error than HANFIS (Sections~\ref{subsec:e8} and~\ref{subsec:e9}). On this target HANFIS therefore provides a compact rule base with a documented response surface, not better accuracy than a simple formula at the four-week horizon. The pre-registered forward evaluation (Section~\ref{subsec:e7-results}) points the same way: the accuracy of HANFIS on this task is bounded by a simple formula; its value lies in structure and interpretability. At eight and twelve weeks the gap narrows but does not close on rows unaffected by the EPSS model change, and the other inputs do not contribute (Sections~\ref{subsec:e14} and~\ref{subsec:e16}). Whether environmental context improves forecasts remains open. Two further contributions are established: the sealed, hash-verified real-world data pipeline (120 assets and 6{,}357 labelled asset-weeks, Section~\ref{subsec:target-definition}) and a completed ablation showing that the monotonicity constraint has a real, membership-family-dependent accuracy cost, met in practice only for the dominant drivers (Sections~\ref{subssec4.5} and~\ref{subsec:e8}).

H1b against persistence remains unconfirmed, and the forward weeks did not support it either (P7a). The bottleneck-width sweep (Section~\ref{subssec4.4}) found that widening the scalar inter-tier bottleneck from $k{=}1$ to $k{=}2$ does not close the gap to persistence; the wider model is significantly worse than persistence. Re-scanning every image with a single frozen vulnerability database, so that no image's CVE surface differs merely because it was scanned on a different day, was done once for the forward evaluation (Section~\ref{subsec:e7-results}); the earlier 57-week window still rests on scans from different days. The policy-translation layer (not a contribution of this paper) and edge deployment (originally hypothesis H5, now future work because the present testbed runs HANFIS cluster-side rather than on its edge node) remain designed but unevaluated. Both are left for a subsequent study.
```

## Limitations

```latex
\subsection{Limitations}
Two limits of construct validity come first. First, the label and two of the inputs share ingredients: $x_2$ (EPSS $\times\,\rho$) and $x_7$ (the KEV indicator) are the values at $t$ of quantities that the label aggregates over $t{+}7,\dots,t{+}28$, and runtime reachability $\rho$ enters both. The task is therefore to forecast the near future of exploitability signals that the model can already see, not to predict independent compromise outcomes, for which no ground truth exists here. The persistence baseline, built in the same way, is the relevant bar, and the comparison with a single CVSS score should be read in that light. The exact Shapley attribution (Section~\ref{subsec:e8}) and the ablation without these two inputs (Section~\ref{subsec:e9}) show how heavily the model's skill rests on them. Second, the dynamic character of the score comes from the time-varying EPSS and KEV feeds and from runtime reachability. Runtime telemetry (CPU, memory, latency) is used only to quantify observability overhead and is not a model input, so ``dynamic'' must not be read as telemetry-driven scoring. The rule-level attribution is faithful on average but not uniformly (Section~\ref{sec:e6}), and we do not claim validated explanations.

\label{subsec5.1}

All analyses labelled post hoc were designed after the confirmatory results and run on the same data; they are descriptive, carry no multiplicity correction, and none of them changes a registered decision.

The inventory consists of public container images and a small number of testbed assets built from a public base image, and the label reflects exploitation signals of public vulnerabilities (EPSS, KEV), not incidents in a specific organisation; generalisation to other workloads or to incident-based outcomes is untested.

Three data-related caveats are detailed in Supplementary note S7 of Additional file~1. On the 120-asset inventory (6{,}357 labelled rows; Table~\ref{tab:e3-baselines}), a linear ridge model over all seven inputs underperforms persistence on every one of the five grouped-temporal folds ($\mathrm{SS}_{\mathrm{pers}}=-2.293$ pooled, raw scale), and we did not test why. The EPSS scoring model changed version (\texttt{v2025.03.14} to \texttt{v2026.06.15}) inside the sealed 57-week window, a threat to label comparability; a post hoc re-analysis restricted to weeks whose labels all pre-date the change leaves the confirmatory conclusions unchanged (Section~\ref{subssec4.5}). The data-sufficiency gate (at least ten observations per parameter) is met by the pooled sample ($6{,}357$ labelled rows against 176 parameters) but not by the two earliest held-out folds ($2.2$ and $7.1$ observations per parameter), which are also those in which HANFIS is furthest behind persistence; H2's pooled margin is dominated by the first fold (Section~\ref{subssec4.5}).

CVEs lacking a Trivy-reported publication date are dated by their first appearance in a sealed EPSS snapshot (at most 7 days late), and a single CVE whose Trivy status lies outside the accepted set makes the whole asset-week unusable; this affected one of the 120 images for seven consecutive weeks from 2026-08-10, and such rows are removed. Labels whose four-week window straddles the EPSS model change of 2026-06-15 (and the persistence labels derived from them) mix two score definitions; these rows (18\% of the out-of-fold rows) hold 77\% of the squared error of persistence and of the formula, and the forward evaluation avoids them. The label aggregation rule, its numeric scale and the definition of Patch Risk were closed and pre-registered as amendment A-13 before the confirmatory comparison in Table~\ref{tab:e4-results} was run.

The testbed is a
single two-node WSL~2/Docker Desktop Kubernetes cluster; external validity to production multi-node
clusters and other CNI/storage stacks is untested. Ten paired observability runs, while showing large
and consistent effects, still provide limited power for null-hypothesis testing on the latency measure
specifically, which is why the reported confidence intervals rather than a significance threshold carry
the interpretive weight in Section~\ref{subsec4.1}.
```


---
Dokumen ini disusun dengan bantuan asisten AI (Claude, Anthropic) dari berkas repositori dan keluaran terminal sesi kerja 2 sampai 3 November 2026. Angka dan kutipan naskah diambil langsung dari berkas; pertimbangan ditandai sebagai pertimbangan.

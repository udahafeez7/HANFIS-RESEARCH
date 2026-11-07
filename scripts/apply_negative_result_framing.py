import sys, hashlib
src, dst = sys.argv[1], sys.argv[2]
t = open(src, encoding='utf-8').read()
pairs = []

# ---- Abstract opening
pairs.append((
r"""while a flat Adaptive Neuro-Fuzzy Inference System (ANFIS) over seven risk inputs requires 128 rules and 1{,}052 parameters. We propose a hierarchical ANFIS (HANFIS) that separates vulnerability and environmental reasoning before an integration tier adds threat intelligence, reducing the model to 34 rules and 176 parameters (73.4\% and 83.3\% fewer). We build""",
r"""while a flat Adaptive Neuro-Fuzzy Inference System (ANFIS) over seven risk inputs requires 128 rules and 1{,}052 parameters. We built a hierarchical ANFIS (HANFIS) that separates vulnerability and environmental reasoning before an integration tier adds threat intelligence, reducing the model to 34 rules and 176 parameters (73.4\% and 83.3\% fewer), and we tested whether it earns that complexity against simple baselines. We build"""))

# ---- Abstract ending
pairs.append((
r"""In a pre-registered forward evaluation, the formula beat persistence and HANFIS did not beat the formula. The data cannot show whether environmental context helps.}""",
r"""In a pre-registered forward evaluation, the formula beat persistence and HANFIS did not beat the formula. On this target HANFIS adds a printable rule base but no accuracy, and the data cannot show whether environmental context helps.}"""))

# ---- Introduction: study sentence
pairs.append((
r"""This study proposes a domain-informed Hierarchical Adaptive Neuro-Fuzzy Inference System (HANFIS).""",
r"""This study builds and tests a domain-informed Hierarchical Adaptive Neuro-Fuzzy Inference System (HANFIS)."""))

# ---- Introduction: aim paragraph
pairs.append((
r"""The aim of this study is to design, implement, and evaluate a HANFIS with a reduced rule base and intermediate variables designed to be interpretable, to test how faithful its rule-level explanations are (Section~\ref{sec:e6}), and to determine whether domain-informed hierarchical decomposition can preserve or improve risk-estimation performance while substantially reducing the rule base and parameter count of a flat ANFIS, for dynamic cybersecurity risk assessment in cloud-native environments. Policy support and edge execution are designed but left to future work.""",
r"""The aim of this study is to find out whether a domain-informed hierarchical decomposition earns its place in cloud-native vulnerability risk scoring. We build a HANFIS with a reduced rule base and intermediate variables designed to be interpretable, test how faithful its rule-level explanations are (Section~\ref{sec:e6}), and ask whether it preserves or improves estimation error relative to a flat ANFIS and, more demandingly, relative to two baselines that need no neuro-fuzzy training: a 4-week persistence forecast and a formula of two inputs. On the realised exploitability-exposure target the answer is mostly negative. The label is dominated by its own recent history, HANFIS is not distinguishable from persistence, and a four-parameter formula beats it in a pre-registered forward window. The paper reports that result together with the frozen protocol, the post hoc analyses that explain it, and the limits of what the data can show. Policy support and edge execution are designed but left to future work."""))

# ---- Contributions: lead-in and C5
pairs.append((
r"""The principal contributions of this study are stated as follows:""",
r"""The contributions of this study are:"""))
pairs.append((
r"""A Fuzzyfortify comparison is not claimed (Section~\ref{subssec4.3}).
\end{enumerate}""",
r"""A Fuzzyfortify comparison is not claimed (Section~\ref{subssec4.3}).
    \item[\textbf{C5.}] A pre-registered negative result for the hierarchical model on this target. Persistence alone removes 97\% of the error relative to climatology, so a model trained on a label of this kind has to be judged against it. In the forward window HANFIS was not better than persistence and was worse than a four-parameter formula (Section~\ref{subsec:e7-results}), and its skill rests on two inputs that are also ingredients of the label (Sections~\ref{subsec:e8} and~\ref{subsec:e9}). The result concerns one architecture, one target and one six-week window, and it is not a verdict on neuro-fuzzy models in general.
\end{enumerate}"""))

# ---- Conclusion paragraph 1
pairs.append((
r"""This paper proposes HANFIS, a domain-informed hierarchical ANFIS. It reduces a 128-rule, 1{,}052-parameter flat Sugeno system over seven cloud-native risk inputs to 34 rules and 176 parameters (Section~\ref{subsec:hanfis-architecture}) by separating vulnerability and environmental reasoning into two first-tier panels before an integration tier combines them with dynamic threat intelligence. Under a protocol frozen and dated before training began (Table~\ref{tab:e4-results}), HANFIS confirms""",
r"""This paper asked whether a domain-informed hierarchical ANFIS earns its complexity when scoring the near-term exploitability exposure of container images. On this target it does not. HANFIS reduces a 128-rule, 1{,}052-parameter flat Sugeno system over seven cloud-native risk inputs to 34 rules and 176 parameters (Section~\ref{subsec:hanfis-architecture}) by separating vulnerability and environmental reasoning into two first-tier panels before an integration tier combines them with dynamic threat intelligence. Under a protocol frozen and dated before training began (Table~\ref{tab:e4-results}), it confirms"""))
pairs.append((
r"""which the study's own mandatory baselines (Section~\ref{subssec4.3}) show to be a far harder bar than static expert scoring.""",
r"""which the study's own mandatory baselines (Section~\ref{subssec4.3}) show to be a far harder bar than static expert scoring: persistence alone removes 97\% of the error relative to climatology."""))

# ---- Conclusion: new paragraph before the "H1b against persistence" paragraph
pairs.append((
r"""H1b against persistence remains unconfirmed, and the forward weeks did not support it either (P7a).""",
r"""Three points follow for practice and for later work. For ranking near-term exploitability exposure from EPSS and KEV signals, the max-form formula, with persistence as the bar that any alternative must beat, is the choice the evidence supports (Section~\ref{sec5}). A hierarchical neuro-fuzzy model is worth building only where an auditable rule structure is required, or where an outcome that depends on the environment, such as incident or impact data, is available to test the environmental panel; the present target cannot show that benefit even if it exists. The result concerns one architecture, one label and one six-week forward window, and it does not extend to other EPSS model versions, other image sets or other neuro-fuzzy designs.

H1b against persistence remains unconfirmed, and the forward weeks did not support it either (P7a)."""))

for i,(o,n) in enumerate(pairs):
    c = t.count(o)
    if c != 1:
        sys.exit(f"FAIL pair {i}: count={c}")
    t = t.replace(o, n)
open(dst,'w',encoding='utf-8').write(t)
print("ok", len(pairs), hashlib.sha256(t.encode()).hexdigest(), len(t))

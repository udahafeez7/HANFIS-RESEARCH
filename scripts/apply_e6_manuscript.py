#!/usr/bin/env python3
"""Tambal naskah untuk hasil E6 dan penyelarasan klaim (edge, kebijakan, interpretabilitas) dengan keputusan H5/C4/H6c.
Jalankan dari akar repo. Gagal-tertutup: bila SATU jangkar tidak ditemukan tepat sekali, TIDAK ADA yang ditulis dan jangkar yang gagal dicetak. Idempoten.
Mengubah: sec. 1 (paragraf evaluasi, kerangka kebijakan, tujuan, kontribusi C4, ringkasan kontribusi) dan menyisipkan sub-bagian E6 sebelum Discussion."""
import shutil, sys
from pathlib import Path
P = Path("manuscript/sn-article.tex")
s = P.read_text(encoding="utf-8")
FRAG = r'''\subsection{Explanation fidelity (E6)}\label{sec:e6}
We tested whether the rule-level explanation that HANFIS exposes is faithful to its inference. The test uses the 25 saved models (five folds $\times$ five seeds), which reproduce the confirmatory predictions of Section~\ref{sec4} exactly (mean over the five seeds; maximum difference $1.4\times10^{-6}$ on the 0--100 scale in single precision). The hypotheses and thresholds were drafted and announced before execution; the version-control freeze, however, preceded the commit that contained the protocol text, so the protocol is not frozen in the strict sense and the run is reported as a documented deviation. Table~\ref{tab:e6} lists the outcome.

\begin{table}[ht]
\caption{Explanation-fidelity checks on the 25 saved models. Pairs are the positive-control images P0-IF with and without the active filter; $S^{+}$ denotes the 23 weeks in which exploitability differs between the two.}\label{tab:e6}
\begin{tabular}{@{}p{0.25\linewidth}p{0.29\linewidth}p{0.20\linewidth}l@{}}
\hline
Check & Criterion & Result & Outcome\\
\hline
H6-0 trace vs.\ inference & $|\Delta|\le10^{-9}$, all test rows & 0 & pass\\
H6-neg identical inputs & $|\Delta|\le10^{-9}$, 34 weeks $\times$ 25 models & 0 & pass\\
H6a direction (monotone) & $\hat y_{\mathrm{on}}-\hat y_{\mathrm{off}}\ge-10^{-9}$ on $S^{+}$ & minimum 0 & pass\\
H6b panel structure & panel E unchanged, panel V changes & $0$ and $2.9\times10^{-4}$ & pass\\
H6c deletion test & ratio $\ge2$ and proportion $\ge0.90$ & 4.11 and 0.835 & fail\\
\hline
\end{tabular}
\end{table}

Removing the three rules ranked highest by attribution changed the output 4.1 times more than removing three random rules, but it exceeded the median random removal in only 83.5\% of non-degenerate rows (criterion: 90\%); 456 of 5{,}400 rows (8.4\%) were degenerate, 446 of them because the output was clamped. Of the 575 positive-control pairs, 552 increased strictly; the remaining 23 include 20 pairs whose output is clamped at zero in both conditions. Post hoc and without bearing on the decision, the proportion reached 0.90 in two of five folds and was lowest in fold~3 (0.637), and it was lowest on the P0 and P0-IF rows (0.648, ratio 1.73, 135 rows). On the nine paired test weeks the mean ON--OFF contrast was 0.037 for the model and 0.073 for the label (0--100 scale): the direction is right and the magnitude is about half.

We therefore do not claim validated rule-level explanations. The rule trace matches the inference exactly and the direction of the response is verified, but the attribution of the output to individual rules is faithful on average rather than uniformly.'''
EDITS = [
 ("evaluasi-latensi", "and median and tail inference latency on the target edge platform.",
  "and median and tail inference latency, with edge-platform measurements left to future work."),
 ("kerangka-kebijakan", "The proposed framework therefore includes a policy-translation layer that maps validated risk states to predefined responses,",
  "The proposed framework therefore specifies a policy-translation layer, designed but not evaluated in this paper, that maps validated risk states to predefined responses,"),
 ("time-to-mitigation", "In this way, the research connects adaptive assessment to measurable time-to-mitigation while preserving accountability and operational safety.",
  "In this way, the framework is designed to connect adaptive assessment to measurable time-to-mitigation in future work, while preserving accountability and operational safety."),
 ("tujuan-1", "an interpretable and computationally efficient HANFIS for dynamic cybersecurity risk assessment and policy support in cloud-native environments.",
  "a HANFIS with a reduced rule base and intermediate variables that are interpretable by construction, for dynamic cybersecurity risk assessment in cloud-native environments."),
 ("tujuan-2", "while substantially reducing the computational burden of flat ANFIS and enabling timely inference at the edge.",
  "while substantially reducing the rule base and parameter count of a flat ANFIS; policy support and edge execution are designed but left to future work."),
 ("kontribusi-C4", "An auditable edge policy-translation mechanism that converts validated risk states into bounded response recommendations or enforcement actions with monotonicity constraints, critical-risk overrides, confidence controls, and an execution log.",
  "An auditable policy-translation mechanism (designed but not evaluated in this paper) that converts validated risk states into bounded response recommendations with monotonicity constraints, critical-risk overrides, confidence controls, and an execution log."),
 ("ringkasan-kontribusi", "from high-dimensional risk factors to computationally tractable edge execution, and from risk estimation to bounded operational response.",
  "from high-dimensional risk factors to a computationally tractable rule base, and, as designed but not yet evaluated extensions, from risk estimation to bounded operational response and to edge execution."),
]
ANCHOR = "\\section{Discussion}\\label{sec5}"
errors, todo = [], []
for name, old, new in EDITS:
    n = s.count(old)
    if n == 1: todo.append((name, old, new))
    elif n == 0 and s.count(new) == 1: print(f"sudah: {name}")
    else: errors.append(f"{name}: jangkar ditemukan {n}x (harus 1)")
insert = "\\label{sec:e6}" not in s
if insert and s.count(ANCHOR) != 1: errors.append(f"sisip-E6: jangkar Discussion ditemukan {s.count(ANCHOR)}x (harus 1)")
if errors:
    print("ABORT, tidak ada yang ditulis:"); [print("  -", e) for e in errors]; sys.exit(2)
for name, old, new in todo: s = s.replace(old, new); print(f"diterapkan: {name}")
if insert: s = s.replace(ANCHOR, FRAG + "\n\n" + ANCHOR); print("diterapkan: sub-bagian E6 (sebelum Discussion)")
if not todo and not insert: print("Sudah diterapkan seluruhnya."); sys.exit(0)
shutil.copy(P, str(P) + ".pre-e6.bak"); P.write_text(s, encoding="utf-8"); print("OK")

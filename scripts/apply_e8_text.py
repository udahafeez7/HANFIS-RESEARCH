#!/usr/bin/env python3
"""Tambal naskah untuk hasil E8 (atribusi Shapley eksak dan uji monotonisitas): (1) koreksi klaim teoretis 'r monotone ...' di Methods, (2) pelunakan kalimat auditability di Discussion dan Conclusion,
(3) satu klausa di paragraf validitas konstruk (Limitations), (4) sub-bagian baru E8 sebelum Discussion. Jangkar toleran terhadap pemotongan baris; gagal-tertutup (semua cocok tepat sekali atau
tidak ada yang ditulis); idempoten; cadangan .pre-e8.bak. Dari akar repo."""
import re, shutil, sys
from pathlib import Path
P = Path("manuscript/sn-article.tex"); s = P.read_text(encoding="utf-8")
FRAG = r'''\subsection{Attribution and monotonicity checks (E8)}\label{subsec:e8}
We computed exact interventional Shapley values for the seven inputs of the 25 saved models (5{,}400 model--row pairs; a background of 60 random labelled rows, excluding P0 and P0-IF and identical for all models; the efficiency property holds to $2\times10^{-14}$). Exploitability ($x_2$) and the KEV indicator ($x_7$), both ingredients of the label, carry 78.9\% of the mean absolute attribution; the three environment inputs ($x_4$--$x_6$) carry 3.3\% (Table~\ref{tab:e8}). The ranking is stable across models (Kendall $W=0.79$; $x_2$ is the top input in 21 of 25 models), and in the 20\% of rows with the highest label $x_7$ alone carries 63.0\%. This quantifies the overlap between label and inputs discussed in Section~\ref{sec5}: the model largely forecasts exploitability signals it can already see, and the label contains no environment component by construction.

\begin{table}[ht]
\caption{Exact Shapley attribution and within-row monotonicity checks for the five-seed ensemble (E8; descriptive and post hoc). ``Falls'' is the share of steps, over the range observed in the data, in which the score drops by more than 0.05 points when one input is raised and the others are held fixed. Share: mean absolute attribution; Max drop and Range: largest fall and mean end-to-end change of the score in points.}\label{tab:e8}
\begin{tabular}{@{}p{0.36\linewidth}rrrr@{}}
\hline
Input & Share (\%) & Falls (\%) & Max drop & Range\\
\hline
$x_1$ CVSS & 10.9 & 1.7 & 2.46 & 1.99\\
$x_2$ Exploitability & 46.4 & 1.2 & 0.21 & 6.53\\
$x_3$ Patch Risk & 6.8 & 24.8 & 2.28 & 1.11\\
$x_4$ MFA Risk & 1.1 & 29.1 & 0.46 & 0.09\\
$x_5$ Kubernetes Exposure & 1.3 & 34.8 & 0.60 & 0.14\\
$x_6$ Asset Criticality & 0.9 & 10.5 & 0.40 & 0.13\\
$x_7$ Threat Intelligence (KEV) & 32.5 & 1.2 & 0.33 & 6.45\\
\hline
\end{tabular}
\end{table}

Non-negative rule slopes do not guarantee a monotone score, because rule weights are normalised and intercepts are free. We therefore varied one input at a time over 11 points spanning the observed range (observed values for discrete inputs, quantiles from 1\% to 99\% otherwise) for the five-seed ensemble that is reported in Section~\ref{sec4}. For the dominant drivers the share of falling steps is small ($x_1$ 1.7\%, $x_2$ 1.2\%, $x_7$ 1.2\%), whereas for patch risk and the environment inputs it is 10--35\%, although the environment inputs move the score by less than 0.15 points on average (Table~\ref{tab:e8}). Individual seeds are less well behaved than the ensemble: the largest single drop (11.6 points, CVSS) occurs in one seed on two assets in the last held-out block, after the EPSS model change. We therefore present monotonicity as an empirical property of the dominant inputs, not as a guarantee of the architecture.'''
EDITS = [
 ("methods-monotone", r"so\s+that\s+\$r\$\s+is\s+monotone\s+non-decreasing\s+in\s+every\s+input\s+under\s+the\s+stated\s+higher-is-riskier\s+convention;\s+intercepts\s+stay\s+free\.",
  r"so that each rule's consequent is non-decreasing in every input under the stated higher-is-riskier convention; intercepts stay free and rule weights are normalised, so $r$ itself is not guaranteed to be monotone, and monotonicity is therefore checked empirically (Section~\ref{subsec:e8})."),
 ("discussion-trade", r"a\s+deliberate\s+trade\s+of\s+some\s+accuracy\s+for\s+interpretability\s+and\s+auditability,\s+not\s+a\s+default\s+that\s+happened\s+to\s+be\s+convenient\.",
  r"a deliberate trade of some accuracy for a response that, for the dominant risk factors, rarely falls as they rise (Section~\ref{subsec:e8}), not a default that happened to be convenient."),
 ("conclusion-required", r"monotonicity\s+constraint\s+required\s+for\s+an\s+auditable,\s+higher-is-riskier\s+score\s+has\s+a\s+real,",
  r"monotonicity constraint intended to keep the score from falling as risk factors rise (met in practice only for the dominant drivers; Section~\ref{subsec:e8}) has a real,"),
 ("limitations-shapley", r"should\s+be\s+read\s+in\s+that\s+light\.", r"should be read in that light; exact Shapley attribution (Section~\ref{subsec:e8}) places 78.9\% of the model's attribution on these two inputs and 3.3\% on the environment inputs."),
]
ANCHOR = "\\section{Discussion}\\label{sec5}"
errors, plan = [], []
for name, pat, new in EDITS:
    m = list(re.finditer(pat, s))
    if len(m) == 1: plan.append((m[0], new, name))
    elif len(m) == 0 and new[:60] in s: print(f"sudah: {name}")
    else: errors.append(f"{name}: jangkar ditemukan {len(m)}x (harus 1)")
insert = "\\label{subsec:e8}" not in s
if insert and s.count(ANCHOR) != 1: errors.append(f"sisip-E8: jangkar Discussion ditemukan {s.count(ANCHOR)}x (harus 1)")
if errors:
    print("ABORT, tidak ada yang ditulis:"); [print("  -", e) for e in errors]; sys.exit(2)
if not plan and not insert: print("Sudah diterapkan seluruhnya."); sys.exit(0)
for m, new, name in sorted(plan, key=lambda t: -t[0].start()): s = s[:m.start()] + new + s[m.end():]; print(f"diterapkan: {name}")
if insert: s = s.replace(ANCHOR, FRAG + "\n\n" + ANCHOR); print("diterapkan: sub-bagian E8 (sebelum Discussion)")
shutil.copy(P, str(P) + ".pre-e8.bak"); P.write_text(s, encoding="utf-8"); print("OK")

#!/usr/bin/env python3
"""Tambal naskah untuk E15 (utilitas prioritisasi): sub-bagian baru 'Prioritisation utility (E15)' (label subsec:e15; tabel tab:e15 dan tab:e15d) sebelum Discussion, setelah sub-bagian E14, dan satu klausa di kalimat Discussion
('What the data support'). Angka dari keluaran e15_ranking.py (2026-10-12). Jangkar inti wajib tepat sekali; klausa Discussion opsional dan dilaporkan bila dilewati. Idempoten; cadangan .pre-e15.bak. Dari akar repo."""
import re, shutil, sys
from pathlib import Path
P = Path("manuscript/sn-article.tex"); s = P.read_text(encoding="utf-8")
flex = lambda t: r"\s+".join(map(re.escape, t.split()))
SUB = r'''\subsection{Prioritisation utility (E15)}\label{subsec:e15}
Risk scores are used to rank assets, so we also compared the predictors on ranking within each week rather than on squared error. For every week with at least 15 assets we computed the Spearman correlation between the predicted score and the realised label and the precision at the top 20\% (the share of the 20\% of assets with the highest predicted score that are also among the 20\% with the highest realised label), and averaged over weeks. Differences between predictors are paired by week, with 95\% intervals from a bootstrap that resamples weeks, a more conservative unit than images. This analysis is post hoc and uses the out-of-fold predictions at the three horizons.

All predictors rank assets almost identically (Table~\ref{tab:e15}). At four weeks the weekly Spearman correlation is $0.99$ for the formula and for persistence and $0.97$ for HANFIS, and the precision at the top 20\% is $0.97$ for all three, so the lower squared error of the formula does not translate into a practical gain in prioritisation (Table~\ref{tab:e15d}: Spearman $+0.002$ and precision $0.000$ against persistence). At eight and twelve weeks persistence ranks somewhat worse (precision $0.94$ and $0.88$) and both HANFIS and the formula improve on it in precision ($+0.016$ and $+0.041$ for the formula, $+0.016$ and $+0.069$ for HANFIS); at twelve weeks HANFIS identifies the top 20\% better than the formula ($+0.028$, interval $[0.007,\,0.055]$) although its Spearman correlation is lower ($-0.024$). Differences in Spearman correlation never exceed $0.03$ and the precision is close to its ceiling, so all these differences should be read as small; with eighteen paired comparisons and no correction for multiplicity, the intervals are descriptive.

\begin{table}[ht]
\caption{Weekly ranking utility (E15, post hoc): mean over weeks of the Spearman correlation between predicted score and realised label, and precision at the top 20\%.}\label{tab:e15}
\small
\begin{tabular}{@{}p{0.40\linewidth}rrr@{}}
\hline
Horizon and metric & Formula & HANFIS & Persistence\\
\hline
4 weeks (45 weeks): Spearman & 0.994 & 0.969 & 0.992\\
4 weeks: precision at top 20\% & 0.969 & 0.973 & 0.969\\
8 weeks (37 weeks): Spearman & 0.989 & 0.963 & 0.982\\
8 weeks: precision at top 20\% & 0.957 & 0.957 & 0.941\\
12 weeks (29 weeks): Spearman & 0.974 & 0.951 & 0.964\\
12 weeks: precision at top 20\% & 0.924 & 0.952 & 0.883\\
\hline
\end{tabular}
\end{table}

\begin{table}[ht]
\caption{Paired weekly differences in ranking utility (E15, post hoc); 95\% week-bootstrap intervals in brackets.}\label{tab:e15d}
\footnotesize
\begin{tabular}{@{}p{0.30\linewidth}rr@{}}
\hline
Comparison & $\Delta$ Spearman & $\Delta$ precision at top 20\%\\
\hline
4 w: formula $-$ persistence & $+0.002$ $[0.001,\,0.004]$ & $0.000$ $[-0.013,\,0.013]$\\
4 w: HANFIS $-$ persistence & $-0.023$ $[-0.027,\,-0.018]$ & $+0.004$ $[-0.009,\,0.018]$\\
4 w: formula $-$ HANFIS & $+0.025$ $[0.021,\,0.029]$ & $-0.004$ $[-0.013,\,0.000]$\\
8 w: formula $-$ persistence & $+0.007$ $[0.004,\,0.012]$ & $+0.016$ $[0.000,\,0.032]$\\
8 w: HANFIS $-$ persistence & $-0.018$ $[-0.026,\,-0.011]$ & $+0.016$ $[0.000,\,0.032]$\\
8 w: formula $-$ HANFIS & $+0.026$ $[0.020,\,0.031]$ & $0.000$ $[0.000,\,0.000]$\\
12 w: formula $-$ persistence & $+0.010$ $[0.005,\,0.017]$ & $+0.041$ $[0.014,\,0.076]$\\
12 w: HANFIS $-$ persistence & $-0.013$ $[-0.025,\,-0.002]$ & $+0.069$ $[0.034,\,0.103]$\\
12 w: formula $-$ HANFIS & $+0.024$ $[0.017,\,0.032]$ & $-0.028$ $[-0.055,\,-0.007]$\\
\hline
\end{tabular}
\end{table}'''
ANCHOR = "\\section{Discussion}\\label{sec5}"
DISC_OLD = "Section~\\ref{subsec:e14}); the data do not support the claim"
DISC_NEW = "Section~\\ref{subsec:e14}); the ranking of assets by predicted risk is almost the same for all predictors at four weeks (Section~\\ref{subsec:e15}); the data do not support the claim"
errors, edits, skipped = [], [], []
if "\\label{subsec:e15}" in s: print("sudah: sub-bagian E15")
elif s.count(ANCHOR) == 1: edits.append((s.index(ANCHOR), s.index(ANCHOR), SUB + "\n\n"))
else: errors.append(f"jangkar Discussion ditemukan {s.count(ANCHOR)}x (harus 1)")
if "almost the same for all predictors at four weeks" in s: print("sudah: Discussion")
else:
    m = list(re.finditer(flex(DISC_OLD), s))
    if len(m) == 1: edits.append((m[0].start(), m[0].end(), DISC_NEW))
    else: skipped.append(f"klausa Discussion ({len(m)}x)")
if errors: print("ABORT, tidak ada yang ditulis:"); [print("  -", e) for e in errors]; sys.exit(2)
if not edits: print("Sudah diterapkan seluruhnya."); sys.exit(0)
for st, en, new in sorted(edits, key=lambda t: -t[0]): s = s[:st] + new + s[en:]
shutil.copy(P, str(P) + ".pre-e15.bak"); P.write_text(s, encoding="utf-8"); print(f"OK: {len(edits)} perubahan")
for k in skipped: print("  DILEWATI (periksa manual):", k)

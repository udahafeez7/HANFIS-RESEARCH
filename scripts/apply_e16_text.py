#!/usr/bin/env python3
"""Tambal naskah untuk anatomi galat (E16 sampai E19 dan kontrol E14c pada baris bersih): sub-bagian 'Error anatomy and the EPSS model change (E16--E19)' (label subsec:e16; tabel tab:e16, tab:e19) sebelum Discussion (setelah E15),
dan kualifikasi klaim yang kini terlalu kuat: abstrak ('gap closes' menjadi 'narrows ... only through weeks around a change of the EPSS model'; 'matches' menjadi 'does not demonstrably exceed, and at the four-week horizon falls behind'), Discussion, Conclusion;
opsional: satu kalimat di sub-bagian E14 dan di Limitations. Jangkar inti wajib tepat sekali (gagal-tertutup); opsional dilaporkan bila dilewati. Idempoten; cadangan .pre-e16.bak. Dari akar repo."""
import re, shutil, sys
from pathlib import Path
P = Path("manuscript/sn-article.tex"); s = P.read_text(encoding="utf-8")
flex = lambda t: r"\s+".join(map(re.escape, t.split()))
SUB = r'''\subsection{Error anatomy and the EPSS model change (E16--E19)}\label{subsec:e16}
The preceding sections compare pooled errors. To see where the differences come from, we analysed the four-week out-of-fold predictions by stratum, by time block and by distance to the change of the EPSS model on 2026-06-15 (post hoc, with a bootstrap clustered by image).

\emph{Reactivity.} The advantage of the formula over persistence is concentrated in rows in which an input changed during the previous four weeks (EPSS exploitability or KEV status; 628 of 1{,}080 rows). Its skill is $0.400$ (interval $0.308$ to $0.487$) in these rows and $0.002$ ($-0.069$ to $0.037$) where nothing changed, so it behaves like persistence when nothing happens (Table~\ref{tab:e16}); a gate that returns persistence in unchanged rows leaves it unchanged. HANFIS has skill $0.125$ in changed rows and $-0.900$ ($-4.171$ to $-0.206$) in unchanged rows: it adds noise where persistence is already adequate. A gate removes this deficit (improvement $0.098$, interval $0.033$ to $0.204$) but leaves HANFIS no better than persistence ($0.111$, $-0.367$ to $0.292$) and worse than the formula ($-0.383$, $-0.998$ to $-0.131$). Since the flag counts any change of the score, most flagged changes are small.

Squared error is extremely concentrated: the worst 5\% of rows hold 91\% (persistence), 95\% (formula) and 67\% (HANFIS) of the total, and the five worst images 68\%, 63\% and 39\%. Leaving out each of the five time blocks in turn leaves the skill of the formula against persistence between $0.34$ and $0.43$, with intervals above zero, although one block (April to June 2026) carries 73\% of the absolute reduction in error; HANFIS is worse than the formula in every such estimate.

\emph{The model change.} The largest errors are not KEV events (the KEV indicator is zero in all twelve worst rows of every predictor) but small shifts of the score, with labels between 3.7 and 10 points on a 100-point scale, in the weeks 2026-W21 to W24. The four-week label windows of these weeks straddle the change of the EPSS model: $x_2$ is computed with the old model while the label, and the label of the persistence forecast, use the new one, and all three predictors err almost equally there. Rows within the label window of the change (190 of 1{,}080 at four weeks) hold 77\% of the squared error of persistence and of the formula and 49\% of that of HANFIS. On the remaining rows (Table~\ref{tab:e19}) the formula keeps its point estimate of skill against persistence ($0.348$ against $0.357$) but the interval now includes zero ($-0.060$ to $0.422$), and HANFIS is significantly worse than persistence ($-1.228$) and than the formula ($-2.418$). The forward evaluation described above is free of this change: its test weeks start on 2026-08-31 and its persistence labels come from weeks after 2026-08-03.

\emph{Horizon, revisited.} The narrowing of the gap between HANFIS and the formula at eight and twelve weeks (Section~\ref{subsec:e14}) must be read in this light. Excluding the affected rows, HANFIS stays behind the formula at eight and twelve weeks ($-0.324$ and $-0.362$, intervals including zero). On the 169 asset-weeks that are common to the three horizons and unaffected at all of them, the skill of HANFIS against the formula still rises with the horizon ($-15.4$, $-1.1$ and $-0.5$; change between four and twelve weeks $+14.9$, interval $6.1$ to $53.7$) but stays significantly negative at every horizon ($-0.515$, interval $-2.117$ to $-0.092$, at twelve weeks). The horizon sweep therefore shows a shrinking deficit, not parity; the sample of unaffected rows is small and the intervals are wide.

\begin{table}[ht]
\caption{Input-change strata at four weeks (E16, post hoc): rows, mean squared error (persistence / formula / HANFIS), and skill against persistence with 95\% intervals.}\label{tab:e16}
\footnotesize
\setlength{\tabcolsep}{3pt}
\begin{tabular}{@{}p{0.17\linewidth}rp{0.19\linewidth}p{0.22\linewidth}p{0.23\linewidth}@{}}
\hline
Stratum & Rows & MSE & Skill, formula & Skill, HANFIS\\
\hline
Input changed & 628 & 0.637 / 0.382 / 0.557 & $0.400$ $[0.308,\,0.487]$ & $0.125$ $[-0.402,\,0.333]$\\
No input change & 452 & 0.107 / 0.106 / 0.202 & $0.002$ $[-0.069,\,0.037]$ & $-0.900$ $[-4.171,\,-0.206]$\\
\hline
\end{tabular}
\end{table}

\begin{table}[ht]
\caption{Skill on all out-of-fold rows and on rows unaffected by the EPSS model change (E19, post hoc), with 95\% image-bootstrap intervals from a separate run (they differ slightly from Table~\ref{tab:e14}). Unaffected rows: 890 of 1{,}080 (four weeks), 536 of 889 (eight) and 342 of 697 (twelve).}\label{tab:e19}
\footnotesize
\setlength{\tabcolsep}{3pt}
\begin{tabular}{@{}p{0.32\linewidth}p{0.29\linewidth}p{0.29\linewidth}@{}}
\hline
Comparison & All rows & Unaffected rows\\
\hline
4 w: formula vs.\ persistence & $0.357$ $[0.279,\,0.407]$ & $0.348$ $[-0.060,\,0.422]$\\
4 w: HANFIS vs.\ persistence & $0.015$ $[-0.627,\,0.252]$ & $-1.228$ $[-12.804,\,-0.015]$\\
4 w: HANFIS vs.\ formula & $-0.534$ $[-1.383,\,-0.204]$ & $-2.418$ $[-13.204,\,-0.709]$\\
8 w: formula vs.\ persistence & $0.492$ $[0.269,\,0.696]$ & $0.623$ $[-0.009,\,0.699]$\\
8 w: HANFIS vs.\ persistence & $0.467$ $[0.241,\,0.670]$ & $0.501$ $[-1.631,\,0.702]$\\
8 w: HANFIS vs.\ formula & $-0.048$ $[-0.200,\,0.036]$ & $-0.324$ $[-2.153,\,0.052]$\\
12 w: formula vs.\ persistence & $0.440$ $[0.245,\,0.597]$ & $0.824$ $[0.270,\,0.913]$\\
12 w: HANFIS vs.\ persistence & $0.462$ $[0.269,\,0.614]$ & $0.761$ $[-0.220,\,0.888]$\\
12 w: HANFIS vs.\ formula & $0.039$ $[-0.034,\,0.106]$ & $-0.362$ $[-1.342,\,0.018]$\\
\hline
\end{tabular}
\end{table}'''
ANCHOR = "\\section{Discussion}\\label{sec5}"
ABS_OLD = r"(skill $-0.53$, 95\% interval $-1.44$ to $-0.21$), a gap that closes at eight and twelve weeks without the other inputs contributing. HANFIS is therefore a compact rule base that matches, but does not demonstrably exceed, a simple formula,"
ABS_NEW = r"(skill $-0.53$, interval $-1.44$ to $-0.21$); the gap narrows at longer horizons only through weeks around an EPSS model change. HANFIS is therefore a compact rule base that does not demonstrably exceed, and at the four-week horizon falls behind, a simple formula,"
DISC_OLD = "(at eight and twelve weeks the gap to the formula closes, Section~\\ref{subsec:e14})"
DISC_NEW = "(at eight and twelve weeks the gap to the formula narrows, but only through weeks around the EPSS model change, Sections~\\ref{subsec:e14} and~\\ref{subsec:e16})"
CONC_OLD = "(at eight and twelve weeks it matches the formula without demonstrably exceeding it, and without the other inputs contributing; Section~\\ref{subsec:e14})"
CONC_NEW = "(at eight and twelve weeks the gap narrows but does not close on rows unaffected by the EPSS model change, and the other inputs do not contribute; Sections~\\ref{subsec:e14} and~\\ref{subsec:e16})"
E14_OLD = "The relative gain of HANFIS at longer horizons therefore comes from a better functional form of the same two inputs, not from the other inputs."
E14_NEW = "The relative gain of HANFIS at longer horizons does not come from the other inputs; Section~\\ref{subsec:e16} shows that it is largely due to weeks around the EPSS model change and that on unaffected rows HANFIS remains behind the formula."
LIM_OLD = "and removes such rows from the analysis."
LIM_NEW = ("and removes such rows from the analysis. Labels whose four-week window straddles the EPSS model change of 2026-06-15 (and the persistence labels derived from them) mix two score definitions; these rows (18\\% of the out-of-fold rows) "
           "hold 77\\% of the squared error of persistence and of the formula, and the forward evaluation avoids them.")
errors, edits, skipped = [], [], []
def core(old, new, name, rx=False):
    m = list(re.finditer(old if rx else flex(old), s))
    if len(m) == 1: edits.append((m[0].start(), m[0].end(), new))
    else: errors.append(f"{name}: jangkar ditemukan {len(m)}x (harus 1)")
def opt(old, new, name):
    m = list(re.finditer(flex(old), s))
    if len(m) == 1: edits.append((m[0].start(), m[0].end(), new))
    else: skipped.append(f"{name} ({len(m)}x)")
if "\\label{subsec:e16}" in s: print("sudah: sub-bagian E16")
elif s.count(ANCHOR) == 1: edits.append((s.index(ANCHOR), s.index(ANCHOR), SUB + "\n\n"))
else: errors.append(f"jangkar Discussion ditemukan {s.count(ANCHOR)}x (harus 1)")
if "narrows at longer horizons only through weeks" in s: print("sudah: abstrak")
else: core(ABS_OLD, ABS_NEW, "abstrak")
if "the gap to the formula narrows, but only through" in s: print("sudah: Discussion")
else: core(DISC_OLD, DISC_NEW, "Discussion")
if "the gap narrows but does not close on rows unaffected" in s: print("sudah: Conclusion")
else: core(CONC_OLD, CONC_NEW, "Conclusion")
if "largely due to weeks around the EPSS model change" in s: print("sudah: E14")
else: opt(E14_OLD, E14_NEW, "kalimat E14")
if "mix two score definitions" in s: print("sudah: Limitations")
else: opt(LIM_OLD, LIM_NEW, "kalimat Limitations")
if errors: print("ABORT, tidak ada yang ditulis:"); [print("  -", e) for e in errors]; sys.exit(2)
if not edits: print("Sudah diterapkan seluruhnya."); sys.exit(0)
for st, en, new in sorted(edits, key=lambda t: -t[0]): s = s[:st] + new + s[en:]
shutil.copy(P, str(P) + ".pre-e16.bak"); P.write_text(s, encoding="utf-8"); print(f"OK: {len(edits)} perubahan")
for k in skipped: print("  DILEWATI (periksa manual):", k)
m = re.search(r"\\abstract\{(.*?)\}\n", s, re.S)
if m: print("palavras do resumo (aprox.):", len(re.sub(r"\\%|\$[^$]*\$|\{,\}|\\", " ", m.group(1)).split()))

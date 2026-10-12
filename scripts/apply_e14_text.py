#!/usr/bin/env python3
"""Tambal naskah untuk E14 (sapuan horizon 4, 8, 12 minggu; kontrol minggu-sama; dampak fitur per horizon). Menambah sub-bagian baru (label subsec:e14, tabel tab:e14) sebelum Discussion dan mengkualifikasi klaim yang kini terlalu umum:
abstrak (ekor post hoc diganti dan dipadatkan agar tetap sekitar 250 kata), Discussion ('lowest error ... at the four-week horizon'), Conclusion, dan C5. Jangkar inti wajib tepat sekali (gagal-tertutup); pemadatan abstrak opsional dan dilaporkan bila dilewati.
Idempoten; cadangan .pre-e14.bak.  Dari akar repo."""
import re, shutil, sys
from pathlib import Path
P = Path("manuscript/sn-article.tex"); s = P.read_text(encoding="utf-8")
flex = lambda t: r"\s+".join(map(re.escape, t.split()))
SUB = r'''\subsection{Horizon sweep and feature impact by horizon (E14)}\label{subsec:e14}
All preceding analyses use the four-week label window of the confirmatory protocol. To check whether the conclusions depend on that horizon, we rebuilt the dataset with label windows of 58 and 86 days (eight and twelve weekly snapshots after $t$), set the persistence lag and the embargo to the window length (8 and 12 weeks; 58 and 86 days) to avoid leakage, and repeated the out-of-fold comparison of HANFIS, the max-form formula and persistence with the same folds, seeds and hyperparameters. Longer windows leave fewer labelled weeks (the last labelled week is 2026-07-27 and 2026-06-29), so the out-of-fold samples shrink to 889 and 697 rows, and mean squared errors at different horizons are not comparable because the labels average different numbers of snapshots; only skill scores are compared. This analysis is post hoc.

The formula's advantage over persistence is stable (skill $0.36$, $0.49$ and $0.44$ at four, eight and twelve weeks), whereas the gap between HANFIS and the formula closes: $-0.534$ (interval $[-1.438,\,-0.208]$) at four weeks, $-0.048$ ($[-0.205,\,0.032]$) at eight and $0.039$ ($[-0.031,\,0.110]$) at twelve. HANFIS beats persistence from eight weeks on ($0.467$ and $0.462$, intervals above zero). Because the longer horizons only contain older weeks (the EPSS model changed on 2026-06-15), horizon and period are confounded. Restricting all three horizons to the 408 asset-weeks present in each, the pattern remains: the skill of HANFIS against the formula changes by $+0.862$ ($[+0.309,\,+2.973]$) between four and twelve weeks, while the skill of the formula against persistence does not change ($-0.016$, $[-0.096,\,+0.141]$).

Removing exploitability and the KEV indicator again removes all skill at eight and twelve weeks (skill against CVSS alone $-0.099$ and $-0.179$, intervals including or touching zero; against HANFIS with all inputs $-24.0$ and $-14.6$), and a ridge model on the remaining five inputs is not better than CVSS alone ($-0.069$ and $-0.071$). The relative gain of HANFIS at longer horizons therefore comes from a better functional form of the same two inputs, not from the other inputs. The evidence is suggestive, not conclusive: at twelve weeks HANFIS and the formula are not distinguishable, cross-fitted blends of the two do not improve on either alone, and the forward evaluation planned for the confirmatory protocol covers only the four-week horizon.

\begin{table}[ht]
\caption{Horizon sweep (E14, post hoc). Skill score with 95\% image-clustered bootstrap interval. Panel A: all out-of-fold rows; B: the 408 asset-weeks present at all three horizons; C: HANFIS retrained without $x_2$ and $x_7$ against CVSS only.}\label{tab:e14}
\small
\begin{tabular}{@{}p{0.47\linewidth}rrr@{}}
\hline
Comparison & Skill & 95\% interval & Rows\\
\hline
\multicolumn{4}{@{}l}{\emph{A. All out-of-fold rows}}\\
4 weeks: formula vs.\ persistence & $0.357$ & $[0.279,\,0.407]$ & 1{,}080\\
4 weeks: HANFIS vs.\ persistence & $0.015$ & $[-0.620,\,0.243]$ & 1{,}080\\
4 weeks: HANFIS vs.\ formula & $-0.534$ & $[-1.438,\,-0.208]$ & 1{,}080\\
8 weeks: formula vs.\ persistence & $0.492$ & $[0.269,\,0.696]$ & 889\\
8 weeks: HANFIS vs.\ persistence & $0.467$ & $[0.236,\,0.651]$ & 889\\
8 weeks: HANFIS vs.\ formula & $-0.048$ & $[-0.205,\,0.032]$ & 889\\
12 weeks: formula vs.\ persistence & $0.440$ & $[0.245,\,0.597]$ & 697\\
12 weeks: HANFIS vs.\ persistence & $0.462$ & $[0.277,\,0.610]$ & 697\\
12 weeks: HANFIS vs.\ formula & $0.039$ & $[-0.031,\,0.110]$ & 697\\
\multicolumn{4}{@{}l}{\emph{B. Same 408 asset-weeks at every horizon}}\\
4 weeks: HANFIS vs.\ formula & $-0.812$ & $[-2.952,\,-0.264]$ & 408\\
8 weeks: HANFIS vs.\ formula & $-0.045$ & $[-0.218,\,0.038]$ & 408\\
12 weeks: HANFIS vs.\ formula & $0.050$ & $[-0.060,\,0.158]$ & 408\\
Change 12 minus 4 weeks: HANFIS vs.\ formula & $0.862$ & $[0.309,\,2.973]$ & 408\\
Change 12 minus 4 weeks: formula vs.\ persistence & $-0.016$ & $[-0.096,\,0.141]$ & 408\\
\multicolumn{4}{@{}l}{\emph{C. HANFIS without $x_2$, $x_7$ vs.\ CVSS only}}\\
4 weeks & $-0.135$ & $[-0.336,\,0.046]$ & 1{,}080\\
8 weeks & $-0.099$ & $[-0.289,\,0.069]$ & 889\\
12 weeks & $-0.179$ & $[-0.406,\,0.007]$ & 697\\
\hline
\end{tabular}
\end{table}'''
ANCHOR = "\\section{Discussion}\\label{sec5}"
TAIL_RX = r"and a four-parameter formula of those two inputs, \$100\\max\(x_2,0\.1\\,x_7\)\$, has a lower error than HANFIS \(0\.27 versus 0\.41; skill \$-0\.53\$, interval \$-1\.44\$ to \$-0\.21\$\)\.\s+On this target HANFIS is therefore a compact rule base, not a more accurate predictor than a simple formula, and the data cannot show whether environmental context improves forecasts\."
TAIL_NEW = (r"and a four-parameter formula of those two inputs, $100\max(x_2,0.1\,x_7)$, has a lower error than HANFIS at a four-week horizon (skill $-0.53$, 95\% interval $-1.44$ to $-0.21$), a gap that closes at eight and twelve weeks without the other inputs contributing. "
            r"HANFIS is therefore a compact rule base that matches, but does not demonstrably exceed, a simple formula, and the data cannot show whether environmental context improves forecasts.")
SHORT = [("We construct a temporal exploitability-exposure target from sealed weekly EPSS and CISA KEV snapshots for a digest-pinned inventory of 120 container images (6{,}357 labelled asset-weeks) and evaluate with grouped, embargoed temporal splits.",
          "We build a temporal exploitability-exposure target from sealed weekly EPSS and CISA KEV snapshots for 120 digest-pinned container images (6{,}357 labelled asset-weeks), evaluated with grouped, embargoed temporal splits."),
         ("A naive 4-week persistence baseline already explains most of the label's variance, and a single CVSS score almost none.", "A 4-week persistence baseline already explains most of the label's variance; a single CVSS score, almost none."),
         ("69.6\\% against a linear model on the same seven inputs and 66.5\\%", "69.6\\% against a linear model and 66.5\\%"),
         ("exact Shapley attribution places 78.9\\% of the model's attribution on exploitability and the KEV indicator, which are ingredients of the label; without them HANFIS shows no skill over CVSS (skill score $-0.14$, 95\\% interval $-0.34$ to $0.05$);",
          "exact Shapley attribution puts 78.9\\% on exploitability and the KEV indicator, ingredients of the label; without them HANFIS has no skill over CVSS (skill $-0.14$, interval $-0.34$ to $0.05$);")]
DISC = ("has the lowest error of all predictors we compared; the data do not support the claim", "has the lowest error of all predictors we compared at the four-week horizon (at eight and twelve weeks the gap to the formula closes, Section~\\ref{subsec:e14}); the data do not support the claim")
CONC = ("rather than better accuracy than a simple formula, and whether environmental context improves forecasts remains open.",
        "rather than better accuracy than a simple formula at the four-week horizon (at eight and twelve weeks it matches the formula without demonstrably exceeding it, and without the other inputs contributing; Section~\\ref{subsec:e14}), and whether environmental context improves forecasts remains open.")
C5 = ("formula baselines and an ablation of the label-ingredient inputs (Section~\\ref{subsec:e9}), using", "formula baselines, an ablation of the label-ingredient inputs and a horizon sweep (Sections~\\ref{subsec:e9} and~\\ref{subsec:e14}), using")
errors, edits, skipped = [], [], []
if "\\label{subsec:e14}" in s: print("sudah: sub-bagian E14")
elif s.count(ANCHOR) == 1: edits.append((s.index(ANCHOR), s.index(ANCHOR), SUB + "\n\n"))
else: errors.append(f"jangkar Discussion ditemukan {s.count(ANCHOR)}x (harus 1)")
def core(rx_or_text, new, name, is_rx=False):
    m = list(re.finditer(rx_or_text if is_rx else flex(rx_or_text), s))
    if len(m) == 1: edits.append((m[0].start(), m[0].end(), new))
    else: errors.append(f"{name}: jangkar ditemukan {len(m)}x (harus 1)")
if "a gap that closes at eight and twelve weeks" in s: print("sudah: abstrak")
else:
    core(TAIL_RX, TAIL_NEW, "abstrak (ekor post hoc)", True)
    for old, new in SHORT:
        m = list(re.finditer(flex(old), s))
        if len(m) == 1: edits.append((m[0].start(), m[0].end(), new))
        else: skipped.append(f"pemadatan abstrak: '{old[:50]}...' ({len(m)}x)")
if "at the four-week horizon (at eight and twelve weeks the gap" in s: print("sudah: Discussion")
else: core(DISC[0], DISC[1], "Discussion")
if "at the four-week horizon (at eight and twelve weeks it matches" in s: print("sudah: Conclusion")
else: core(CONC[0], CONC[1], "Conclusion")
if "and a horizon sweep (Sections" in s: print("sudah: C5")
else: core(C5[0], C5[1], "C5")
if errors: print("ABORT, tidak ada yang ditulis:"); [print("  -", e) for e in errors]; sys.exit(2)
if not edits: print("Sudah diterapkan seluruhnya."); sys.exit(0)
for st, en, new in sorted(edits, key=lambda t: -t[0]): s = s[:st] + new + s[en:]
shutil.copy(P, str(P) + ".pre-e14.bak"); P.write_text(s, encoding="utf-8"); print(f"OK: {len(edits)} perubahan")
for k in skipped: print("  DILEWATI (periksa manual):", k)
m = re.search(r"\\abstract\{(.*?)\}\n", s, re.S)
if m: print("palavras do resumo (aprox.):", len(re.sub(r"\\%|\$[^$]*\$|\{,\}|\\", " ", m.group(1)).split()))

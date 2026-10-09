#!/usr/bin/env python3
"""Tambal naskah untuk E9 dan E10: (1) abstrak baru (sekitar 250 kata) yang memuat keterbatasan post hoc, (2) satu klausa di paragraf validitas konstruk (Limitations),
(3) sub-bagian baru 'Label-ingredient ablation and information-minimal baselines (E9, E10)' dengan tabel, sebelum Discussion. Dari akar repo.
Gagal-tertutup (semua jangkar cocok tepat sekali atau tidak ada yang ditulis); idempoten; cadangan .pre-e9.bak."""
import re, shutil, sys
from pathlib import Path
P = Path("manuscript/sn-article.tex"); s = P.read_text(encoding="utf-8")
ABSTRACT = r'''Static, expert-weighted fuzzy risk scores go stale between elicitations, while a flat Adaptive Neuro-Fuzzy Inference System (ANFIS) over seven cloud-native risk inputs requires 128 rules and 1{,}052 parameters. We propose HANFIS, a hierarchical ANFIS that separates vulnerability and environmental reasoning before an integration tier adds threat intelligence, reducing the model to 34 rules and 176 parameters (73.4\% and 83.3\% fewer). We construct a temporal exploitability-exposure target from sealed weekly EPSS and CISA KEV snapshots for a digest-pinned inventory of 120 container images (6{,}357 labelled asset-weeks) and evaluate with grouped, embargoed temporal splits. A naive 4-week persistence baseline already explains most of the label's variance, and a single CVSS score almost none. Under a protocol frozen before training, HANFIS reduces mean squared error by 96.7\% against CVSS, 69.6\% against a linear model on the same seven inputs and 66.5\% against a parameter-matched flat ANFIS (95\% bootstrap intervals excluding zero), but is not distinguishable from persistence and is better only around structural breaks of the label. Post hoc analyses qualify these gains: exact Shapley attribution places 78.9\% of the model's attribution on exploitability and the KEV indicator, which are ingredients of the label; without them HANFIS shows no skill over CVSS (skill score $-0.14$, 95\% interval $-0.34$ to $0.05$); and it is not demonstrably better than gradient boosting restricted to those two inputs. Monotonicity holds in practice only for the dominant inputs. HANFIS is therefore a compact, transparent estimator of near-term exploitability exposure, not evidence that environmental context improves forecasts.'''
FRAG = r'''\subsection{Label-ingredient ablation and information-minimal baselines (E9, E10)}\label{subsec:e9}
Both analyses were designed after the attribution results of Section~\ref{subsec:e8} and are therefore post hoc. In E9 we retrained HANFIS with $x_2$ and $x_7$ replaced by the constant zero in training and test data, on the folds, seeds, embargo, validation split and hyperparameters of the confirmatory run, which we verified to reproduce the same 1{,}080 held-out rows. Skill scores are $\mathrm{SS}=1-\mathrm{MSE}_{\mathrm{model}}/\mathrm{MSE}_{\mathrm{reference}}$ with 95\% bootstrap intervals clustered by image (2{,}000 resamples). Without the two label ingredients the five-seed ensemble has a mean squared error of 14.23, against 0.41 with them and 12.54 for a single CVSS score; its skill over CVSS is $-0.135$ (interval $[-0.336,\,0.046]$) and over a ridge model on the remaining five inputs $-0.070$ ($[-0.250,\,0.096]$), and that ridge model is itself no better than CVSS ($-0.061$, $[-0.130,\,0.006]$). On this inventory the remaining inputs therefore carry no demonstrable information beyond CVSS, and essentially all of the model's skill comes from the two inputs that are also ingredients of the label.

In E10 we compared the confirmatory HANFIS predictions with the simplest functions of those inputs, trained on the same rows: a plug-in $100\,x_2$, ridge regression on $(x_2,x_7)$, and gradient boosting on $(x_2,x_7)$, on all seven inputs, and on the seven inputs plus the four-week lag of the label (Table~\ref{tab:e9}). HANFIS has a lower error than every learned alternative with an interval excluding zero, except gradient boosting restricted to $x_2$ and $x_7$ (skill $0.606$, interval $[-0.079,\,0.847]$). Adding the other inputs makes gradient boosting worse, not better, and models that receive the lagged label as a feature do much worse than the lag itself, which we attribute, without having tested it, to distribution shift between training and test periods. We therefore read HANFIS as a compact nonlinear estimator of exposure from $x_2$ and $x_7$ whose accuracy matches persistence without access to past labels, not as evidence that the vulnerability--environment decomposition improves forecasts.

\begin{table}[ht]
\caption{Label-ingredient ablation (E9) and information-minimal baselines (E10), 1{,}080 held-out rows. Skill score with 95\% image-clustered bootstrap interval; MSE of the model and of the reference.}\label{tab:e9}
\small
\begin{tabular}{@{}p{0.38\linewidth}rrr@{}}
\hline
Comparison & Skill & 95\% interval & MSE\\
\hline
\multicolumn{4}{@{}l}{\emph{E9: HANFIS retrained without $x_2$ and $x_7$}}\\
vs.\ CVSS only & $-0.135$ & $[-0.336,\,0.046]$ & 14.23 / 12.54\\
vs.\ ridge, remaining five inputs & $-0.070$ & $[-0.250,\,0.096]$ & 14.23 / 13.30\\
vs.\ HANFIS with all inputs & $-33.8$ & $[-56.5,\,-22.5]$ & 14.23 / 0.41\\
Ridge, five inputs, vs.\ CVSS only & $-0.061$ & $[-0.130,\,0.006]$ & 13.30 / 12.54\\
\multicolumn{4}{@{}l}{\emph{E10: HANFIS with all inputs vs.}}\\
Plug-in $100\,x_2$ & $0.859$ & $[0.672,\,0.931]$ & 0.41 / 2.89\\
Ridge on $(x_2,x_7)$ & $0.693$ & $[0.518,\,0.817]$ & 0.41 / 1.33\\
Ridge on lag-4 label, $x_2$, $x_7$ & $0.635$ & $[0.399,\,0.781]$ & 0.41 / 1.12\\
Boosting on $(x_2,x_7)$ & $0.606$ & $[-0.079,\,0.847]$ & 0.41 / 1.04\\
Boosting on seven inputs & $0.659$ & $[0.133,\,0.860]$ & 0.41 / 1.20\\
Boosting on lag-4 label and inputs & $0.653$ & $[0.104,\,0.858]$ & 0.41 / 1.18\\
Persistence (lag-4 label) & $0.015$ & $[-0.620,\,0.243]$ & 0.41 / 0.42\\
\hline
\end{tabular}
\end{table}'''
ANCHOR = "\\section{Discussion}\\label{sec5}"
OLD_CLAUSE = r"and 3.3\% on the environment inputs."
NEW_CLAUSE = r"and 3.3\% on the environment inputs, and without these two inputs the model shows no demonstrable skill over a single CVSS score (Section~\ref{subsec:e9})."
ab = list(re.finditer(r"\\abstract\{Static, expert-weighted.{0,4000}?available for the present assets\.\}", s, re.S))
errors, edits = [], []
if "Post hoc analyses qualify these gains" in s: print("sudah: abstrak")
elif len(ab) == 1: edits.append(("abstrak", ab[0].start(), ab[0].end(), "\\abstract{" + ABSTRACT + "}"))
else: errors.append(f"abstrak: cocok {len(ab)}x (harus 1)")
if "(Section~\\ref{subsec:e9})." in s: print("sudah: klausa Limitations")
elif s.count(OLD_CLAUSE) == 1: i = s.index(OLD_CLAUSE); edits.append(("klausa-limitations", i, i + len(OLD_CLAUSE), NEW_CLAUSE))
else: errors.append(f"klausa-limitations: jangkar ditemukan {s.count(OLD_CLAUSE)}x (harus 1)")
insert = "\\label{subsec:e9}" not in s
if insert and s.count(ANCHOR) != 1: errors.append(f"sisip: jangkar Discussion ditemukan {s.count(ANCHOR)}x (harus 1)")
if errors: print("ABORT, tidak ada yang ditulis:"); [print("  -", e) for e in errors]; sys.exit(2)
if not edits and not insert: print("Sudah diterapkan seluruhnya."); sys.exit(0)
for name, a, b, new in sorted(edits, key=lambda t: -t[1]): s = s[:a] + new + s[b:]; print(f"diterapkan: {name}")
if insert: s = s.replace(ANCHOR, FRAG + "\n\n" + ANCHOR); print("diterapkan: sub-bagian E9/E10 (sebelum Discussion)")
shutil.copy(P, str(P) + ".pre-e9.bak"); P.write_text(s, encoding="utf-8"); print("OK")

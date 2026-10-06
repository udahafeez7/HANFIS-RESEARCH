#!/usr/bin/env python3
"""Tulis temuan eksploratori e4_influence/e4_regime ke naskah dengan angka dari keluaran skrip:
(1) abstrak: H1b tidak lagi disebut 'open result' saja; (2) sec. 4.5: ganti kalimat spekulatif H2 dengan MSE nyata
dan tambah paragraf analisis rezim post hoc; (3) Limitations: gerbang obs/parameter per fold dan dominasi fold 0 pada H2;
(4) Conclusion: lunakkan klaim 'bukan artefak pelatihan'. Gagal-tertutup (tiap jangkar tepat 1x), idempoten."""
import sys, shutil, pathlib
P = pathlib.Path("manuscript/sn-article.tex"); s = P.read_text(encoding="utf-8")
if "tab:e4-regime" in s or "dominated by the first block" in s:
    print("Sudah diterapkan; tidak ada perubahan."); sys.exit(0)
REGIME = r"""\emph{Where HANFIS and persistence differ.} The pooled skill against persistence ($0.015$) hides two regimes, and
this exploratory, post hoc analysis (not part of the Holm-corrected family) separates them. Dropping one held-out
fold at a time leaves it between $0.007$ and $0.172$ except for fold~3, whose removal gives $-1.168$. Fold~3 ends at
the EPSS model change, and the label of week $t$ is built from snapshots up to $t{+}28$ days ahead whereas the
persistence forecast reuses the label of week $t{-}4$. For the four weeks in which the label is fully computed under the
new model while the lagged label is still computed under the old one (2026-W24 to W27; 95 rows), skill against
persistence is $+0.483$; on the remaining 985 rows it is $-0.420$. In 2026-W25 and W26 the squared error of persistence is
$63.1$ and $28.9$ against $0.7$ and $1.0$ for HANFIS, while the parameter-matched model also adapts ($4.8$ and $5.2$), so the
advantage reflects access to the current EPSS input rather than the hierarchical structure. In the week the label first
jumps (W24) neither HANFIS nor persistence anticipates it ($108.9$ and $115.2$). In the stable weeks that follow
HANFIS keeps a small error floor (about $0.7$--$0.8$ per week over 24 rows, against $0.1$ for persistence). The pooled
advantage of $6.5$ squared-error units is thus the sum of $+104.1$ in the break weeks and $-97.6$ elsewhere. The same
pattern appears before the change: in the run restricted to earlier weeks the advantage concentrates in 2026-W06 and W07,
the weeks of one image's label surge (an image carrying 77.8\% of the persistence error), and the total is $-12.3$.
HANFIS is therefore reactive rather than predictive: better than persistence when the label moves, worse when it does not.
Two further observations qualify H2. The first held-out fold, trained on 2.2 observations per parameter, contributes
$91\%$ of the pooled gap to the matched model (squared error $869.6$ against $73.9$); without it the skill against
FlatANFISMatched is $0.183$ and against the full flat model $0.084$, whereas the skill against the ridge model stays between
$0.656$ and $0.793$ whichever fold is removed.

"""
R = [
 ("HANFIS is not yet distinguishable from the persistence baseline (confidence interval crossing zero), which we report as an open rather than a negative result.",
  "HANFIS is not distinguishable from the persistence baseline overall (confidence interval crossing zero), and a post hoc analysis shows it is better only around structural breaks in the label and worse in stable periods, so we report H1b as unconfirmed rather than as a tie."),
 ("the larger margin over the matched flat model (H2: $0.665$ to $0.913$) may reflect\nthat the post-change blocks are harder for HANFIS than for a flat model, but this analysis does not establish it.",
  "the larger margin over the matched flat model (H2: $0.665$ to $0.913$) comes from the matched\nmodel, whose mean squared error per held-out row rises from $1.22$ to $3.77$ while that of HANFIS stays at $0.41$ and $0.33$."),
 ("\\section{Discussion}\\label{sec5}", REGIME + "\\section{Discussion}\\label{sec5}"),
 ("leaves the confirmatory conclusions\nunchanged (Section~\\ref{subssec4.5}).",
  "leaves the confirmatory conclusions\nunchanged (Section~\\ref{subssec4.5}). The data-sufficiency gate (at least ten observations per parameter) is met by the pooled\nsample ($6{,}833$ rows against 176 parameters) but not by the two earliest held-out folds ($2.2$ and $7.1$ observations per\nparameter), which are also those in which HANFIS is furthest behind persistence, and H2's pooled margin is dominated by the\nfirst fold (Section~\\ref{subssec4.5})."),
 ("H2's margin is read as evidence that the vulnerability/environmental/threat\ndecomposition mirrors the label's own generative structure (Section~\\ref{subsec:target-definition}) --\nan advantage a capacity-matched but domain-blind flat model cannot access from input density alone --\nrather than as a training artefact, on the strength of a per-fold check in which HANFIS wins four of\nthe five held-out blocks (Section~\\ref{subssec4.3}).",
  "H2 is confirmed as non-inferiority to a capacity-matched flat model, and HANFIS has the lower error in four of the\nfive held-out blocks (Section~\\ref{subssec4.3}); the pooled margin is, however, dominated by the first block, where\ntraining is thinnest, so it is read as suggestive of, not as evidence for, a structural advantage of the\nvulnerability/environmental/threat decomposition (Section~\\ref{subssec4.5})."),
]
for old, _ in R:
    n = s.count(old)
    if n != 1: sys.exit(f"ABORT: jangkar {n}x (harus 1): {old[:80]!r}")
for old, new in R: s = s.replace(old, new)
shutil.copy(P, str(P) + ".pre-regime.bak"); P.write_text(s, encoding="utf-8"); print("OK")

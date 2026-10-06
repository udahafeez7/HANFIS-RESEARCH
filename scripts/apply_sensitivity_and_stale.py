#!/usr/bin/env python3
"""Patch 0074: (1) hyperref hypertexnames=false (13 peringatan 'same identifier' -> 0, diuji di salinan);
(2) '120 images/120-image' -> '120 assets/120-asset' (konsisten dgn sec. 3.5); (3) buang kalimat Discussion/Conclusion
yang basi (E4/E5 sudah selesai, inventaris sudah 120); (4) sensitivitas post hoc pra-pergantian model EPSS
(Tabel baru di sec. 4.5 + satu kalimat di Limitations). Gagal-tertutup: tiap jangkar tepat 1x, jika tidak, tidak menulis. Idempoten."""
import sys, shutil, pathlib
P = pathlib.Path("manuscript/sn-article.tex")
s = P.read_text(encoding="utf-8")
if "tab:e4-epss" in s:
    print("Sudah diterapkan; tidak ada perubahan."); sys.exit(0)

SENS = r"""\emph{Sensitivity to the EPSS model change.} The EPSS scoring model changed version on 2026-06-15
(\texttt{v2025.03.14} to \texttt{v2026.06.15}). Because the label of week $t$ is computed from snapshots
$t{+}7,\dots,t{+}28$ days ahead, two of the five held-out blocks of the confirmatory comparison involve labels
computed under the newer version: one block straddles the change and one lies wholly after it. This contrast
was not pre-registered, so it is reported as a post hoc sensitivity analysis. The confirmatory pipeline was
re-run with the same code, seeds and frozen configuration on the 4{,}560 asset-weeks whose labels all
pre-date the change (weeks up to 2026-05-11; 720 held-out rows), with the results in
Table~\ref{tab:e4-epss}. H1a, H1c and H2 remain confirmed, and H1b remains unconfirmed, with a much wider
interval. Because both the training and the held-out windows change, skill scores are not directly comparable
across the two columns; the larger margin over the matched flat model (H2: $0.665$ to $0.913$) may reflect
that the post-change blocks are harder for HANFIS than for a flat model, but this analysis does not establish it.

\begin{table}[h]
\caption{Post hoc sensitivity of the confirmatory comparison to the EPSS model change: full run versus weeks
whose labels all pre-date 2026-06-15 (skill score, 95\% group-clustered bootstrap CI).}\label{tab:e4-epss}
\begin{tabular}{@{}llcc@{}}
\toprule
Hypothesis & Comparator & Full run & Pre-change weeks \\
\midrule
H1a & Single CVSS score & 0.967 [0.951, 0.980] & 0.973 [0.939, 0.991] \\
H1b & Persistence (4-week) & 0.015 [$-$0.607, 0.246] & $-$0.055 [$-$2.731, 0.201] \\
H1c & Ridge, 7 inputs & 0.696 [0.527, 0.816] & 0.728 [0.484, 0.901] \\
H2 & FlatANFISMatched & 0.665 [0.269, 0.844] & 0.913 [0.753, 0.974] \\
H2$'$ & Flat ANFIS (full) & 0.253 & 0.441 \\
\botrule
\end{tabular}
\end{table}

"""
R = [
 ("\\begin{document}", "\\hypersetup{hypertexnames=false}\n\\begin{document}"),
 ("On the completed 120-image inventory", "On the completed 120-asset inventory"),
 ("on the completed 120-image\ninventory", "on the completed 120-asset\ninventory"),
 ("The full inventory of 120 images is now complete", "The full inventory of 120 assets is now complete"),
 ("re-run on the completed 120-image inventory (6{,}357 rows)", "re-run on the completed 120-asset inventory (6{,}357 labelled rows)"),
 ("should be read once it is complete. First, the", "should be read. First, the"),
 ("Confirming H1b against persistence, running the bottleneck-width sweep (Section~\\ref{subssec4.4}) to\n"
  "test whether widening the scalar inter-tier bottleneck trades parameters for the interaction H1b's gap\n"
  "may reflect, and re-running the confirmatory comparison as the inventory scales from 109 toward the\n"
  "120 images targeted for the final manuscript, are the immediate next steps. ",
  "Confirming H1b against persistence is the main open question; the bottleneck-width sweep\n"
  "(Section~\\ref{subssec4.4}) found that widening the scalar inter-tier bottleneck from $k{=}1$ to $k{=}2$\n"
  "does not close the gap to persistence and is significantly worse than it. "),
 ("a threat to label comparability across that\nboundary that is recorded but not yet corrected for.",
  "a threat to label comparability across that\nboundary; two of the five held-out blocks involve labels computed under the newer version, and a post hoc\n"
  "re-analysis restricted to weeks whose labels all pre-date the change leaves the confirmatory conclusions\nunchanged (Section~\\ref{subssec4.5})."),
 ("\\section{Discussion}\\label{sec5}", SENS + "\\section{Discussion}\\label{sec5}"),
]
for old, _ in R:
    n = s.count(old)
    if n != 1: sys.exit(f"ABORT: jangkar {n}x (harus 1): {old[:70]!r}")
for old, new in R: s = s.replace(old, new)
shutil.copy(P, str(P) + ".pre-0074.bak")
P.write_text(s, encoding="utf-8"); print("OK")

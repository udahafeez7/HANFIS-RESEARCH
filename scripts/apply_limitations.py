#!/usr/bin/env python3
"""Tambah paragraf validitas konstruk (label dan masukan berbagi bahan; 'dinamis' bukan berbasis telemetri; atribusi E6) di awal subbagian Limitations.
Jalankan dari akar repo. Gagal-tertutup (jangkar harus tepat satu), idempoten, cadangan .pre-lim.bak."""
import shutil, sys
from pathlib import Path
P = Path("manuscript/sn-article.tex"); s = P.read_text(encoding="utf-8")
ANCHOR = "\\subsection{Limitations}"
MARK = "two limits of construct validity"
PARA = (r"Two limits of construct validity deserve emphasis before the usual caveats. First, the label and two of the inputs share ingredients: "
        r"$x_2$ (EPSS $\times\,\rho$) and $x_7$ (the KEV indicator) are the values at $t$ of quantities that the label aggregates over $t{+}7,\dots,t{+}28$, "
        r"and runtime reachability $\rho$ enters both. The task is therefore to forecast the near future of exploitability signals that the model can already see, "
        r"not to predict independent compromise outcomes, for which no ground truth exists here; the persistence baseline, built in the same way, is the relevant bar, "
        r"and the comparison with a single CVSS score should be read in that light. Second, the dynamic character of the score comes from the time-varying EPSS and KEV feeds "
        r"and from runtime reachability; runtime telemetry (CPU, memory, latency) is used only to quantify observability overhead and is not a model input, "
        r"so ``dynamic'' must not be read as telemetry-driven scoring. The rule-level attribution is faithful on average but not uniformly (Section~\ref{sec:e6}), "
        r"and we do not claim validated explanations.")
if MARK in s.lower(): print("Sudah diterapkan; tidak ada perubahan."); sys.exit(0)
if s.count(ANCHOR) != 1: sys.exit(f"ABORT: jangkar \\subsection{{Limitations}} ditemukan {s.count(ANCHOR)}x (harus 1); tidak ada yang ditulis")
shutil.copy(P, str(P) + ".pre-lim.bak"); P.write_text(s.replace(ANCHOR, ANCHOR + "\n" + PARA + "\n", 1), encoding="utf-8"); print("OK: paragraf validitas konstruk ditambahkan")

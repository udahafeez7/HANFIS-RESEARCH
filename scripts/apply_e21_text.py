#!/usr/bin/env python3
r"""Menyisipkan subbagian 'Calibration (E21)' (post hoc, dijalankan setelah registrasi E7 publik) ke manuscript/sn-article.tex, tepat sebelum \section{Discussion}.
Gagal-tertutup: jangkar '\section{Discussion}\label{sec5}' harus ada tepat sekali dan didahului '\end{table}'; lingkungan table/tabular harus seimbang sesudah sisipan. Tidak ada yang ditulis bila salah satunya gagal.
Idempoten (label subsec:e21 sudah ada -> tidak berubah). Cadangan .pre-e21.bak.   python scripts/apply_e21_text.py [--tex manuscript/sn-article.tex]"""
import argparse, re, shutil, sys
from pathlib import Path

BLOCK = r'''\subsection{Calibration (E21)}\label{subsec:e21}
We checked calibration after the registration of the forward evaluation had become public (post hoc, descriptive, no training). For the four-week out-of-fold predictions of persistence, the formula and HANFIS we report the mean error (prediction minus label), the slope $\beta$ and intercept $\alpha$ of the regression of the label on the prediction (a calibrated predictor has $\beta=1$ and $\alpha=0$), and the mean label by decile of the prediction. Intervals come from the bootstrap clustered by image used above. The coefficients of the formula were fitted inside each training fold, on the same folds as HANFIS, so its calibration is also out-of-fold. Table~\ref{tab:e21} covers all 1{,}080 rows and the 890 rows whose label window does not straddle the change of the EPSS model (Section~\ref{subsec:e16}).

All three predictors lie close to the identity line. Persistence runs low on all rows (mean error $-0.097$, interval $-0.196$ to $-0.013$), and almost all of this bias comes from the weeks around the model change: on unaffected rows it is $-0.015$ ($-0.079$ to $0.025$). The interval of the formula's mean error includes zero in both samples. HANFIS departs most: its slope is $1.025$ ($1.008$ to $1.044$) on all rows and $1.031$ ($1.014$ to $1.053$) on unaffected rows, where its intercept is $-0.193$ ($-0.300$ to $-0.085$). In the fourth decile of its predictions the mean prediction is $1.0$ and the mean label $0.5$ (unaffected rows: $1.1$ and $0.5$); the mean label does not rise between the third and fourth decile ($0.5$ in both) although the mean prediction doubles. In the upper deciles predictions and labels agree ($7.9$ and $8.1$ in the eighth decile, $9.8$ and $9.9$ in the ninth). These departures are small next to the label scale. The intervals resample images and treat weekly shocks shared by all images as fixed, so a bootstrap clustered by week would give wider intervals; we read the results as descriptive.

\begin{table}[ht]
\caption{Calibration of the four-week out-of-fold predictions (E21, post hoc): mean error (prediction minus label), and slope $\beta$ and intercept $\alpha$ of the regression of the label on the prediction, with 95\% image-bootstrap intervals. Unaffected rows are those whose label window does not straddle the change of the EPSS model.}\label{tab:e21}
\footnotesize
\setlength{\tabcolsep}{3pt}
\begin{tabular}{@{}p{0.17\linewidth}p{0.26\linewidth}p{0.26\linewidth}p{0.26\linewidth}@{}}
\hline
Predictor & Mean error & Slope $\beta$ & Intercept $\alpha$\\
\hline
\multicolumn{4}{@{}l}{\emph{All rows (1{,}080)}}\\
Persistence & $-0.097$ $[-0.196,\,-0.013]$ & $0.997$ $[0.986,\,1.007]$ & $0.109$ $[0.012,\,0.228]$\\
Formula & $-0.040$ $[-0.106,\,0.017]$ & $0.998$ $[0.990,\,1.005]$ & $0.048$ $[-0.021,\,0.132]$\\
HANFIS & $0.016$ $[-0.080,\,0.104]$ & $1.025$ $[1.008,\,1.044]$ & $-0.115$ $[-0.228,\,0.007]$\\
\multicolumn{4}{@{}l}{\emph{Unaffected rows (890)}}\\
Persistence & $-0.015$ $[-0.079,\,0.025]$ & $0.997$ $[0.993,\,1.001]$ & $0.026$ $[-0.017,\,0.091]$\\
Formula & $0.012$ $[-0.029,\,0.040]$ & $1.000$ $[0.997,\,1.002]$ & $-0.012$ $[-0.044,\,0.035]$\\
HANFIS & $0.068$ $[-0.029,\,0.157]$ & $1.031$ $[1.014,\,1.053]$ & $-0.193$ $[-0.300,\,-0.085]$\\
\hline
\end{tabular}
\end{table}

'''
ap = argparse.ArgumentParser(); ap.add_argument("--tex", default="manuscript/sn-article.tex"); a = ap.parse_args()
P = Path(a.tex); s = P.read_text(encoding="utf-8")
if r"\label{subsec:e21}" in s: print("Tidak ada perubahan (subbagian E21 sudah ada)."); sys.exit(0)
ANCH = r"\section{Discussion}\label{sec5}"
n = s.count(ANCH)
if n != 1: sys.exit(f"ABORT, tidak ada yang ditulis: jangkar Discussion ditemukan {n}x (harus 1)")
i = s.index(ANCH)
if not s[:i].rstrip().endswith(r"\end{table}"): sys.exit(r"ABORT, tidak ada yang ditulis: sebelum Discussion tidak ada \end{table} (tata letak naskah berubah)")
new = s[:i] + BLOCK + s[i:]
for env in ("table", "tabular"):
    b, e = new.count(r"\begin{%s}" % env), new.count(r"\end{%s}" % env)
    if b != e: sys.exit(f"ABORT, tidak ada yang ditulis: \\begin/\\end{{{env}}} tidak seimbang ({b} vs {e})")
shutil.copy(P, str(P) + ".pre-e21.bak"); P.write_text(new, encoding="utf-8"); print("OK: subbagian Calibration (E21) disisipkan sebelum Discussion")

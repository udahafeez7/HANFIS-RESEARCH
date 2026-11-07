#!/usr/bin/env python3
"""apply_af1_new_items.py - Additional file 1: Table S9 (E25 per fold), Table S10 (frozen hyperparameters), Tables S11 sampai S13 (fungsi keanggotaan dan 34 aturan satu model, E27), Figure S4 (permukaan respons x2 dan x7), pengantar Supplementary notes, dan label H2/H3 di Table S3.

Lapisan (P1): naskah (pelaporan). Dokumen: manuscript/additional_file_1.tex, manuscript/fig_e27_surface_x2_x7.pdf (salinan dari manuscript/figures/e4bis_pdp_x2x7). Angka E25 dari results_python/e25/raw_20261107T040539Z.csv; aturan dari model tersimpan
results_python/e4bis_120_models/models/fold0_seed20260928_hanfis.pt lewat aksesor model (rekonstruksi diverifikasi terhadap forward pass oleh scripts/e27_rules_and_surface.py). Hiperparameter dari scripts/e4_run.py, amendemen A-09 dan A-16.
Teks-persis, gagal-tertutup: tiap teks lama harus cocok TEPAT SATU KALI (spasi dan baris baru dinormalkan) sebelum apa pun ditulis.
Idempoten: bila semua teks baru sudah terpasang, keluar 0 tanpa menulis. Keadaan campuran = ABORT.
Akhir baris (LF/CRLF) dipertahankan. Cadangan: manuscript/additional_file_1.tex.pre-af1new.bak.
Jalankan dari root repo:  python3 Patch/apply_af1_new_items.py
"""
import os, re, sys

P = os.path.join("manuscript", "additional_file_1.tex")
if not (os.path.isfile(P) and os.path.isdir(".git")):
    sys.exit("ABORT: jalankan dari root repo (harus ada .git dan manuscript/additional_file_1.tex)")

PAIRS = [('\\section*{Supplementary figures}',
  '\\begin{table}[ht]\n'
  '\\caption{E25 per fold: median over three repetitions of the training time, the peak memory increase and the single-row latency of the full flat '
  'ANFIS (F), FlatANFISMatched (M) and HANFIS (H). Unregistered descriptive measurement, first frozen seed, one machine.}\n'
  '\\footnotesize\n'
  '\\setlength{\\tabcolsep}{3pt}\n'
  '\\begin{tabular}{@{}lrrrrrrrrr@{}}\n'
  '\\hline\n'
  ' & \\multicolumn{3}{c}{Training time (s)} & \\multicolumn{3}{c}{Memory increase (MiB)} & \\multicolumn{3}{c}{Latency ($\\mu$s)}\\\\\n'
  'Fold & F & M & H & F & M & H & F & M & H\\\\\n'
  '\\hline\n'
  '0 & 0.87 & 0.23 & 5.71 & 0.27 & 5.56 & 0.11 & 92.5 & 47.1 & 395.3\\\\\n'
  '1 & 2.17 & 0.57 & 7.66 & 2.48 & 66.75 & 0.25 & 94.1 & 49.1 & 387.6\\\\\n'
  '2 & 11.03 & 0.95 & 9.43 & 4.99 & 194.13 & 0.46 & 96.4 & 50.0 & 402.1\\\\\n'
  '3 & 7.30 & 2.71 & 8.42 & 8.20 & 390.17 & 0.85 & 95.6 & 53.8 & 398.2\\\\\n'
  '4 & 12.06 & 6.37 & 10.09 & 6.72 & 663.46 & 0.72 & 97.1 & 47.3 & 424.2\\\\\n'
  '\\hline\n'
  '\\end{tabular}\n'
  '\\end{table}\n'
  '\\begin{table}[ht]\n'
  '\\caption{Frozen training configuration of the confirmatory comparison (amendments A-09 and A-16).}\n'
  '\\footnotesize\n'
  '\\begin{tabular}{@{}p{0.34\\linewidth}p{0.60\\linewidth}@{}}\n'
  '\\hline\n'
  'Item & Value\\\\\n'
  '\\hline\n'
  'HANFIS membership functions & Gaussian, $m=2$ on each raw input, $m_I=3$ on $v$ and $e$, softplus-constrained non-negative slopes (monotone)\\\\\n'
  'HANFIS training & hybrid closed-form and Adam, alternating lower-panel scheme; learning rate $10^{-2}$, ridge $10^{-3}$\\\\\n'
  'Restarts and stopping & three pre-registered restarts per fold and seed, lowest validation loss kept; patience 100, minimum 200 and maximum 600 '
  'epochs\\\\\n'
  'Seeds & 20260928, 20261005, 20261012, 20261019, 20261026; held-out predictions averaged over the five seeds\\\\\n'
  'Split & \\texttt{GroupTimeSplit}, five folds, 30-day embargo equal to the outcome window; 15\\% validation carve-out per fold\\\\\n'
  'FlatANFISMatched & subtractive clustering with the radius searched on each training fold so that parameters match HANFIS within $\\pm 5\\%$; '
  'patience 100, minimum 200 epochs\\\\\n'
  'Flat ANFIS (full) & grid partition with $m=2$ on seven inputs (128 rules, 1{,}052 parameters); patience 60\\\\\n'
  '\\hline\n'
  '\\end{tabular}\n'
  '\\end{table}\n'
  '\\begin{table}[ht]\n'
  '\\caption{Membership functions of the documented HANFIS (fold 0, first frozen seed), in normalised input units. The last column states whether '
  'the centres keep the order of the membership-function index (one entry per input).}\n'
  '\\footnotesize\n'
  '\\begin{tabular}{@{}lllrrl@{}}\n'
  '\\hline\n'
  'Panel & Input & Function & Centre $c$ & Width $s$ & Centres in index order\\\\\n'
  '\\hline\n'
  'V & $x_1$ & MF1 & 0.153 & 0.174 & yes\\\\\n'
  'V & $x_1$ & MF2 & 0.546 & 0.454 & \\\\\n'
  'V & $x_2$ & MF1 & 0.682 & 0.176 & no\\\\\n'
  'V & $x_2$ & MF2 & 0.282 & 0.385 & \\\\\n'
  'V & $x_3$ & MF1 & -0.099 & 0.176 & yes\\\\\n'
  'V & $x_3$ & MF2 & 0.371 & 0.468 & \\\\\n'
  'E & $x_4$ & MF1 & 0.631 & 0.390 & yes\\\\\n'
  'E & $x_4$ & MF2 & 0.998 & 0.184 & \\\\\n'
  'E & $x_5$ & MF1 & 0.347 & 0.257 & yes\\\\\n'
  'E & $x_5$ & MF2 & 1.072 & 0.174 & \\\\\n'
  'E & $x_6$ & MF1 & -0.061 & 0.194 & yes\\\\\n'
  'E & $x_6$ & MF2 & 0.593 & 0.284 & \\\\\n'
  'I & $v$ & MF1 & 0.352 & 0.379 & no\\\\\n'
  'I & $v$ & MF2 & 0.677 & 0.315 & \\\\\n'
  'I & $v$ & MF3 & 0.659 & 0.252 & \\\\\n'
  'I & $e$ & MF1 & 0.317 & 0.244 & no\\\\\n'
  'I & $e$ & MF2 & 0.297 & 0.328 & \\\\\n'
  'I & $e$ & MF3 & 0.484 & 0.362 & \\\\\n'
  'I & $x_7$ & MF1 & 0.218 & 0.280 & yes\\\\\n'
  'I & $x_7$ & MF2 & 0.605 & 0.296 & \\\\\n'
  '\\hline\n'
  '\\end{tabular}\n'
  '\\end{table}\n'
  '\\begin{table}[ht]\n'
  '\\caption{Rules of panels $V$ and $E$ of the documented HANFIS (fold 0, first frozen seed): membership-function index per input (inputs in the '
  'order $x_1,x_2,x_3$ for $V$ and $x_4,x_5,x_6$ for $E$) and the consequent $f=b_0+b_1z_1+b_2z_2+b_3z_3$ in normalised units (slopes after the '
  'softplus constraint).}\n'
  '\\footnotesize\n'
  '\\begin{tabular}{@{}llrrrr@{}}\n'
  '\\hline\n'
  'Rule & Antecedent & $b_0$ & $b_1$ & $b_2$ & $b_3$\\\\\n'
  '\\hline\n'
  'V1 & MF1, MF1, MF1 & +0.001 & 0.000 & 0.000 & 0.000\\\\\n'
  'V2 & MF1, MF1, MF2 & +0.001 & 0.000 & 0.000 & 0.000\\\\\n'
  'V3 & MF1, MF2, MF1 & +0.839 & 0.000 & 0.000 & 0.000\\\\\n'
  'V4 & MF1, MF2, MF2 & +0.760 & 0.014 & 0.000 & 0.037\\\\\n'
  'V5 & MF2, MF1, MF1 & +0.001 & 0.000 & 0.000 & 0.000\\\\\n'
  'V6 & MF2, MF1, MF2 & +0.044 & 0.037 & 0.003 & 0.036\\\\\n'
  'V7 & MF2, MF2, MF1 & +0.621 & 0.001 & 0.001 & 0.001\\\\\n'
  'V8 & MF2, MF2, MF2 & +0.767 & 0.000 & 1.420 & 0.000\\\\\n'
  '\\hline\n'
  'E1 & MF1, MF1, MF1 & +0.086 & 0.000 & 0.025 & 0.000\\\\\n'
  'E2 & MF1, MF1, MF2 & +0.078 & 0.172 & 0.000 & 0.000\\\\\n'
  'E3 & MF1, MF2, MF1 & +0.085 & 0.024 & 0.060 & 0.000\\\\\n'
  'E4 & MF1, MF2, MF2 & -0.030 & 0.004 & 0.000 & 0.084\\\\\n'
  'E5 & MF2, MF1, MF1 & -0.002 & 0.030 & 0.000 & 0.005\\\\\n'
  'E6 & MF2, MF1, MF2 & +0.019 & 0.000 & 0.000 & 0.000\\\\\n'
  'E7 & MF2, MF2, MF1 & +0.057 & 0.040 & 0.040 & 0.011\\\\\n'
  'E8 & MF2, MF2, MF2 & -0.005 & 0.000 & 0.000 & 0.000\\\\\n'
  '\\hline\n'
  '\\end{tabular}\n'
  '\\end{table}\n'
  '\\begin{table}[ht]\n'
  '\\caption{Rules of the integration panel $I$ of the documented HANFIS (fold 0, first frozen seed): membership-function index for $(v,e,x_7)$ and '
  'the consequent $f=b_0+b_1v+b_2e+b_3x_7$ in normalised units. A negative intercept with small slopes gives a negative output that is clipped at '
  'zero.}\n'
  '\\footnotesize\n'
  '\\begin{tabular}{@{}llrrrr@{}}\n'
  '\\hline\n'
  'Rule & Antecedent $(v,e,x_7)$ & $b_0$ & $b_1$ & $b_2$ & $b_3$\\\\\n'
  '\\hline\n'
  'I1 & MF1, MF1, MF1 & -0.529 & 0.000 & 0.000 & 0.004\\\\\n'
  'I2 & MF1, MF1, MF2 & -0.002 & 0.008 & 0.000 & 0.084\\\\\n'
  'I3 & MF1, MF2, MF1 & -0.665 & 0.000 & 0.000 & 0.005\\\\\n'
  'I4 & MF1, MF2, MF2 & -0.002 & 0.005 & 0.000 & 0.109\\\\\n'
  'I5 & MF1, MF3, MF1 & -0.455 & 0.000 & 0.000 & 0.004\\\\\n'
  'I6 & MF1, MF3, MF2 & -0.002 & 0.005 & 0.000 & 0.072\\\\\n'
  'I7 & MF2, MF1, MF1 & +0.136 & 0.758 & 0.074 & 0.000\\\\\n'
  'I8 & MF2, MF1, MF2 & +0.027 & 0.030 & 0.008 & 0.000\\\\\n'
  'I9 & MF2, MF2, MF1 & +0.080 & 0.808 & 0.080 & 0.000\\\\\n'
  'I10 & MF2, MF2, MF2 & +0.022 & 0.020 & 0.010 & 0.006\\\\\n'
  'I11 & MF2, MF3, MF1 & +0.092 & 0.613 & 0.061 & 0.000\\\\\n'
  'I12 & MF2, MF3, MF2 & +0.019 & 0.020 & 0.007 & 0.000\\\\\n'
  'I13 & MF3, MF1, MF1 & -0.457 & 0.217 & 0.000 & 0.005\\\\\n'
  'I14 & MF3, MF1, MF2 & +0.030 & 0.037 & 0.005 & 0.103\\\\\n'
  'I15 & MF3, MF2, MF1 & -0.623 & 0.166 & 0.000 & 0.007\\\\\n'
  'I16 & MF3, MF2, MF2 & +0.032 & 0.035 & 0.007 & 0.135\\\\\n'
  'I17 & MF3, MF3, MF1 & -0.406 & 0.158 & 0.000 & 0.004\\\\\n'
  'I18 & MF3, MF3, MF2 & +0.023 & 0.028 & 0.005 & 0.089\\\\\n'
  '\\hline\n'
  '\\end{tabular}\n'
  '\\end{table}\n'
  '\\section*{Supplementary figures}'),
 ('\\section*{Supplementary notes}',
  '\\begin{figure}[ht]\n'
  '\\centering\n'
  '\\includegraphics[width=0.72\\linewidth]{fig_e27_surface_x2_x7.pdf}\n'
  '\\caption{Response of the five-seed ensemble of fold 0 over exploitability ($x_2$) and threat intelligence ($x_7$), the other inputs held at '
  'their sample medians (E27, descriptive, forward pass of the saved models, no training).}\\label{fig:e27-surface}\n'
  '\\end{figure}\n'
  '\n'
  '\\section*{Supplementary notes}\n'
  'Notes S1 to S7 reproduce the original wording of the corresponding main-text sections as they stood on 3 November 2026. The main text has since '
  'been revised; for example, the comparison with FlatANFISMatched that these notes label H2 is labelled H2/H3 in the main text.'),
 ('H2 & FlatANFISMatched & 0.665 [0.269, 0.844] & 0.913', 'H2/H3 & FlatANFISMatched & 0.665 [0.269, 0.844] & 0.913')]


def rx(text):
    return re.compile(r"\s+".join(re.escape(t) for t in text.split()))


raw = open(P, "rb").read()
crlf = b"\r\n" in raw
s = raw.decode("utf-8").replace("\r\n", "\n")

state = []
for n, (old, new) in enumerate(PAIRS, 1):
    co, cn = len(rx(old).findall(s)), len(rx(new).findall(s))
    nrm = lambda z: " ".join(z.split())
    if co == 1 and cn == 0:
        state.append("old")
    elif cn >= 1 and (co == 0 or nrm(old) in nrm(new)):
        state.append("new")
    else:
        sys.exit(f"ABORT: pasangan {n}: teks lama cocok {co} kali, teks baru {cn} kali; tidak ada yang ditulis")
if all(x == "new" for x in state):
    print("SUDAH TERPASANG: semua", len(PAIRS), "suntingan; tidak ada yang ditulis")
    sys.exit(0)
if any(x == "new" for x in state):
    sys.exit("ABORT: keadaan campuran (sebagian suntingan sudah terpasang); tidak ada yang ditulis")

for n, (old, new) in enumerate(PAIRS, 1):
    s, k = rx(old).subn(lambda m, new=new: new, s, count=1)
    if k != 1:
        sys.exit(f"ABORT: pasangan {n} tidak dapat diterapkan; tidak ada yang ditulis")

out = (s.replace("\n", "\r\n") if crlf else s).encode("utf-8")
with open(P + ".pre-af1new.bak", "wb") as f:
    f.write(raw)
with open(P, "wb") as f:
    f.write(out)
print("OK", len(PAIRS), "suntingan |", "CRLF" if crlf else "LF", "| cadangan", P + ".pre-af1new.bak")

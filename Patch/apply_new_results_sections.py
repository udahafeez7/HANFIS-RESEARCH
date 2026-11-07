#!/usr/bin/env python3
"""apply_new_results_sections.py - tiga subbagian Results baru: E25 (biaya komputasi terhadap flat ANFIS, Tabel perbandingan), E26 (ablasi x7 untuk H4), E27 (aturan terlatih dan urutan fungsi keanggotaan).

Lapisan (P1): naskah (pelaporan hasil). Dokumen: manuscript/sn-article.tex. Angka dari results_python/e25/summary_20261107T040539Z.json, results_python/e26/e26_summary_20261107T042449Z.json, protocols/E25_*.md dan E26_*.md, dan docs/progress/E26_E27_results_2026-11-07.md.
Ketiganya post hoc atau deskriptif, tidak terdaftar, dijalankan setelah E7 tanpa data E7; protokol dibekukan lebih dulu (tag e25-protocol-2026-11-07 dan e26-protocol-2026-11-07).
Teks-persis, gagal-tertutup: tiap teks lama harus cocok TEPAT SATU KALI (spasi dan baris baru dinormalkan) sebelum apa pun ditulis.
Idempoten: bila semua teks baru sudah terpasang, keluar 0 tanpa menulis. Keadaan campuran = ABORT.
Akhir baris (LF/CRLF) dipertahankan. Cadangan: manuscript/sn-article.tex.pre-newsec.bak.
Jalankan dari root repo:  python3 Patch/apply_new_results_sections.py
"""
import os, re, sys

P = os.path.join("manuscript", "sn-article.tex")
if not (os.path.isfile(P) and os.path.isdir(".git")):
    sys.exit("ABORT: jalankan dari root repo (harus ada .git dan manuscript/sn-article.tex)")

PAIRS = [('\\subsection{Prospective evaluation (E7): forward results}\\label{subsec:e7-results}',
  '\\subsection{Computational cost against flat ANFIS variants (E25)}\\label{subsec:e25}\n'
  'The introduction and H2 promise a cost comparison that the confirmatory protocol did not contain. We therefore measured, after the forward '
  'evaluation and without using any of its data, the training time, peak memory, single-row inference latency and batch throughput of the frozen '
  'E4-bis procedures of HANFIS, FlatANFISMatched and the full flat ANFIS. The protocol was written and tagged before the measurement '
  '(\\texttt{e25-protocol-2026-11-07}). The measurement ran once (five folds, three repetitions, the first frozen seed, one thread, CPU only, one '
  'mini PC under WSL~2) and is descriptive and unregistered. Table~\\ref{tab:flat-vs-hanfis} sets it beside the accuracy results of '
  'Section~\\ref{subssec4.3}; per-fold values are in Table~S9 of Additional file~1.\n'
  '\n'
  '\\begin{table}[ht]\n'
  '\\caption{HANFIS against the two flat ANFIS variants. The accuracy rows come from the confirmatory E4-bis comparison (registered for '
  'FlatANFISMatched, reported without criterion for the full model; the fold-0 row is post hoc). The cost rows are the unregistered E25 measurement '
  '(median of 15 runs, first frozen seed, one machine). Flat ANFIS variants were not part of the forward evaluation.}\\label{tab:flat-vs-hanfis}\n'
  '\\footnotesize\n'
  '\\setlength{\\tabcolsep}{4pt}\n'
  '\\begin{tabular}{@{}p{0.34\\linewidth}p{0.20\\linewidth}p{0.22\\linewidth}p{0.16\\linewidth}@{}}\n'
  '\\hline\n'
  ' & Flat ANFIS (full) & FlatANFISMatched & HANFIS\\\\\n'
  '\\hline\n'
  'Rules / parameters & 128 / 1{,}052 & 8 / 176 & 34 / 176\\\\\n'
  'Skill of HANFIS against the model & 0.253 (no criterion) & 0.665 [0.269, 0.844] (H2/H3) & ---\\\\\n'
  'The same without fold 0 (post hoc) & 0.084 & 0.183 & ---\\\\\n'
  'Range of held-out predictions & not reported & $-6.679$ to $11.059$ & $0.000$ to $10.401$\\\\\n'
  'Training time, median (s) & 7.30 & 0.95 & 8.51\\\\\n'
  'Peak memory increase, median (MiB) & 3.83 & 194.13 & 0.40\\\\\n'
  'Single-row latency, median ($\\mu$s) & 95.6 & 49.1 & 398.2\\\\\n'
  'Batch throughput, median (rows/s) & 264{,}865 & 2{,}456{,}989 & 388{,}665\\\\\n'
  '\\hline\n'
  '\\end{tabular}\n'
  '\\end{table}\n'
  '\n'
  'Relative to the full flat ANFIS, HANFIS has about six times fewer parameters ($176$ against $1{,}052$), its peak memory increase during training '
  'is about a tenth ($0.40$ against $3.83$~MiB, lower in all five folds), and its batch throughput is higher ($388{,}665$ against $264{,}865$ rows '
  'per second, higher in all five folds). It was not faster to train (median $8.51$ against $7.30$~s, lower in two of five folds), and its '
  'single-row latency was about four times higher ($398$ against $96$~$\\mu$s). FlatANFISMatched has the same parameter budget but trained about '
  'nine times faster ($0.95$~s) and answered about eight times faster per row ($49$~$\\mu$s); its memory increase was far larger and grew with the '
  'number of training rows ($5.5$ to $663$~MiB from fold 0 to fold 4), probably because of its cluster-radius search, which we did not test. The '
  'hierarchy therefore lowers parameters and peak training memory and raises batch throughput relative to the full flat model, but it does not '
  'reduce training time or single-row latency, and the part of H2 that promised those reductions is not supported.\n'
  '\n'
  'The measurement has limits. It uses one seed. HANFIS training time includes three restarts, whereas the full flat model is trained once with a '
  'different patience, so early stopping differs between models. Latency includes the conversion from NumPy to PyTorch and three unoptimised panel '
  'passes, a property of this implementation. Memory is a process-level peak with a resolution of about 1~MiB. The machine is not an edge device. '
  'Flat ANFIS variants were not part of the forward evaluation, so no forward comparison with them exists.\n'
  '\n'
  '\\subsection{Prospective evaluation (E7): forward results}\\label{subsec:e7-results}'),
 ('\\subsection{Horizon sweep and feature impact by horizon (E14)}\\label{subsec:e14}',
  '\\subsection{Threat-intelligence ablation (E26)}\\label{subsec:e26}\n'
  'H4 asks whether including the time-varying threat input improves prioritisation compared with an otherwise identical HANFIS without it. The '
  'registered protocols contain no test of H4, and E9 removes $x_2$ and $x_7$ together. After the forward evaluation we therefore ran the closest '
  'procedure (protocol \\texttt{e26-protocol-2026-11-07}; post hoc, descriptive, unregistered, no forward data): HANFIS was retrained with only '
  '$x_7$, the KEV indicator, set to zero, on the E4-bis folds, seeds, embargo and hyperparameters of E9. Without $x_7$ the pooled mean squared error '
  'rose from $0.41$ to $3.16$ (skill against the full model $-6.738$, 95\\% CI $-13.958$ to $-2.899$), in all five folds. The weekly ranking also '
  'fell: the Spearman correlation from $0.969$ to $0.889$ (difference $-0.080$, $-0.089$ to $-0.072$) and the precision at the top 20\\% from '
  '$0.973$ to $0.716$ ($-0.258$, $-0.307$ to $-0.204$). Without $x_7$, HANFIS still beat the CVSS-only baseline (skill $+0.748$, $+0.605$ to '
  '$+0.856$) but was far behind persistence ($-6.625$, $-19.375$ to $-2.492$). In the direction that H4 predicts, then, removing $x_7$ hurts. The '
  'reading is limited: $x_7$ is the KEV indicator, an ingredient of the label (Section~\\ref{subsec:e8}), so the result measures the dependence of '
  'the model on a label ingredient, not the value of $x_7$ as an independent threat signal, and H4 as registered remains untested.\n'
  '\n'
  '\\subsection{Trained rules and membership order (E27)}\\label{subsec:e27}\n'
  'To document the rule base we printed the 34 rules of one model fixed beforehand (fold 0, first frozen seed) with the accessors of the model '
  'itself (Tables~S11 to S13 of Additional file~1); the output of each panel rebuilt from these parameters equals the forward pass of the model on '
  '1{,}000 fixed rows. Figure~S4 of Additional file~1 shows the response of the five-seed ensemble of fold 0 over $(x_2,x_7)$: it rises smoothly in '
  'both inputs, and the response to $x_2$ saturates inside the observed range. The Gaussian centres are free parameters, and nothing forces them to '
  'keep the order of their index. In the documented model the centres of $x_2$, $v$ and $e$ are not in index order. Reading the parameters of all 25 '
  'saved models (an extension beyond the protocol, descriptive, no training), the centres are in increasing order for $x_1$, $x_3$, $x_4$, $x_5$ and '
  '$x_6$ in all 25 models, for $x_2$ in 24 and for $x_7$ in 20, but for the intermediate variables in only 8 models for $v$ and 17 for $e$. The '
  "names ``low, medium, high'' therefore cannot be read from the membership index of the intermediate variables in most trained models, although "
  'Section~\\ref{subsec:hanfis-architecture} chose three functions for them to keep that reading. The rule base is printable and its structure is '
  'fixed, but the meaning of its intermediate terms has to be recovered for each trained model.\n'
  '\n'
  '\\subsection{Horizon sweep and feature impact by horizon (E14)}\\label{subsec:e14}')]


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
with open(P + ".pre-newsec.bak", "wb") as f:
    f.write(raw)
with open(P, "wb") as f:
    f.write(out)
print("OK", len(PAIRS), "suntingan |", "CRLF" if crlf else "LF", "| cadangan", P + ".pre-newsec.bak")

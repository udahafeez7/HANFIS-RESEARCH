#!/usr/bin/env python3
"""apply_abstract_conclusion_ai_2026-11-11.py - abstrak <= 250 kata, penutup, H3, dan pernyataan penggunaan AI (11 November 2026).

Lapisan (P1): naskah (pelaporan). Dokumen: manuscript/sn-article.tex (sesudah apply_overleaf_merge_2026-11-11.py).
(1) Abstrak dipadatkan dari 271 ke <= 250 kata; angka 73.4% dan 83.3% dihapus dari abstrak (tetap ada di Section 3, baris 'reduces the rule
    count by 73.4% and the parameter count by 83.3%'); semua angka lain tetap. (2) H3: kalimat yang menafsirkan plateau flat ANFIS sebagai bukti
    mekanisme dihapus (audit klaim 7 November, baris 6). (3) Penutup: tiga kalimat diperbaiki agar tidak memakai pola 'not X but Y' dan agar
    klaim interpretabilitas selaras dengan Section E27. (4) Pernyataan AI di Methods dan Declarations ditulis ulang sesuai kebijakan Springer
    Nature (alat, versi, cakupan, tanggung jawab manusia); kalimat 'All experiments were run by the authors' dihapus karena tidak benar.
Teks-persis, gagal-tertutup: tiap teks lama harus cocok TEPAT SATU KALI (spasi dan baris baru dinormalkan) sebelum apa pun ditulis.
Idempoten: bila semua teks baru sudah terpasang, keluar 0 tanpa menulis. Keadaan campuran = ABORT.
Akhir baris (LF/CRLF) dipertahankan. Cadangan: manuscript/sn-article.tex.pre-absconcl.bak.
Jalankan dari root repo:  python3 Patch/apply_abstract_conclusion_ai_2026-11-11.py
"""
import os, re, sys

P = os.path.join("manuscript", "sn-article.tex")
if not (os.path.isfile(P) and os.path.isdir(".git")):
    sys.exit("ABORT: jalankan dari root repo (harus ada .git dan manuscript/sn-article.tex)")

ABS_OLD = (r"\abstract{Static, expert-weighted fuzzy risk scores go stale between elicitations, while a flat Adaptive Neuro-Fuzzy Inference System (ANFIS) over seven risk inputs requires 128 rules and 1{,}052 parameters. We built a hierarchical ANFIS (HANFIS) that separates vulnerability and environmental reasoning before an integration tier adds threat intelligence, reducing the model to 34 rules and 176 parameters (73.4\% and 83.3\% fewer), and we tested whether it earns that complexity against simple baselines. We build a temporal exploitability-exposure target from sealed weekly Exploit Prediction Scoring System (EPSS) and Known Exploited Vulnerabilities (KEV) snapshots for 120 container images (6{,}357 labelled asset-weeks), evaluated with grouped, embargoed splits. A 4-week persistence baseline lowers mean squared error relative to climatology by 97\%; a single Common Vulnerability Scoring System (CVSS) score, by 22\%. Under a protocol frozen before training, HANFIS reduces mean squared error by 96.7\% against CVSS, 69.6\% against a ridge model on all seven inputs and 66.5\% against a parameter-matched flat ANFIS (95\% bootstrap intervals excluding zero; the last margin comes largely from one fold), but is not distinguishable from persistence. Post hoc analyses qualify these gains. Exact Shapley attribution puts 78.9\% on exploitability and the KEV indicator, ingredients of the label, and without them HANFIS has no skill over CVSS (skill $-0.14$, interval $-0.34$ to $0.05$). A four-parameter formula of those two inputs, $100\max(x_2,0.1\,x_7)$, has a lower error than HANFIS at four weeks (skill $-0.53$, interval $-1.44$ to $-0.21$). In a pre-registered forward evaluation, the formula beat persistence and HANFIS did not beat the formula. On this target HANFIS adds a printable rule base but no accuracy, and the data cannot show whether environmental context helps.}")
ABS_NEW = (r"\abstract{Static, expert-weighted fuzzy risk scores go stale between elicitations, and a flat Adaptive Neuro-Fuzzy Inference System (ANFIS) over seven risk inputs needs 128 rules and 1{,}052 parameters. We built a hierarchical ANFIS (HANFIS) that separates vulnerability and environmental reasoning before an integration tier adds threat intelligence (34 rules, 176 parameters) and tested it against simple baselines. The target is exploitability exposure from sealed weekly Exploit Prediction Scoring System (EPSS) and Known Exploited Vulnerabilities (KEV) snapshots for 120 container images (6{,}357 labelled asset-weeks), evaluated with grouped, embargoed splits. A 4-week persistence baseline lowers mean squared error relative to climatology by 97\%; a single Common Vulnerability Scoring System (CVSS) score, by 22\%. Under a protocol frozen before training, HANFIS reduces error by 96.7\% against CVSS, 69.6\% against a ridge model on all seven inputs and 66.5\% against a parameter-matched flat ANFIS (95\% bootstrap intervals excluding zero; the last margin comes largely from one fold), and it is not distinguishable from persistence. Post hoc analyses narrow these gains. Exact Shapley attribution puts 78.9\% on exploitability and the KEV indicator, both label ingredients; without them HANFIS has no skill over CVSS (skill $-0.14$, interval $-0.34$ to $0.05$). A four-parameter formula of those two inputs, $100\max(x_2,0.1\,x_7)$, beats HANFIS at four weeks (skill $-0.53$, interval $-1.44$ to $-0.21$). In a pre-registered forward evaluation the formula beat persistence and HANFIS did not. On this target HANFIS offers a printable rule base and no gain in accuracy, and the data cannot show whether environmental context helps.}")

PAIRS = [
 (ABS_OLD, ABS_NEW),
 (r"within a prespecified margin, despite the reduction in rule-base complexity. A flat ANFIS's plateau below the full-capacity reference is treated as evidence for the mechanism this decomposition trades away (cross-subsystem interaction discarded by the scalar inter-tier bottleneck) rather than as a falsification of H2/H3 by itself.",
  r"within a prespecified margin, despite the reduced rule-base complexity."),
 (r"so it is read as suggestive of a structural advantage of the vulnerability/environmental/threat decomposition, not as evidence for one (Section~\ref{subssec4.5}).",
  r"so it is read as suggestive of a structural advantage of the vulnerability/environmental/threat decomposition and is not evidence for one (Section~\ref{subssec4.5})."),
 (r"On this target HANFIS therefore provides a compact rule base with a documented response surface, not better accuracy than a simple formula at the four-week horizon. Its intermediate variables do not keep a stable linguistic meaning across trained models (Section~\ref{subsec:e27}).",
  r"On this target HANFIS therefore provides a compact rule base with a documented response surface, while its four-week accuracy stays below that of a simple formula. Its intermediate variables do not keep a stable linguistic meaning across trained models (Section~\ref{subsec:e27})."),
 (r"the accuracy of HANFIS on this task is bounded by a simple formula; its value lies in structure and interpretability.",
  r"the accuracy of HANFIS on this task is bounded by a simple formula, and what the model adds is a printable structure."),
 (r"\subsection*{Use of AI tools}" "\n"
  r"An AI assistant (Claude, Anthropic) was used to help write and test analysis and utility code, to draft and revise manuscript text, and to review study protocols. All experiments were run by the authors, who verified the code and the results, reviewed and edited all text, and take full responsibility for the content; the assistant is not an author (see Declarations).",
  r"\subsection*{Use of AI tools}" "\n"
  r"An AI assistant (Claude, Anthropic; the Claude Sonnet 5.5, Claude Opus 5.5 and Claude Fable 5.1 models, used through the Claude Code environment during 2026) helped to write and test analysis and utility code, to draft the two unregistered protocols (Sections~\ref{subsec:e25} and~\ref{subsec:e26}), to run scripts at the authors' direction, including the stages of the forward evaluation on the pre-registered date, to draft and revise manuscript text, including first drafts of parts of the Results and Discussion, and to check the reference list against doi.org. The authors decided every protocol, hypothesis and claim before the corresponding run, verified the code, the results and the references, reviewed and edited all text, and take full responsibility for the content. The assistant is not an author (see Declarations)."),
 (r"\item \textbf{Use of AI tools.} During the preparation of this work the authors used an AI assistant (Claude, Anthropic) to help write and test analysis and utility code, to draft and revise manuscript text, and to review study protocols. The authors ran and verified all code and results, reviewed and edited all text, and take full responsibility for the content of the publication.",
  r"\item \textbf{Use of AI tools.} During the preparation of this work the authors used an AI assistant (Claude, Anthropic; Claude Sonnet 5.5, Claude Opus 5.5 and Claude Fable 5.1 models, 2026) to help write and test code, to draft the two unregistered protocols, to run scripts at the authors' direction, to draft and revise manuscript text, and to check references. The authors decided every protocol and claim, verified all code, results and references, reviewed and edited all text, and take full responsibility for the content of the publication. The assistant is not an author."),
]


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
with open(P + ".pre-absconcl.bak", "wb") as f:
    f.write(raw)
with open(P, "wb") as f:
    f.write(out)
print("OK", len(PAIRS), "suntingan |", "CRLF" if crlf else "LF", "| cadangan", P + ".pre-absconcl.bak")

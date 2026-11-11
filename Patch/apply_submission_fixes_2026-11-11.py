#!/usr/bin/env python3
r"""apply_submission_fixes_2026-11-11.py - temuan A.1, A.3, A.4, A.5, A.8 dari penilaian 11 November 2026.

Lapisan (P1): naskah (pelaporan). Dokumen: manuscript/sn-article.tex, manuscript/sn-bibliography.bib.
A.1 gerbang data: kode (python_hanfis/asset_weeks.py:444) memasang 1.320 baris = 10 x 132 parameter (konfigurasi m_I=2 sebelum A-02;
    diverifikasi HANFIS(m_intermediate=2) = 132 parameter); untuk 176 parameter ambang setara 1.760; inventori 6.833 baris melewati keduanya.
A.3 kata kunci: tambah 'Hierarchical fuzzy systems', 'Pre-registered evaluation', 'Negative result'; judul tidak diubah.
A.4 bagian 'Additional files' sebelum Declarations (format SpringerOpen: nama, format, judul, deskripsi). Isi S1 sampai S17, Figure S1 sampai S5,
    Note S1 sampai S11 mengandaikan apply_condense_2026-11-11.py dijalankan sesudahnya.
A.5 URL OSF di teks (dua tempat) menjadi \cite{osf_ahcvs}; entri bib @misc ditambahkan; janji 'a Zenodo version DOI will be added' dihapus.
A.8 'All authors read and approved the final manuscript.' di Authors' contributions.
Teks-persis, gagal-tertutup; idempoten; CRLF dipertahankan; cadangan .pre-subfix.bak. Jalankan dari root repo:
  python3 Patch/apply_submission_fixes_2026-11-11.py
"""
import os, re, sys

P = os.path.join("manuscript", "sn-article.tex"); B = os.path.join("manuscript", "sn-bibliography.bib")
if not (os.path.isfile(P) and os.path.isfile(B) and os.path.isdir(".git")):
    sys.exit("ABORT: jalankan dari root repo")

PAIRS = [
 (r"This clears the pre-registered data-quality gate: protocol frozen and dated; $\ge 10$ observations per model parameter, i.e.\ $\ge 1{,}320$ rows for the 176-parameter configuration; no leakage across the split described below; and every mandatory baseline runnable on the pilot.",
  r"This clears the pre-registered data-quality gate: protocol frozen and dated; at least ten observations per model parameter (the gate is coded as $\ge 1{,}320$ rows, which is ten times the 132 parameters of the configuration with $m_I=2$ that preceded the frozen $m_I=3$ setting; the same rule gives $\ge 1{,}760$ rows for the 176-parameter configuration, and the inventory clears both); no leakage across the split described below; and every mandatory baseline runnable on the pilot."),
 (r"\keywords{Adaptive Neuro-Fuzzy Inference System, Exploit prediction, Security Risk Assessment, Container Orchestration, Cloud-Native Security}",
  r"\keywords{Adaptive Neuro-Fuzzy Inference System, Hierarchical fuzzy systems, Exploit prediction, Container security, Kubernetes, Pre-registered evaluation, Negative result}"),
 (r"The protocol was also registered on the Open Science Framework before any forward label was computed (registration date 2026-10-13; \texttt{https://osf.io/ahcvs/}; DOI \texttt{10.17605/OSF.IO/AHCVS}).",
  r"The protocol was also registered on the Open Science Framework before any forward label was computed (registration date 2026-10-13)~\cite{osf_ahcvs}."),
 (r"and registered on the Open Science Framework (\texttt{https://osf.io/ahcvs/}; DOI \texttt{10.17605/OSF.IO/AHCVS}); the forward outputs are tagged \texttt{e7-results-2026-11-02}, and a Zenodo version DOI will be added.",
  r"and registered on the Open Science Framework~\cite{osf_ahcvs}; the forward outputs are tagged \texttt{e7-results-2026-11-02}."),
 (r"B.R.: supervision, contribution to the design of the experimental platform (cluster and telemetry network), methodology review, writing -- review and editing.",
  r"B.R.: supervision, contribution to the design of the experimental platform (cluster and telemetry network), methodology review, writing -- review and editing. All authors read and approved the final manuscript."),
 ("\\section*{Declarations}\n\n\\begin{itemize}\n\\item \\textbf{Funding.}",
  "\\section*{Additional files}\n\n\\begin{itemize}\n\\item \\textbf{Additional file 1.} Format: PDF. Title: Supplementary tables, figures and notes. Description: Tables S1 to S17 (acceptance gates of the testbed, the membership-family ablation, the EPSS-change sensitivity run, explanation-fidelity checks, ranking utility, input-change strata, calibration, forward-evaluation details, the trained rule base of one model, the observability-overhead measurements, the horizon sweep, the error anatomy by EPSS model change, and the map from experiment and amendment codes to sections); Figures S1 to S5 (methodology overview, baseline and skill-score plots, the response surface of one trained model, and the bottleneck-width curve); Supplementary notes S1 to S11 (full text of the sections that the main text condenses: testbed and observability-overhead protocol with its validity safeguards, ablation details, explanation fidelity, ranking utility, error anatomy, calibration and stacking, data caveats, the horizon sweep and the accuracy-complexity sweep).\n\\end{itemize}\n\n\\section*{Declarations}\n\n\\begin{itemize}\n\\item \\textbf{Funding.}"),
]
BIB_ANCHOR = "@article{holm1979simple,"
BIB_NEW = ("@misc{osf_ahcvs,\n  author = {Hersyah, Mohammad Hafiz and Derisma, Derisma and Rahmadya, Budi},\n"
           "  title = {{HANFIS} forward evaluation ({E7}): pre-registered protocol},\n  howpublished = {Open Science Framework registration},\n"
           "  year = {2026},\n  doi = {10.17605/OSF.IO/AHCVS},\n  note = {Registered 13 October 2026; accessed 11 November 2026}\n}\n\n")


def rx(text):
    return re.compile(r"\s+".join(re.escape(t) for t in text.split()))


def load(p):
    raw = open(p, "rb").read(); return raw, b"\r\n" in raw, raw.decode("utf-8").replace("\r\n", "\n")


raw, crlf, s = load(P); braw, bcrlf, bs = load(B)
nrm = lambda z: " ".join(z.split())
state = []
for n, (old, new) in enumerate(PAIRS, 1):
    co, cn = len(rx(old).findall(s)), len(rx(new).findall(s))
    if co == 1 and cn == 0: state.append("old")
    elif cn >= 1 and (co == 0 or nrm(old) in nrm(new)): state.append("new")
    else: sys.exit(f"ABORT: pasangan {n}: teks lama cocok {co} kali, teks baru {cn} kali; tidak ada yang ditulis")
state.append("new" if "@misc{osf_ahcvs," in bs else ("old" if bs.count(BIB_ANCHOR) == 1 else sys.exit("ABORT: jangkar bib tidak unik")))
if all(x == "new" for x in state):
    print("SUDAH TERPASANG: semua", len(PAIRS) + 1, "suntingan; tidak ada yang ditulis"); sys.exit(0)
if any(x == "new" for x in state):
    sys.exit("ABORT: keadaan campuran; tidak ada yang ditulis")
for n, (old, new) in enumerate(PAIRS, 1):
    s, k = rx(old).subn(lambda m, new=new: new, s, count=1)
    if k != 1: sys.exit(f"ABORT: pasangan {n} gagal; tidak ada yang ditulis")
bs = bs.replace(BIB_ANCHOR, BIB_NEW + BIB_ANCHOR, 1)
for p, r0, c, txt, tag in ((P, raw, crlf, s, "subfix"), (B, braw, bcrlf, bs, "subfix")):
    open(p + f".pre-{tag}.bak", "wb").write(r0); open(p, "wb").write((txt.replace("\n", "\r\n") if c else txt).encode("utf-8"))
print("OK", len(PAIRS), "suntingan naskah + 1 entri bib |", "CRLF" if crlf else "LF")

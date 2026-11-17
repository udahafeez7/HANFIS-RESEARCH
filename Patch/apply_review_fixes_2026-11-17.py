#!/usr/bin/env python3
r"""apply_review_fixes_2026-11-17.py - perbaikan dari penilaian PDF Overleaf (17 November 2026).

Lapisan (P1): naskah (pelaporan). Dokumen: manuscript/sn-article.tex, manuscript/additional_file_1.tex, scripts/fig_e5_rule_growth.py.
(1) Availability: rujukan 'Sections 4.15 to 4.10' (urutan terbalik) menjadi tiga rujukan bernama (E25, E26, E27).
(2) Bagian 5.1: titik koma sebelum huruf besar ('persistence; The H2/H3') menjadi titik.
(3) Bagian 3.4: satu kalimat yang menjelaskan 6.833 baris lawan 6.357 baris berlabel (476 baris = 4 minggu terakhir, 2026-08-31 sampai 2026-09-21,
    119 kelompok image per minggu, tanpa label karena jendela label melewati snapshot tersegel terakhir; diverifikasi dari tabel asset_weeks_v2_120assets_e4bis.csv).
(4) Gaya sitasi author-year: \cite (tekstual) menjadi \citep (dalam kurung) kecuali empat tempat khusus: \citet (HANFIS of Soozanchi-K. et al.;
    'argument of Raju et al.; Wang'), \citealp di dalam kurung yang sudah ada (aritmetika Raju/Wang di C2; tumpukan observabilitas Prometheus).
    Hasil: 51 \cite di naskah dan 2 di Additional file 1 menjadi \citep; tidak ada kunci sitasi yang berubah.
(5) Figure 2: label 'refused' dipindah ke bawah kedua garis (skrip pembuat gambar).
Teks-persis, gagal-tertutup; idempoten; CRLF dipertahankan; cadangan .pre-reviewfix.bak. Jalankan dari root repo:  python3 Patch/apply_review_fixes_2026-11-17.py
"""
import os, re, sys

P = os.path.join("manuscript", "sn-article.tex"); A = os.path.join("manuscript", "additional_file_1.tex"); G = os.path.join("scripts", "fig_e5_rule_growth.py")
if not (os.path.isfile(P) and os.path.isfile(A) and os.path.isfile(G) and os.path.isdir(".git")):
    sys.exit("ABORT: jalankan dari root repo")

PAIRS = [
 (r"the results of the computational-cost measurement and of the two post hoc analyses of Sections~\ref{subsec:e25} to~\ref{subsec:e27}, Additional file~1,",
  r"the results of the computational-cost measurement (Section~\ref{subsec:e25}), of the threat-intelligence ablation (Section~\ref{subsec:e26}) and of the rule documentation (Section~\ref{subsec:e27}), Additional file~1,"),
 (r"which are also those in which HANFIS is furthest behind persistence; The H2/H3 pooled margin",
  r"which are also those in which HANFIS is furthest behind persistence. The H2/H3 pooled margin"),
 (r"the non-missing rate is 0.93, and no row is left in an unresolved evidence state. This clears",
  r"the non-missing rate is 0.93, and no row is left in an unresolved evidence state. Of these rows, 6{,}357 carry a label; the other 476 (119 image groups in each of the weeks 2026-08-31 to 2026-09-21) are feature-only, because their label window extends beyond the last sealed snapshot. This clears"),
 (r"Unlike the speaker-verification HANFIS of~\cite{soozanchi2010hanfis}, its three tiers",
  r"Unlike the speaker-verification HANFIS of~\citet{soozanchi2010hanfis}, its three tiers"),
 (r"(the arithmetic of hierarchical fuzzy systems~\cite{raju1991,wang1998hierarchical}), accompanied",
  r"(the arithmetic of hierarchical fuzzy systems~\citealp{raju1991,wang1998hierarchical}), accompanied"),
 (r"keeps the hierarchy argument of~\cite{raju1991,wang1998hierarchical} and evaluates",
  r"keeps the hierarchy argument of~\citet{raju1991,wang1998hierarchical} and evaluates"),
 (r"The observability stack (Prometheus~\cite{prometheus_overview}, Prometheus Operator, kube-state-metrics and node-exporter) ran",
  r"The observability stack (Prometheus, Prometheus Operator, kube-state-metrics and node-exporter; \citealp{prometheus_overview}) ran"),
]
N_BULK = {P: 51, A: 2}   # \cite{ restantes setelah empat tempat khusus (naskah) dan seluruhnya (AF1)
G_PAIRS = [('ax.text(sum(refused) / len(refused), 3e4, f"refused\\n(>{MAX_PARAMS:,}-param\\nbudget)", ha="center", va="center", color="#c0392b", fontsize=9)',
            'ax.text(3.45, 2.5e2, f"refused\\n(>{MAX_PARAMS:,}-param\\nbudget)", ha="center", va="center", color="#c0392b", fontsize=9)')]


def rx(text):
    return re.compile(r"\s+".join(re.escape(t) for t in text.split()))


def load(p):
    raw = open(p, "rb").read(); return raw, b"\r\n" in raw, raw.decode("utf-8").replace("\r\n", "\n")


nrm = lambda z: " ".join(z.split())
raw, crlf, s = load(P); araw, acrlf, a = load(A); graw, gcrlf, g = load(G)
state = []
for n, (old, new) in enumerate(PAIRS, 1):
    co, cn = len(rx(old).findall(s)), len(rx(new).findall(s))
    if co == 1 and cn == 0: state.append("old")
    elif cn >= 1 and (co == 0 or nrm(old) in nrm(new)): state.append("new")
    else: sys.exit(f"ABORT: pasangan {n}: teks lama cocok {co} kali, teks baru {cn} kali; tidak ada yang ditulis")
for old, new in G_PAIRS:
    co, cn = g.count(old), g.count(new)
    if co == 1 and cn == 0: state.append("old")
    elif cn == 1 and co == 0: state.append("new")
    else: sys.exit("ABORT: jangkar skrip gambar tidak unik; tidak ada yang ditulis")
bulk = {p: len(re.findall(r"\\cite\{", t)) for p, t in ((P, s), (A, a))}
if all(x == "new" for x in state) and all(v == 0 for v in bulk.values()):
    print("SUDAH TERPASANG; tidak ada yang ditulis"); sys.exit(0)
if any(x == "new" for x in state):
    sys.exit("ABORT: keadaan campuran; tidak ada yang ditulis")
# pasangan 1 dan 2 saling bergantung (dua langkah pada kalimat yang sama): terapkan berurutan
for n, (old, new) in enumerate(PAIRS, 1):
    s, k = rx(old).subn(lambda m, new=new: new, s, count=1)
    if k != 1: sys.exit(f"ABORT: pasangan {n} gagal; tidak ada yang ditulis")
left_p, left_a = len(re.findall(r"\\cite\{", s)), len(re.findall(r"\\cite\{", a))
if (left_p, left_a) != (N_BULK[P], N_BULK[A]):
    sys.exit("ABORT: jumlah cite tak terduga (naskah %d, AF1 %d); tidak ada yang ditulis" % (left_p, left_a))
s = re.sub(r"\\cite\{", lambda m: r"\citep{", s); a = re.sub(r"\\cite\{", lambda m: r"\citep{", a)
for old, new in G_PAIRS:
    g = g.replace(old, new, 1)
for p, r0, c, t in ((P, raw, crlf, s), (A, araw, acrlf, a), (G, graw, gcrlf, g)):
    open(p + ".pre-reviewfix.bak", "wb").write(r0); open(p, "wb").write((t.replace("\n", "\r\n") if c else t).encode("utf-8"))
print("OK", len(PAIRS), "suntingan teks +", N_BULK[P], "dan", N_BULK[A], "\\cite -> \\citep + label Figure 2 |", "CRLF" if crlf else "LF")

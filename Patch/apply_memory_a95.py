#!/usr/bin/env python3
"""apply_memory_a95.py - patch HANFIS_RESEARCH_MEMORY.md dari v2.74 ke v2.75 (2026-11-13).

Menambah A-89: perbaikan temuan kirim (gerbang 1.320, Additional files, OSF ke bib, pernyataan persetujuan penulis, kata kunci) dan pemadatan
C.1 sampai C.7 (61 ke 54 halaman). Lapisan (P1): pelaporan naskah. Dokumen: HANFIS_RESEARCH_MEMORY.md.
Teks-persis, gagal-tertutup; idempoten; CRLF dipertahankan; cadangan .pre-a95.bak. Jalankan dari root repo:  python3 Patch/apply_memory_a95.py
"""
import os, sys

MEM = "HANFIS_RESEARCH_MEMORY.md"
if not (os.path.isfile(MEM) and os.path.isdir(".git")):
    sys.exit("ABORT: jalankan dari root repo")
OLD_HEAD = "> Versi: 2.74 · Tanggal: 2026-11-13 ·"
NEW_HEAD = "> Versi: 2.75 · Tanggal: 2026-11-13 ·"
A89 = (
"| A-95 | 2026-11-13 | Pemeriksaan akhir sebelum kirim: gerbang, bibliografi, angka abstrak (lanjutan A-94) | "
"(1) Gerbang 2026-11-13: pytest 126 passed, 11 subtests; `verify_prereg_tag.py e7-prereg-2026-10-12` + 23 berkas dari freeze record LOLOS (identik dengan berkas kerja); `e7_d2.py --dry-run` STATUS=E7_D2_DRY_RUN. "
"(2) Bibliografi (43 entri, berkas Downloads = repo): 35 OK, 6 tanpa DOI (Trivy, KEV, CVSS 4.0, Holm, Kubernetes, Prometheus; diperiksa manual sebelumnya), 2 PERIKSA: brown1995curse (tanggal rekaman IEEE Xplore, entri benar) dan osf_ahcvs (judul bib berbeda dari judul registrasi). Deep audit: dua catatan booktitle/series, bukan kesalahan. Semua kunci yang disitasi ada di bib dan tidak ada entri yang tidak disitasi. Log: 0 undefined, 0 peringatan bibtex di kedua dokumen; peringatan multiply defined di AF1 hanya efek xr-hyper (dikenal, jinak). "
"(3) `Patch/apply_final_checks_2026-11-13.py` (diuji di salinan): abstrak memakai tiga desimal persis Table tab:e9 (-0.135, [-0.336, 0.046]; -0.534, [-1.438, -0.208]) menggantikan pembulatan dua desimal yang tidak ada di tabel; judul entri osf_ahcvs disamakan dengan registrasi ('HANFIS prospective evaluation (E7)'). Abstrak tetap 248 kata; PDF 51 halaman. "
"Angka abstrak yang tersisa tanpa padanan huruf demi huruf: 96.7%, 69.6%, 66.5% = skill score 0.967, 0.696, 0.665 di Table tab:e4-results (konversi persen, dapat dilacak). Berkas sn-article.tex dan sn-bibliography.bib berubah; Overleaf perlu diunggah ulang (dua berkas). Terbuka: pembacaan utuh oleh penulis; tag pengiriman. |"
)
raw = open(MEM, "rb").read(); crlf = b"\r\n" in raw; s = raw.decode("utf-8").replace("\r\n", "\n"); nl = "\r\n" if crlf else "\n"
if NEW_HEAD in s and s.count("| A-95 |") == 1 and A89 in s:
    print("SUDAH TERPASANG: v2.75 (A-95)"); sys.exit(0)
if "| A-95 |" in s: sys.exit("ABORT: A-95 sudah ada dengan isi lain")
if s.count(OLD_HEAD) != 1: sys.exit("ABORT: kepala v2.74 tidak unik")
lines = s.split("\n"); idx = [i for i, l in enumerate(lines) if l.startswith("| A-94 |")]
if len(idx) != 1 or (idx[0] + 1 < len(lines) and lines[idx[0] + 1].startswith("|")): sys.exit("ABORT: A-94 bukan baris terakhir tabel")
lines = s.replace(OLD_HEAD, NEW_HEAD).split("\n"); lines.insert(idx[0] + 1, A89)
open(MEM + ".pre-a95.bak", "wb").write(raw); open(MEM, "wb").write(nl.join(lines).encode("utf-8")); print("OK v2.75 (A-95)")

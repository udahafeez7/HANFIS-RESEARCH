#!/usr/bin/env python3
"""apply_memory_a94.py - patch HANFIS_RESEARCH_MEMORY.md dari v2.73 ke v2.74 (2026-11-13).

Menambah A-89: perbaikan temuan kirim (gerbang 1.320, Additional files, OSF ke bib, pernyataan persetujuan penulis, kata kunci) dan pemadatan
C.1 sampai C.7 (61 ke 54 halaman). Lapisan (P1): pelaporan naskah. Dokumen: HANFIS_RESEARCH_MEMORY.md.
Teks-persis, gagal-tertutup; idempoten; CRLF dipertahankan; cadangan .pre-a94.bak. Jalankan dari root repo:  python3 Patch/apply_memory_a94.py
"""
import os, sys

MEM = "HANFIS_RESEARCH_MEMORY.md"
if not (os.path.isfile(MEM) and os.path.isdir(".git")):
    sys.exit("ABORT: jalankan dari root repo")
OLD_HEAD = "> Versi: 2.73 · Tanggal: 2026-11-13 ·"
NEW_HEAD = "> Versi: 2.74 · Tanggal: 2026-11-13 ·"
A89 = (
"| A-94 | 2026-11-13 | Zenodo v2.0 terbit; CITATION.cff dan README (lanjutan A-93) | "
"(1) Peneliti menekan Publish pada 2026-11-13: https://doi.org/10.5281/zenodo.24133609 membalas HTTP 200; API rekaman memuat v2.0, tanggal publikasi 2026-11-11 (diwarisi dari draf), lima berkas (`HANFIS-RESEARCH_4d82bea_code.zip`, `HANFIS_results_models_2026-11-11.tar.gz`, `HANFIS_asset_week_tables_2026-11-13.tar.gz`, `Additional_file_1.pdf`, `SHA256SUMS.txt`). DOI semua versi tetap 10.5281/zenodo.23357117; v1.0 10.5281/zenodo.23357118. Berkas rekaman tidak dapat diubah lagi; perubahan berikutnya lewat versi baru. "
"(2) `Patch/apply_citation_zenodo_v2_2026-11-13.py` (diuji di salinan): CITATION.cff (version v2.0, date-released 2026-11-11, doi 24133609, judul sesuai rekaman) dan README (status publik, DOI v2) diperbarui; CITATION.cff valid saat diparse. "
"(3) Naskah (Availability, Code availability) sudah memuat DOI 24133609 dan naskah di Overleaf 51 halaman sama dengan kompilasi lokal. Terbuka: pembacaan utuh oleh penulis; keputusan cabang bawaan GitHub (saat ini research/hanfis-private-publish-20260921, bukan research/amend-a02-a06); token Zenodo harus dihapus peneliti (berkas lokal sudah tidak ada). |"
)
raw = open(MEM, "rb").read(); crlf = b"\r\n" in raw; s = raw.decode("utf-8").replace("\r\n", "\n"); nl = "\r\n" if crlf else "\n"
if NEW_HEAD in s and s.count("| A-94 |") == 1 and A89 in s:
    print("SUDAH TERPASANG: v2.74 (A-94)"); sys.exit(0)
if "| A-94 |" in s: sys.exit("ABORT: A-94 sudah ada dengan isi lain")
if s.count(OLD_HEAD) != 1: sys.exit("ABORT: kepala v2.73 tidak unik")
lines = s.split("\n"); idx = [i for i, l in enumerate(lines) if l.startswith("| A-93 |")]
if len(idx) != 1 or (idx[0] + 1 < len(lines) and lines[idx[0] + 1].startswith("|")): sys.exit("ABORT: A-93 bukan baris terakhir tabel")
lines = s.replace(OLD_HEAD, NEW_HEAD).split("\n"); lines.insert(idx[0] + 1, A89)
open(MEM + ".pre-a94.bak", "wb").write(raw); open(MEM, "wb").write(nl.join(lines).encode("utf-8")); print("OK v2.74 (A-94)")

#!/usr/bin/env python3
"""apply_memory_a93.py - patch HANFIS_RESEARCH_MEMORY.md dari v2.72 ke v2.73 (2026-11-13).

Menambah A-89: perbaikan temuan kirim (gerbang 1.320, Additional files, OSF ke bib, pernyataan persetujuan penulis, kata kunci) dan pemadatan
C.1 sampai C.7 (61 ke 54 halaman). Lapisan (P1): pelaporan naskah. Dokumen: HANFIS_RESEARCH_MEMORY.md.
Teks-persis, gagal-tertutup; idempoten; CRLF dipertahankan; cadangan .pre-a93.bak. Jalankan dari root repo:  python3 Patch/apply_memory_a93.py
"""
import os, sys

MEM = "HANFIS_RESEARCH_MEMORY.md"
if not (os.path.isfile(MEM) and os.path.isdir(".git")):
    sys.exit("ABORT: jalankan dari root repo")
OLD_HEAD = "> Versi: 2.72 · Tanggal: 2026-11-13 ·"
NEW_HEAD = "> Versi: 2.73 · Tanggal: 2026-11-13 ·"
A89 = (
"| A-93 | 2026-11-13 | Zenodo v2: tabel asset-week ditambahkan; repositori publik terverifikasi (lanjutan A-92) | "
"(1) Keputusan peneliti 2026-11-13: tabel asset-week turunan boleh diunggah. `HANFIS_asset_week_tables_2026-11-13.tar.gz` (2,2 MB, 39 berkas dari data/processed, md5 91ba7e5a683feb4446325e90837c6267) diunggah ke draf 24133609; `SHA256SUMS.txt` diganti (empat berkas, md5 93e32d51d0e1c6e5670d9d1e77f7fd28); deskripsi draf diperbarui. Draf masih unsubmitted. "
"(2) Repositori GitHub udahafeez7/HANFIS-RESEARCH terverifikasi publik tanpa login (HTTP 200, private false). Catatan: cabang bawaan di GitHub adalah research/hanfis-private-publish-20260921, bukan research/amend-a02-a06 yang berisi naskah terbaru; pembaca yang membuka repo mendarat di cabang lama. "
"(3) `Patch/apply_availability_assetweeks_2026-11-13.py`: Availability menyebut tabel asset-week sebagai bagian arsip. PDF 51 halaman, 0 peringatan bibtex. Terbuka: peneliti memeriksa draf lalu menekan Publish; sesudahnya hapus token Zenodo dan ~/.zenodo_token; CITATION.cff dan README diperbarui; cabang bawaan GitHub diputuskan peneliti. |"
)
raw = open(MEM, "rb").read(); crlf = b"\r\n" in raw; s = raw.decode("utf-8").replace("\r\n", "\n"); nl = "\r\n" if crlf else "\n"
if NEW_HEAD in s and s.count("| A-93 |") == 1 and A89 in s:
    print("SUDAH TERPASANG: v2.73 (A-93)"); sys.exit(0)
if "| A-93 |" in s: sys.exit("ABORT: A-93 sudah ada dengan isi lain")
if s.count(OLD_HEAD) != 1: sys.exit("ABORT: kepala v2.72 tidak unik")
lines = s.split("\n"); idx = [i for i, l in enumerate(lines) if l.startswith("| A-92 |")]
if len(idx) != 1 or (idx[0] + 1 < len(lines) and lines[idx[0] + 1].startswith("|")): sys.exit("ABORT: A-92 bukan baris terakhir tabel")
lines = s.replace(OLD_HEAD, NEW_HEAD).split("\n"); lines.insert(idx[0] + 1, A89)
open(MEM + ".pre-a93.bak", "wb").write(raw); open(MEM, "wb").write(nl.join(lines).encode("utf-8")); print("OK v2.73 (A-93)")

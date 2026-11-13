#!/usr/bin/env python3
"""apply_memory_a96.py - patch HANFIS_RESEARCH_MEMORY.md dari v2.75 ke v2.76 (2026-11-13).

Menambah A-89: perbaikan temuan kirim (gerbang 1.320, Additional files, OSF ke bib, pernyataan persetujuan penulis, kata kunci) dan pemadatan
C.1 sampai C.7 (61 ke 54 halaman). Lapisan (P1): pelaporan naskah. Dokumen: HANFIS_RESEARCH_MEMORY.md.
Teks-persis, gagal-tertutup; idempoten; CRLF dipertahankan; cadangan .pre-a96.bak. Jalankan dari root repo:  python3 Patch/apply_memory_a96.py
"""
import os, sys

MEM = "HANFIS_RESEARCH_MEMORY.md"
if not (os.path.isfile(MEM) and os.path.isdir(".git")):
    sys.exit("ABORT: jalankan dari root repo")
OLD_HEAD = "> Versi: 2.75 · Tanggal: 2026-11-13 ·"
NEW_HEAD = "> Versi: 2.76 · Tanggal: 2026-11-13 ·"
A89 = (
"| A-96 | 2026-11-13 | Tag pengiriman dan cover letter (lanjutan A-95) | "
"(1) `Patch/apply_submission_tag_2026-11-13.py` (diuji di salinan): Code availability menyebut tag `manuscript-submission-2026-11` sebagai penanda versi yang dikirim. Tag anotasi dibuat pada komit yang memuat suntingan ini dan memuat baris A-96 ini (komit akhir naskah); riwayat sesudahnya tidak mengubah naskah tanpa tag baru. PDF 51 halaman, 0 peringatan bibtex. "
"(2) Cover letter: `docs/progress/cover_letter_2026-11-13.docx` (Word, 643 kata, bahasa Inggris, untuk editor Journal of Cloud Computing). Isi memakai hanya angka naskah: 34/176 lawan 128/1.052, 120 image, 6.357 asset-week, persistence 97%, 96.7/69.6/66.5%, Shapley 78.9%, evaluasi maju P7e skill 0.340 [0.060, 0.628]; DOI Zenodo 24133609, OSF AHCVS, repositori publik; pengungkapan AI; pendanaan. Pernyataan 'not under consideration elsewhere' dan 'authors declare no competing interests' mengikuti naskah; penulis harus memastikan yang pertama benar saat kirim. Daftar reviewer usulan tidak ditulis (tidak ada nama dari peneliti; tidak diarang). Terbuka: pembacaan utuh oleh penulis; unggah ulang sn-article.tex ke Overleaf (kalimat tag). |"
)
raw = open(MEM, "rb").read(); crlf = b"\r\n" in raw; s = raw.decode("utf-8").replace("\r\n", "\n"); nl = "\r\n" if crlf else "\n"
if NEW_HEAD in s and s.count("| A-96 |") == 1 and A89 in s:
    print("SUDAH TERPASANG: v2.76 (A-96)"); sys.exit(0)
if "| A-96 |" in s: sys.exit("ABORT: A-96 sudah ada dengan isi lain")
if s.count(OLD_HEAD) != 1: sys.exit("ABORT: kepala v2.75 tidak unik")
lines = s.split("\n"); idx = [i for i, l in enumerate(lines) if l.startswith("| A-95 |")]
if len(idx) != 1 or (idx[0] + 1 < len(lines) and lines[idx[0] + 1].startswith("|")): sys.exit("ABORT: A-95 bukan baris terakhir tabel")
lines = s.replace(OLD_HEAD, NEW_HEAD).split("\n"); lines.insert(idx[0] + 1, A89)
open(MEM + ".pre-a96.bak", "wb").write(raw); open(MEM, "wb").write(nl.join(lines).encode("utf-8")); print("OK v2.76 (A-96)")

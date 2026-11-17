#!/usr/bin/env python3
"""apply_memory_a97.py - patch HANFIS_RESEARCH_MEMORY.md dari v2.76 ke v2.77 (2026-11-13).

Menambah A-89: perbaikan temuan kirim (gerbang 1.320, Additional files, OSF ke bib, pernyataan persetujuan penulis, kata kunci) dan pemadatan
C.1 sampai C.7 (61 ke 54 halaman). Lapisan (P1): pelaporan naskah. Dokumen: HANFIS_RESEARCH_MEMORY.md.
Teks-persis, gagal-tertutup; idempoten; CRLF dipertahankan; cadangan .pre-a97.bak. Jalankan dari root repo:  python3 Patch/apply_memory_a97.py
"""
import os, sys

MEM = "HANFIS_RESEARCH_MEMORY.md"
if not (os.path.isfile(MEM) and os.path.isdir(".git")):
    sys.exit("ABORT: jalankan dari root repo")
OLD_HEAD = "> Versi: 2.76 · Tanggal: 2026-11-13 ·"
NEW_HEAD = "> Versi: 2.77 · Tanggal: 2026-11-17 ·"
A89 = (
"| A-97 | 2026-11-17 | Perbaikan dari penilaian PDF Overleaf (lanjutan A-96) | "
"(1) `Patch/apply_review_fixes_2026-11-17.py` (diuji di salinan: terapkan, ulang hash sama, CRLF, teks lama diubah ditolak): (a) Availability: 'Sections 4.15 to 4.10' (urutan terbalik) menjadi tiga rujukan bernama E25, E26, E27 (Sections 4.15, 4.9, 4.10); "
"(b) Section 5.1: titik koma sebelum 'The H2/H3' menjadi titik; (c) Section 3.4: satu kalimat yang menjelaskan 6.833 baris lawan 6.357 baris berlabel (476 baris feature-only = 4 minggu terakhir 2026-08-31 sampai 2026-09-21, 119 kelompok image per minggu; diverifikasi dari `asset_weeks_v2_120assets_e4bis.csv`); "
"(d) gaya sitasi author-year: 51 `\\cite` menjadi `\\citep` di naskah dan 2 di Additional file 1, dua `\\citet` (HANFIS of Soozanchi-K. et al.; argument of Raju et al.; Wang) dan dua `\\citealp` (aritmetika Raju/Wang di C2; tumpukan Prometheus); multiset kunci sitasi identik dengan HEAD (61 dan 2); "
"(e) Figure 2: label 'refused' dipindah ke bawah kedua garis (`scripts/fig_e5_rule_growth.py`, gambar dibuat ulang, diperiksa visual). "
"(2) Hasil: PDF 51 halaman, Additional file 1 23 halaman, 0 peringatan bibtex, tanpa referensi tak terdefinisi; cite/label/math identik, satu \\ref baru (subsec:e26), satu angka baru (476) yang sengaja; gaya sitasi tercetak sebagai '(Jang 1993)' dan '(Hafiz Hersyah et al. 2025)' sesuai sn-basic. "
"(3) Terbuka: tag `manuscript-submission-2026-11` masih menunjuk komit 7e39a90 (sebelum perbaikan ini); menggeser tag ke komit baru menunggu persetujuan peneliti karena menulis ulang tag yang sudah di-push. Judul, cakupan jurnal, dan pembanding praktisi tidak diubah. Unggah ulang `sn-article.tex` dan `fig_e5_rule_growth.pdf` ke Overleaf diperlukan. |"
)
raw = open(MEM, "rb").read(); crlf = b"\r\n" in raw; s = raw.decode("utf-8").replace("\r\n", "\n"); nl = "\r\n" if crlf else "\n"
if NEW_HEAD in s and s.count("| A-97 |") == 1 and A89 in s:
    print("SUDAH TERPASANG: v2.77 (A-97)"); sys.exit(0)
if "| A-97 |" in s: sys.exit("ABORT: A-97 sudah ada dengan isi lain")
if s.count(OLD_HEAD) != 1: sys.exit("ABORT: kepala v2.76 tidak unik")
lines = s.split("\n"); idx = [i for i, l in enumerate(lines) if l.startswith("| A-96 |")]
if len(idx) != 1 or (idx[0] + 1 < len(lines) and lines[idx[0] + 1].startswith("|")): sys.exit("ABORT: A-96 bukan baris terakhir tabel")
lines = s.replace(OLD_HEAD, NEW_HEAD).split("\n"); lines.insert(idx[0] + 1, A89)
open(MEM + ".pre-a97.bak", "wb").write(raw); open(MEM, "wb").write(nl.join(lines).encode("utf-8")); print("OK v2.77 (A-97)")

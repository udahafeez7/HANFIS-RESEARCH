#!/usr/bin/env python3
"""apply_memory_a90.py - patch HANFIS_RESEARCH_MEMORY.md dari v2.69 ke v2.70 (2026-11-11).

Menambah A-89: perbaikan temuan kirim (gerbang 1.320, Additional files, OSF ke bib, pernyataan persetujuan penulis, kata kunci) dan pemadatan
C.1 sampai C.7 (61 ke 54 halaman). Lapisan (P1): pelaporan naskah. Dokumen: HANFIS_RESEARCH_MEMORY.md.
Teks-persis, gagal-tertutup; idempoten; CRLF dipertahankan; cadangan .pre-a90.bak. Jalankan dari root repo:  python3 Patch/apply_memory_a90.py
"""
import os, sys

MEM = "HANFIS_RESEARCH_MEMORY.md"
if not (os.path.isfile(MEM) and os.path.isdir(".git")):
    sys.exit("ABORT: jalankan dari root repo")
OLD_HEAD = "> Versi: 2.69 · Tanggal: 2026-11-11 ·"
NEW_HEAD = "> Versi: 2.70 · Tanggal: 2026-11-11 ·"
A89 = (
"| A-90 | 2026-11-11 | Ronde pangkas kedua, keterangan tabel, Figure 2 dibuat ulang, periode AI, rekomendasi ketersediaan (lanjutan A-89) | "
"(1) `Patch/apply_round2_2026-11-11.py` (22 pasangan, diuji di salinan): Literature Review 2.2 paragraf aplikasi, Predictive performance (dua paragraf), E9-E11 (tiga), E25 (dua), E7 results (satu) dan Discussion (tiga) dipadatkan; "
"satu kalimat baru di Discussion menyebut dua kandidat penjelasan kegagalan maju yang terlihat di data lama (noise pada baris tanpa perubahan masukan, Section E16; varians prediksi melebihi varians label pada image hampir konstan, Section 4.3) dan menyatakannya tidak diuji. "
"Keterangan tabel/gambar: kalimat pertama semua <= 15 kata (10 keterangan; sebelumnya 7 melebihi), kode E dihapus dari keterangan. Periode AI: September sampai November 2026 (keputusan peneliti). "
"Hasil: badan 9.539 menjadi 9.056 kata; PDF 54 menjadi 52 halaman (referee); kode E di badan 34 menjadi 26; 0 peringatan bibtex. Invarian: cite dan label identik; angka yang hilang dari prosa semuanya masih ada di tabel atau Additional file 1 (176/1.052, 264.865, 388.665, 0.95, 49, 2.5, 0.27, 99.4, 39.8). "
"(2) Figure 2 dibuat ulang: `scripts/fig_e5_rule_growth.py` (analitik, dari `estimate_params(2,3,k)`: k=1 34/176, k=2 178/1.152, k=3 1.474/11.920, k=4 13.138/131.552; label 'refused (>2,000-param budget)'); gambar lama dicadangkan `.pre-regen.bak`. "
"(3) Zenodo v1 (API, 2026-11-11): rekaman terbuka, satu berkas `HANFIS-RESEARCH_534de7d.zip` (5,76 MB, md5 5c6f040f29062e57fa85207e5ca24da2). Komit 534de7d memuat: 116 berkas bukti Trivy, manifes snapshot (bukan berkas EPSS/KEV mentah), results_python 160 berkas termasuk lima model akhir E7 (.pt) dan hasil E3/E4, protokol 14 berkas. TIDAK memuat: 25 model tersimpan E4-bis, keluaran E7 (D2), hasil E25-E27, Additional file 1, snapshot EPSS/KEV bersegel. "
"Rekomendasi: Zenodo v2 sebelum kirim dengan semua itu; pernyataan Availability dibetulkan agar menyebut isi v1 dan v2 apa adanya; repo dibuka publik saat kirim (telaah satu arah, tidak ada alasan menutup) atau kalimat 'private during review' diganti 'public on acceptance'. Belum diubah: menunggu keputusan dan tanggal dari peneliti. "
"(4) Terbuka: naskah 52 halaman referee masih di atas target 45; blok besar yang tersisa Introduction, Methodology 3.1-3.2, Lit Review 2.1 (butuh keputusan peneliti); pembacaan utuh; unggah ke Overleaf menunggu konfirmasi. |"
)
raw = open(MEM, "rb").read(); crlf = b"\r\n" in raw; s = raw.decode("utf-8").replace("\r\n", "\n"); nl = "\r\n" if crlf else "\n"
if NEW_HEAD in s and s.count("| A-90 |") == 1 and A89 in s:
    print("SUDAH TERPASANG: v2.70 (A-90)"); sys.exit(0)
if "| A-90 |" in s: sys.exit("ABORT: A-90 sudah ada dengan isi lain")
if s.count(OLD_HEAD) != 1: sys.exit("ABORT: kepala v2.69 tidak unik")
lines = s.split("\n"); idx = [i for i, l in enumerate(lines) if l.startswith("| A-89 |")]
if len(idx) != 1 or (idx[0] + 1 < len(lines) and lines[idx[0] + 1].startswith("|")): sys.exit("ABORT: A-89 bukan baris terakhir tabel")
lines = s.replace(OLD_HEAD, NEW_HEAD).split("\n"); lines.insert(idx[0] + 1, A89)
open(MEM + ".pre-a90.bak", "wb").write(raw); open(MEM, "wb").write(nl.join(lines).encode("utf-8")); print("OK v2.70 (A-90)")

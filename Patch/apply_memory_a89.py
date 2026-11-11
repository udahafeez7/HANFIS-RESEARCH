#!/usr/bin/env python3
"""apply_memory_a89.py - patch HANFIS_RESEARCH_MEMORY.md dari v2.68 ke v2.69 (2026-11-11).

Menambah A-89: perbaikan temuan kirim (gerbang 1.320, Additional files, OSF ke bib, pernyataan persetujuan penulis, kata kunci) dan pemadatan
C.1 sampai C.7 (61 ke 54 halaman). Lapisan (P1): pelaporan naskah. Dokumen: HANFIS_RESEARCH_MEMORY.md.
Teks-persis, gagal-tertutup; idempoten; CRLF dipertahankan; cadangan .pre-a89.bak. Jalankan dari root repo:  python3 Patch/apply_memory_a89.py
"""
import os, sys

MEM = "HANFIS_RESEARCH_MEMORY.md"
if not (os.path.isfile(MEM) and os.path.isdir(".git")):
    sys.exit("ABORT: jalankan dari root repo")
OLD_HEAD = "> Versi: 2.68 · Tanggal: 2026-11-11 ·"
NEW_HEAD = "> Versi: 2.69 · Tanggal: 2026-11-11 ·"
A89 = (
"| A-89 | 2026-11-11 | Temuan kirim A.1, A.3, A.4, A.5, A.8 dan pemadatan C.1 sampai C.7 (lanjutan A-88) | "
"(1) `Patch/apply_submission_fixes_2026-11-11.py` (6 pasangan + 1 entri bib, diuji di salinan): gerbang data ditulis apa adanya (kode `asset_weeks.py:444` memasang 1.320 baris = 10 x 132 parameter konfigurasi m_I=2 sebelum A-02, "
"diverifikasi `HANFIS(m_intermediate=2)` = 132 parameter; untuk 176 parameter setara 1.760; inventori melewati keduanya); kata kunci menjadi ANFIS, Hierarchical fuzzy systems, Exploit prediction, Container security, Kubernetes, Pre-registered evaluation, Negative result (judul tetap); "
"bagian `Additional files` ditambahkan sebelum Declarations; dua URL OSF di teks menjadi `\\cite{osf_ahcvs}` (entri @misc dengan DOI dan tanggal akses); janji 'a Zenodo version DOI will be added' dihapus; 'All authors read and approved the final manuscript' ditambahkan. "
"(2) `Patch/apply_condense_2026-11-11.py` (gagal-tertutup, diuji: terapkan, ulang hash sama, keadaan campuran ditolak, anchor rusak ditolak): dipindah utuh ke Additional file 1 dengan teks asli: protokol overhead observabilitas dan pengaman validitas (Note S8, Table S14), horizon sweep (Note S9, Table S15), anatomi galat E16-E19 (Note S10, Table S16), kurva akurasi-kompleksitas (Note S11, Figure S5); "
"Table S17 memetakan kode E1-E27, Runs 7-16 dan amendemen A-02, A-04, A-06, A-09, A-10, A-13, A-16 ke bagian naskah. Teks utama diganti ringkasan dengan angka kunci yang sama; E6, E15, E21 dipadatkan; judul subbagian tanpa kode E; sebutan 'amendment A-xx' di badan 10 menjadi 1 (rujukan ke Table S17). "
"Hasil: badan 11.086 menjadi 9.539 kata; subbagian 29 menjadi 27; tabel badan 11 menjadi 8; gambar 3 menjadi 2; PDF 61 menjadi 54 halaman (opsi referee); Additional file 1 15 menjadi 22 halaman; 0 peringatan bibtex; kode E di badan 56 menjadi 34. "
"Pemeriksa invarian: cite/label/ref hanya berpindah; angka yang hilang dari gabungan badan+AF1 hanya pembulatan ganda (99.4 vs 99.36 dsb.), ID gerbang O5-B4.10/11, dan DOI OSF yang pindah ke bib. Tidak ada angka hasil yang berubah. "
"(3) Belum dikerjakan: C.6 hanya sebagian (kalimat >40 kata 63 menjadi 60; pengulangan 97% tetap 5); A.6 keterangan tabel >15 kata (13 dari 14); A.7 Figure 2; A.2 Zenodo v2 dan status repo; periode AI 'during 2026'. Judul tidak diubah (keputusan peneliti 3 Nov). |"
)
raw = open(MEM, "rb").read(); crlf = b"\r\n" in raw; s = raw.decode("utf-8").replace("\r\n", "\n"); nl = "\r\n" if crlf else "\n"
if NEW_HEAD in s and s.count("| A-89 |") == 1 and A89 in s:
    print("SUDAH TERPASANG: v2.69 (A-89)"); sys.exit(0)
if "| A-89 |" in s: sys.exit("ABORT: A-89 sudah ada dengan isi lain")
if s.count(OLD_HEAD) != 1: sys.exit("ABORT: kepala v2.68 tidak unik")
lines = s.split("\n"); idx = [i for i, l in enumerate(lines) if l.startswith("| A-88 |")]
if len(idx) != 1 or (idx[0] + 1 < len(lines) and lines[idx[0] + 1].startswith("|")): sys.exit("ABORT: A-88 bukan baris terakhir tabel")
lines = s.replace(OLD_HEAD, NEW_HEAD).split("\n"); lines.insert(idx[0] + 1, A89)
open(MEM + ".pre-a89.bak", "wb").write(raw); open(MEM, "wb").write(nl.join(lines).encode("utf-8")); print("OK v2.69 (A-89)")

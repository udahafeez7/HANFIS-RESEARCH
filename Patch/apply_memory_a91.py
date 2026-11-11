#!/usr/bin/env python3
"""apply_memory_a91.py - patch HANFIS_RESEARCH_MEMORY.md dari v2.70 ke v2.71 (2026-11-11).

Menambah A-89: perbaikan temuan kirim (gerbang 1.320, Additional files, OSF ke bib, pernyataan persetujuan penulis, kata kunci) dan pemadatan
C.1 sampai C.7 (61 ke 54 halaman). Lapisan (P1): pelaporan naskah. Dokumen: HANFIS_RESEARCH_MEMORY.md.
Teks-persis, gagal-tertutup; idempoten; CRLF dipertahankan; cadangan .pre-a91.bak. Jalankan dari root repo:  python3 Patch/apply_memory_a91.py
"""
import os, sys

MEM = "HANFIS_RESEARCH_MEMORY.md"
if not (os.path.isfile(MEM) and os.path.isdir(".git")):
    sys.exit("ABORT: jalankan dari root repo")
OLD_HEAD = "> Versi: 2.70 · Tanggal: 2026-11-11 ·"
NEW_HEAD = "> Versi: 2.71 · Tanggal: 2026-11-11 ·"
A89 = (
"| A-91 | 2026-11-11 | Ronde pangkas ketiga: Introduction, Literature Review 2.1, Methodology 3.1-3.2 (lanjutan A-90) | "
"(1) `Patch/apply_round3_2026-11-11.py` (18 pasangan + Note S12, diuji di salinan: terapkan, ulang hash sama, CRLF, anchor rusak ditolak). Introduction dipadatkan; dua paragraf edge/policy digabung; 'telemetry indicates' menjadi 'new evidence shows' (selaras A-77); "
"masukan ancaman ditulis apa adanya (x7 = indikator KEV; EPSS masuk lewat exploitability) menggantikan daftar EPSS/recency/source confidence yang tidak dipakai model; nama Jetson tidak lagi disebut (P11); roadmap satu kalimat. Teks H1a-H4 tidak diubah. "
"Lit Review 2.1 dipadatkan; alias HANFIS-DRS (tidak pernah dipakai) dihapus. Methodology 3.1 menjadi 'Study design' satu paragraf (teks lama utuh di Note S12); 3.2 berjudul 'HANFIS architecture and training' sehingga judul ganda hilang; persentase 73.4/83.3 yang terulang di 3.2 dihapus (tetap di Introduction); kode E2 dan amendment A-09 dihapus (peta Table S17). "
"(2) Hasil: badan 9.056 menjadi 8.596 kata; PDF 52 menjadi 51 halaman (referee, spasi ganda); tanpa opsi referee/lineno 33 halaman; Additional file 1 23 halaman; amendment A-xx di badan 0; Jetson 0; tanda pisah 0; 0 peringatan bibtex. Invarian: cite, label, math identik; angka yang keluar dari badan hanya duplikat 73.4/83.3 dan kode E2/A-09. "
"(3) Penilaian (pertimbangan): strength 79, weakness 47, gap 48, opportunity 65, kesiapan submit 77. Penahan: Zenodo v2 dan pernyataan ketersediaan, pembacaan utuh oleh penulis, unggah Overleaf. |"
)
raw = open(MEM, "rb").read(); crlf = b"\r\n" in raw; s = raw.decode("utf-8").replace("\r\n", "\n"); nl = "\r\n" if crlf else "\n"
if NEW_HEAD in s and s.count("| A-91 |") == 1 and A89 in s:
    print("SUDAH TERPASANG: v2.71 (A-91)"); sys.exit(0)
if "| A-91 |" in s: sys.exit("ABORT: A-91 sudah ada dengan isi lain")
if s.count(OLD_HEAD) != 1: sys.exit("ABORT: kepala v2.70 tidak unik")
lines = s.split("\n"); idx = [i for i, l in enumerate(lines) if l.startswith("| A-90 |")]
if len(idx) != 1 or (idx[0] + 1 < len(lines) and lines[idx[0] + 1].startswith("|")): sys.exit("ABORT: A-90 bukan baris terakhir tabel")
lines = s.replace(OLD_HEAD, NEW_HEAD).split("\n"); lines.insert(idx[0] + 1, A89)
open(MEM + ".pre-a91.bak", "wb").write(raw); open(MEM, "wb").write(nl.join(lines).encode("utf-8")); print("OK v2.71 (A-91)")

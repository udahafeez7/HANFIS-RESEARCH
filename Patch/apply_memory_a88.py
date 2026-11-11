#!/usr/bin/env python3
"""apply_memory_a88.py - patch HANFIS_RESEARCH_MEMORY.md dari v2.67 ke v2.68 (2026-11-11).

Menambah A-88: penyatuan sumber Overleaf ke repositori, audit bib 42 entri, abstrak <= 250 kata, penutup, H3, pernyataan AI, Holm terverifikasi.
Lapisan (P1): pelaporan naskah dan prosedur mutu. Dokumen: HANFIS_RESEARCH_MEMORY.md.
Teks-persis, gagal-tertutup: semua jangkar dicek (harus cocok tepat satu kali) sebelum apa pun ditulis.
Idempoten: bila sudah dalam keadaan akhir, keluar 0 tanpa menulis. Keadaan sebagian = ABORT.
Akhir baris (LF/CRLF) dipertahankan. Cadangan: HANFIS_RESEARCH_MEMORY.md.pre-a88.bak.
Jalankan dari root repo:  python3 Patch/apply_memory_a88.py
"""
import os, sys

MEM = "HANFIS_RESEARCH_MEMORY.md"
if not (os.path.isfile(MEM) and os.path.isdir(".git")):
    sys.exit("ABORT: jalankan dari root repo (harus ada .git dan HANFIS_RESEARCH_MEMORY.md)")

OLD_HEAD = "> Versi: 2.67 · Tanggal: 2026-11-11 ·"
NEW_HEAD = "> Versi: 2.68 · Tanggal: 2026-11-11 ·"

A88 = (
"| A-88 | 2026-11-11 | Satu sumber naskah (Overleaf ke repositori), audit bib 42 entri, abstrak, penutup, H3, pernyataan AI (lanjutan A-87) | "
"(1) Zip Overleaf `2026_11_07_HIBAH_KEPAKARAN_HAFIZ___ANFIS.zip` (diunduh peneliti 2026-11-11) disatukan ke repositori lewat `Patch/apply_overleaf_merge_2026-11-11.py` "
"(hash masukan dikunci: sn-article.tex 05ce5b82d286, sn-bibliography.bib e51c7491611f; cadangan `.pre-overleafmerge.bak`; tiga perbaikan gerbang A-87 diterapkan ulang di atasnya). "
"Sejak komit ini `manuscript/sn-article.tex` di repositori adalah SATU-SATUNYA sumber kebenaran; Overleaf harus diperbarui dari repositori (unggah tex dan bib), bukan sebaliknya. "
"Zip tidak memuat `additional_file_1.tex`; versi repositori dipertahankan. "
"(2) Audit bib Overleaf (42 entri; `audit_bib_dois.py` diberi penjaga tahun None dari Crossref): 35 OK, 6 tanpa DOI (Trivy, KEV, CVSS 4.0, Holm, Kubernetes, Prometheus), 1 PERIKSA `brown1995curse` "
"(Crossref mencatat 2002 sebagai tanggal rekaman IEEE Xplore; konferensi 1995, entri benar). `bib_deep_audit.py`: 36 entri ber-DOI lengkap, dua catatan booktitle lawan series (soozanchi2010hanfis, brown1995curse) bukan kesalahan. "
"Holm (1979) DIVERIFIKASI peneliti dari JSTOR 2026-11-11: Scand. J. Statist. 6(2):65-70; entri bib sudah sesuai. "
"(3) `Patch/apply_abstract_conclusion_ai_2026-11-11.py` (7 pasangan, diuji di salinan: terapkan, ulang hash sama, CRLF, anchor rusak ditolak): abstrak 271 menjadi 248 kata (73.4% dan 83.3% dihapus dari abstrak, tetap di Section 3; "
"angka lain tetap); kalimat H3 yang menafsirkan plateau flat ANFIS sebagai bukti mekanisme dihapus (audit klaim 2026-11-07 baris 6); tiga kalimat penutup tanpa pola 'not X but Y' dan klaim interpretabilitas diselaraskan dengan E27; "
"pernyataan AI di Methods dan Declarations ditulis ulang: model Claude Sonnet 5.5, Opus 5.5, Fable 5.1 (dari log sesi Claude Code 2026-10-20 ke depan), cakupan (kode, dua protokol tak terdaftar, menjalankan skrip atas arahan penulis termasuk tahap E7, draf teks termasuk sebagian Results dan Discussion, pemeriksaan referensi), "
"kalimat 'All experiments were run by the authors' dihapus. Periode 'during 2026' masih harus dikonfirmasi peneliti (sesi sebelum 2026-10-20 tidak ada di log mesin ini). "
"(4) Kompilasi: sn-article.pdf 61 halaman, 0 peringatan bibtex, tanpa referensi tak terdefinisi, satu overfull 0.78pt; additional_file_1.pdf 15 halaman. Pemeriksa invarian: cite/label/ref hanya bertambah (Literature Review Overleaf), angka hilang hanya 73.4, 83.3 dan 'H2/H3' pada kalimat yang dihapus. "
"Terbuka: label mentah '2{,}000' di Figure 2 (skrip pembuat `fig_e5_rule_growth.pdf` tidak ada di repositori; `e5_sweep.py` tidak menggambar); pembacaan utuh oleh penulis; Zenodo ditunda atas keputusan peneliti. |"
)

raw = open(MEM, "rb").read()
crlf = b"\r\n" in raw
s = raw.decode("utf-8").replace("\r\n", "\n")
nl = "\r\n" if crlf else "\n"

if NEW_HEAD in s and s.count("| A-88 |") == 1 and A88 in s:
    print("SUDAH TERPASANG: v2.68 (A-88); tidak ada yang ditulis")
    sys.exit(0)
if "| A-88 |" in s:
    sys.exit("ABORT: A-88 sudah ada dengan isi lain; tidak ada yang ditulis")
if s.count(OLD_HEAD) != 1:
    sys.exit(f"ABORT: kepala v2.67 cocok {s.count(OLD_HEAD)} kali (harus 1); tidak ada yang ditulis")
lines = s.split("\n")
idx = [i for i, l in enumerate(lines) if l.startswith("| A-87 |")]
if len(idx) != 1:
    sys.exit(f"ABORT: baris A-87 cocok {len(idx)} kali (harus 1); tidak ada yang ditulis")
if idx[0] + 1 < len(lines) and lines[idx[0] + 1].startswith("|"):
    sys.exit("ABORT: A-87 bukan baris terakhir tabel amendemen; tidak ada yang ditulis")

s2 = s.replace(OLD_HEAD, NEW_HEAD)
lines = s2.split("\n")
idx = [i for i, l in enumerate(lines) if l.startswith("| A-87 |")]
lines.insert(idx[0] + 1, A88)
out = nl.join(lines).encode("utf-8")

with open(MEM + ".pre-a88.bak", "wb") as f:
    f.write(raw)
with open(MEM, "wb") as f:
    f.write(out)
print("OK v2.68 (A-88)", "| CRLF" if crlf else "| LF", "| cadangan", MEM + ".pre-a88.bak")

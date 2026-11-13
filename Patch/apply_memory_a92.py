#!/usr/bin/env python3
"""apply_memory_a92.py - patch HANFIS_RESEARCH_MEMORY.md dari v2.71 ke v2.72 (2026-11-13).

Menambah A-89: perbaikan temuan kirim (gerbang 1.320, Additional files, OSF ke bib, pernyataan persetujuan penulis, kata kunci) dan pemadatan
C.1 sampai C.7 (61 ke 54 halaman). Lapisan (P1): pelaporan naskah. Dokumen: HANFIS_RESEARCH_MEMORY.md.
Teks-persis, gagal-tertutup; idempoten; CRLF dipertahankan; cadangan .pre-a92.bak. Jalankan dari root repo:  python3 Patch/apply_memory_a92.py
"""
import os, sys

MEM = "HANFIS_RESEARCH_MEMORY.md"
if not (os.path.isfile(MEM) and os.path.isdir(".git")):
    sys.exit("ABORT: jalankan dari root repo")
OLD_HEAD = "> Versi: 2.71 · Tanggal: 2026-11-11 ·"
NEW_HEAD = "> Versi: 2.72 · Tanggal: 2026-11-13 ·"
A89 = (
"| A-92 | 2026-11-13 | Zenodo v2: unggah via API, metadata, pernyataan Availability (lanjutan A-91) | "
"(1) Draf Zenodo https://zenodo.org/uploads/24133609 (DOI cadangan 10.5281/zenodo.24133609, status unsubmitted, TIDAK dipublikasikan): lewat API (token deposit:write saja, disimpan lokal di ~/.zenodo_token, harus dihapus peneliti) diunggah `HANFIS-RESEARCH_4d82bea_code.zip` (md5 604041cf151fe6a7655a79ec52839985), `HANFIS_results_models_2026-11-11.tar.gz` (d292a72e28098ab9b823021e701add3b), `Additional_file_1.pdf` (4775c0913fa34a1e7177a45318c238f7), `SHA256SUMS.txt` (c1f1ad83df88f5096e3b9c0ca60d0c63); md5 Zenodo = md5 lokal. "
"Keputusan peneliti 2026-11-13: snapshot EPSS/KEV TIDAK diunggah (tidak boleh didistribusikan ulang); lewati; manifes SHA-256 ada di zip kode. Metadata diisi via API: Version v2.0, deskripsi v2 (menggantikan deskripsi v1 yang usang), related isNewVersionOf 10.5281/zenodo.23357118 dan isSupplementTo repositori GitHub, kata kunci Negative result dan Forward evaluation. "
"(2) Isi arsip v2 diperiksa dari zip dan tarball: ADA protokol beku, manifes snapshot, 25 model E4-bis, lima model akhir E7 dan keluaran D2, hasil E25-E27, Additional file 1, keluaran Trivy 15 image; TIDAK ADA berkas snapshot EPSS/KEV, keluaran Trivy lengkap, tabel asset-week turunan, keluaran mentah telemetri Runs 7-16. "
"Akibat: tabel asset-week tidak ada di arsip, jadi reviewer tidak dapat menjalankan ulang pelatihan tanpa membangunnya dari snapshot dan pindaian; keputusan menyertakan tabel turunan (data hasil olahan, bukan berkas EPSS mentah) ada pada peneliti. "
"(3) `Patch/apply_availability_zenodo_v2_2026-11-13.py` (2 pasangan, diuji di salinan): Availability dan Code availability menyebut DOI v2 24133609 dan v1 23357118, isi arsip apa adanya, snapshot tidak didistribusikan ulang, OSF lewat \\cite{osf_ahcvs}; 'private during review' diganti repositori publik github.com/udahafeez7/HANFIS-RESEARCH. PDF 51 halaman, 0 peringatan bibtex. "
"(4) Terbuka: repositori GitHub BELUM publik (gh tidak terpasang; peneliti ubah di Settings, Danger Zone, Change visibility; deskripsi Zenodo dan naskah sudah menyebut publik, jadi harus dilakukan sebelum Publish dan sebelum kirim). Pemindaian rahasia: pola token/kunci di pohon HEAD bersih; riwayat penuh belum dipindai (git grep lintas 400 revisi terlalu lambat di /mnt/c); nama berkas sensitif di riwayat hanya hasil pindai image external-secrets. "
"Publish Zenodo menunggu peneliti; setelah terbit CITATION.cff dan README (masih DOI v1 dan 'private during review') diperbarui. |"
)
raw = open(MEM, "rb").read(); crlf = b"\r\n" in raw; s = raw.decode("utf-8").replace("\r\n", "\n"); nl = "\r\n" if crlf else "\n"
if NEW_HEAD in s and s.count("| A-92 |") == 1 and A89 in s:
    print("SUDAH TERPASANG: v2.72 (A-92)"); sys.exit(0)
if "| A-92 |" in s: sys.exit("ABORT: A-92 sudah ada dengan isi lain")
if s.count(OLD_HEAD) != 1: sys.exit("ABORT: kepala v2.71 tidak unik")
lines = s.split("\n"); idx = [i for i, l in enumerate(lines) if l.startswith("| A-91 |")]
if len(idx) != 1 or (idx[0] + 1 < len(lines) and lines[idx[0] + 1].startswith("|")): sys.exit("ABORT: A-91 bukan baris terakhir tabel")
lines = s.replace(OLD_HEAD, NEW_HEAD).split("\n"); lines.insert(idx[0] + 1, A89)
open(MEM + ".pre-a92.bak", "wb").write(raw); open(MEM, "wb").write(nl.join(lines).encode("utf-8")); print("OK v2.72 (A-92)")

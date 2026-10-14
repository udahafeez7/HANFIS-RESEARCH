#!/usr/bin/env python3
r"""Mencatat A-63 (penyuntingan naskah dua tahap: bahasa dan akurasi klaim) di HANFIS_RESEARCH_MEMORY.md dan menaikkan versi 2.36 -> 2.37.
Gagal-tertutup: baris A-62 dan kepala 'Versi: 2.36 · Tanggal: 2026-10-14' harus ada tepat sekali; baris A-63 harus berisi tepat 5 pipa. Idempoten (baris A-63 yang ada diganti). Cadangan .pre-a63.bak.
   python scripts/apply_memory_a63.py [--today 2026-10-14]"""
import argparse, re, shutil, sys
from pathlib import Path
ap = argparse.ArgumentParser(); ap.add_argument("--today", default="2026-10-14"); a = ap.parse_args()
M = Path("HANFIS_RESEARCH_MEMORY.md"); m = M.read_text(encoding="utf-8")
ROW = ("| A-63 | " + a.today + " | Naskah, batas klaim | Penyuntingan naskah dua tahap, keduanya melalui skrip teks-persis yang gagal-tertutup (komit 35e73ba dan c0b8436). "
 "Tahap 1, bahasa: 20 suntingan (`scripts/apply_prose_edits_1.py` sha256 7854fe7c154773df); kalimat dipendekkan, pola kontras dan rantai titik koma dikurangi, pengulangan angka Shapley di Limitations diganti rujukan silang; kutipan, rujukan silang, rumus, dan angka diperiksa identik. "
 "Tahap 2, akurasi dan batas klaim: 11 suntingan (`scripts/apply_prose_edits_2.py` sha256 319d2c6334ce22ec). "
 "(A) Abstract dan Discussion diselaraskan dengan Tabel E3: SS_clim persistence 0,974 dan CVSS 0,222 (semula abstrak menyebut CVSS 'almost none' dan Discussion memakai angka pilot). "
 "(B) janji perbandingan Fuzzyfortify di Introduction dihapus, karena Section 4.3 menyatakan perbandingan itu tidak dilakukan. "
 "(C) policy-translation layer bukan kontribusi naskah ini: paragraf Introduction diringkas menjadi satu kalimat, C4 lama dihapus dan C5 menjadi C4, rujukan di Conclusion disesuaikan. "
 "(D) 'interpretable by construction' diganti 'designed to be interpretable' dan tujuan studi mencakup uji fidelitas penjelasan (E6; H6c gagal). "
 "(E) definisi 'pre-registered' diberi pengecualian OSF untuk E7. (F) salah ketik 'uncriteria'd'. "
 "(G) Limitations memuat pernyataan bahwa analisis post hoc dijalankan pada data yang sama tanpa koreksi multiplisitas dan tidak mengubah keputusan terdaftar, serta batas validitas eksternal inventaris dan label. "
 "Tidak ada angka hasil, kutipan, atau teks hipotesis terdaftar yang diubah. Diverifikasi: 37 halaman, tanpa 'undefined', satu Overfull lama. "
 "Menunggu: kalimat E7 'results will be added to a later version' diganti setelah D2; kalimat kontribusi D.D. menunggu konfirmasi beliau |")
if ROW.count("|") != 5: sys.exit(f"ABORT: baris A-63 harus berisi tepat 5 pipa (ada {ROW.count('|')})")
if re.search(r"^\| A-63 \|", m, re.M): new = re.sub(r"^\| A-63 \|.*$", lambda x: ROW, m, count=1, flags=re.M)
else:
    r62 = list(re.finditer(r"^\| A-62 \|.*$", m, re.M)); h = list(re.finditer(r"Versi: 2\.36 \u00b7 Tanggal: 2026-10-14", m))
    if len(r62) != 1 or len(h) != 1: sys.exit(f"ABORT, tidak ada yang ditulis: baris A-62 {len(r62)}x, kepala {len(h)}x (harus 1 dan 1)")
    new = m[:r62[0].end()] + "\n" + ROW + m[r62[0].end():]; new = new.replace("Versi: 2.36 \u00b7 Tanggal: 2026-10-14", f"Versi: 2.37 \u00b7 Tanggal: {a.today}", 1)
if new == m: print("Tidak ada perubahan (sudah sama)."); sys.exit(0)
shutil.copy(M, str(M) + ".pre-a63.bak"); M.write_text(new, encoding="utf-8"); print("OK: A-63 ditambahkan; versi 2.37")

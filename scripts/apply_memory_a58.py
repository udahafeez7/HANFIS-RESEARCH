#!/usr/bin/env python3
"""Amandemen A-58 pada HANFIS_RESEARCH_MEMORY.md: E22 (sensitivitas E21, bootstrap per minggu), koreksi kalimat E21, dan konfirmasi kata kontribusi B.R.; versi 2.32. Dijalankan lagi memperbarui baris A-58 yang sama.
Gagal-tertutup (baris A-57 dan kepala 'Versi: 2.31 · Tanggal: 2026-10-14' harus ada tepat sekali); cadangan .pre-a58.bak.   python scripts/apply_memory_a58.py [--today 2026-10-14]"""
import argparse, re, shutil, sys
from pathlib import Path
ap = argparse.ArgumentParser(); ap.add_argument("--today", default="2026-10-14"); a = ap.parse_args()
P = Path("HANFIS_RESEARCH_MEMORY.md"); s = P.read_text(encoding="utf-8")
ROW = ("| A-58 | " + a.today + " | Eksperimen E22 dan E23, naskah | E22 (sensitivitas E21, post hoc, tanpa pelatihan, data lama): bootstrap berkelompok per minggu (45 minggu; 37 pada baris bersih) dibandingkan dengan per image; prediksi dan lipatan sama dengan E21 (pemeriksaan reproduksi --by image identik dengan E21); "
       "hasil: interval per minggu lebih sempit, bukan lebih lebar (mengoreksi kalimat E21 yang menyatakan sebaliknya); selisih penyimpangan dari ideal HANFIS minus rumus pada baris bersih: kemiringan +0,031 (minggu 0,018 sampai 0,042; image 0,013 sampai 0,051) dan intersep +0,182 (minggu 0,131 sampai 0,230; image 0,063 sampai 0,278) positif pada kedua pengelompokan, ME +0,055 positif hanya per minggu (image -0,016 sampai 0,133); pada semua baris hanya kemiringan positif (+0,023; per image 0,001 sampai 0,041); "
       "E23 (rekalibrasi linear silang dan dalam-sampel): skill HANFIS terhadap rumus tidak berubah (semua baris -0,534 menjadi -0,535, perubahan -0,001 [-0,047; 0,116]; baris bersih -2,418 menjadi -2,315, perubahan +0,103 [-0,152; 1,060], sekitar 4 persen defisit, batas dalam-sampel 10 persen): defisit HANFIS bukan akibat miskalibrasi linear; "
       "kalimat E21 diganti dan paragraf E23 ditambahkan (apply_e22_text.py lalu apply_e22_fix_e23.py); keluaran results_python/e22/ dan results_python/e23/; kata kontribusi B.R. (testbed) dikonfirmasi Dr. Budi (komit 80b1835) |")
if ROW.count("|") != 5: sys.exit("ABORT: baris A-58 harus berisi tepat 5 pipa (hapus tanda | dari isi)")
if re.search(r"^\| A-58 \|", s, re.M):
    new = re.sub(r"^\| A-58 \|.*$", lambda m: ROW, s, count=1, flags=re.M); msg = "baris A-58 diperbarui"
else:
    m = list(re.finditer(r"^\| A-57 \|.*$", s, re.M)); h = list(re.finditer(r"Versi: 2\.31 \u00b7 Tanggal: 2026-10-14", s))
    if len(m) != 1 or len(h) != 1: sys.exit(f"ABORT, tidak ada yang ditulis: baris A-57 {len(m)}x, kepala {len(h)}x (harus 1 dan 1)")
    new = s[:m[0].end()] + "\n" + ROW + s[m[0].end():]; new = new.replace("Versi: 2.31 \u00b7 Tanggal: 2026-10-14", f"Versi: 2.32 \u00b7 Tanggal: {a.today}", 1); msg = "A-58 ditambahkan; versi 2.32"
if new == s: print("Tidak ada perubahan."); sys.exit(0)
shutil.copy(P, str(P) + ".pre-a58.bak"); P.write_text(new, encoding="utf-8"); print("OK:", msg)

#!/usr/bin/env python3
"""Amandemen A-58 pada HANFIS_RESEARCH_MEMORY.md: E22 (sensitivitas E21, bootstrap per minggu), koreksi kalimat E21, dan konfirmasi kata kontribusi B.R.; versi 2.32. Dijalankan lagi memperbarui baris A-58 yang sama.
Gagal-tertutup (baris A-57 dan kepala 'Versi: 2.31 · Tanggal: 2026-10-14' harus ada tepat sekali); cadangan .pre-a58.bak.   python scripts/apply_memory_a58.py [--today 2026-10-14]"""
import argparse, re, shutil, sys
from pathlib import Path
ap = argparse.ArgumentParser(); ap.add_argument("--today", default="2026-10-14"); a = ap.parse_args()
P = Path("HANFIS_RESEARCH_MEMORY.md"); s = P.read_text(encoding="utf-8")
ROW = ("| A-58 | " + a.today + " | Eksperimen E22, naskah | E22 (sensitivitas E21, post hoc, tanpa pelatihan, data lama): bootstrap berkelompok per minggu (45 minggu; 37 pada baris bersih) menggantikan per image; prediksi dan lipatan sama dengan E21 (pemeriksaan reproduksi --by image identik dengan E21); "
       "hasil: interval per minggu SEMPIT bukan lebih lebar (mengoreksi kalimat E21 yang menyatakan sebaliknya); selisih penyimpangan dari ideal HANFIS minus rumus: selisih mutlak beta dari 1 +0,023 [0,011; 0,033] semua baris (per image 0,001; 0,041) dan +0,031 [0,018; 0,042] baris bersih; selisih mutlak alfa dari 0 +0,182 [0,131; 0,230] dan selisih mutlak ME +0,055 [0,034; 0,068] positif hanya pada baris bersih; "
       "HANFIS minus persistence pada baris bersih juga positif; kalimat penutup E21 di naskah diganti (apply_e22_text.py); keluaran results_python/e22/e22_week_all_rows.txt, e22_week_clean_rows.txt, e22_image_all_rows.txt; kata kontribusi B.R. (testbed: design of the experimental platform, cluster and telemetry network) dikonfirmasi Dr. Budi (komit 80b1835) |")
if ROW.count("|") != 5: sys.exit("ABORT: baris A-58 harus berisi tepat 5 pipa (hapus tanda | dari isi)")
if re.search(r"^\| A-58 \|", s, re.M):
    new = re.sub(r"^\| A-58 \|.*$", lambda m: ROW, s, count=1, flags=re.M); msg = "baris A-58 diperbarui"
else:
    m = list(re.finditer(r"^\| A-57 \|.*$", s, re.M)); h = list(re.finditer(r"Versi: 2\.31 \u00b7 Tanggal: 2026-10-14", s))
    if len(m) != 1 or len(h) != 1: sys.exit(f"ABORT, tidak ada yang ditulis: baris A-57 {len(m)}x, kepala {len(h)}x (harus 1 dan 1)")
    new = s[:m[0].end()] + "\n" + ROW + s[m[0].end():]; new = new.replace("Versi: 2.31 \u00b7 Tanggal: 2026-10-14", f"Versi: 2.32 \u00b7 Tanggal: {a.today}", 1); msg = "A-58 ditambahkan; versi 2.32"
if new == s: print("Tidak ada perubahan."); sys.exit(0)
shutil.copy(P, str(P) + ".pre-a58.bak"); P.write_text(new, encoding="utf-8"); print("OK:", msg)

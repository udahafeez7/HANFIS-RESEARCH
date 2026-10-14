#!/usr/bin/env python3
"""Amandemen A-57 pada HANFIS_RESEARCH_MEMORY.md: E21 (kalibrasi, post hoc, setelah registrasi publik); versi 2.31. Dijalankan lagi memperbarui baris A-57 yang sama.
Gagal-tertutup (baris A-56 dan kepala 'Versi: 2.30 · Tanggal: 2026-10-14' harus ada tepat sekali); cadangan .pre-a57.bak.   python scripts/apply_memory_a57.py [--today 2026-10-14]"""
import argparse, re, shutil, sys
from pathlib import Path
ap = argparse.ArgumentParser(); ap.add_argument("--today", default="2026-10-14"); a = ap.parse_args()
P = Path("HANFIS_RESEARCH_MEMORY.md"); s = P.read_text(encoding="utf-8")
ROW = ("| A-57 | " + a.today + " | Eksperimen E21, naskah | E21 (kalibrasi, post hoc, deskriptif, tanpa pelatihan) dijalankan setelah registrasi E7 publik pada prediksi out-of-fold E11 horizon 4 minggu (1.080 baris; 890 baris bersih dari pergantian model EPSS): ME, regresi label = alfa + beta x prediksi, desil prediksi; bootstrap per image 2.000 resampel (seed 20261012); "
       "koefisien rumus dicocokkan di dalam lipatan latih pada lipatan yang sama dengan HANFIS (out-of-fold); hasil: persistence bias rendah pada semua baris (ME -0,097) yang hampir seluruhnya berasal dari minggu pergantian model (bersih: -0,015); rumus tanpa bias terdeteksi; HANFIS paling menyimpang (beta 1,025 semua baris, 1,031 bersih; alfa -0,193 bersih); desil 4 HANFIS memprediksi 1,0 untuk label 0,5; deskriptif, interval berkelompok per image; "
       "keluaran results_python/e21/e21_all_rows.txt dan e21_clean_rows.txt (commit efb1e12); subbagian naskah subsec:e21 dan Tabel tab:e21 ditambahkan; E21 tidak tercantum dalam registrasi (dijalankan sesudahnya) |")
if re.search(r"^\| A-57 \|", s, re.M):
    new = re.sub(r"^\| A-57 \|.*$", lambda m: ROW, s, count=1, flags=re.M); msg = "baris A-57 diperbarui"
else:
    m = list(re.finditer(r"^\| A-56 \|.*$", s, re.M)); h = list(re.finditer(r"Versi: 2\.30 \u00b7 Tanggal: 2026-10-14", s))
    if len(m) != 1 or len(h) != 1: sys.exit(f"ABORT, tidak ada yang ditulis: baris A-56 {len(m)}x, kepala {len(h)}x (harus 1 dan 1)")
    new = s[:m[0].end()] + "\n" + ROW + s[m[0].end():]; new = new.replace("Versi: 2.30 \u00b7 Tanggal: 2026-10-14", f"Versi: 2.31 \u00b7 Tanggal: {a.today}", 1); msg = "A-57 ditambahkan; versi 2.31"
if new == s: print("Tidak ada perubahan."); sys.exit(0)
shutil.copy(P, str(P) + ".pre-a57.bak"); P.write_text(new, encoding="utf-8"); print("OK:", msg)

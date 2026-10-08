#!/usr/bin/env python3
"""A-47: koreksi batas data latih model akhir E7 (kebocoran temporal). (1) tambah bagian di protocols/E7_preregistration_DRAFT.md, (2) tambah baris A-47 di
HANFIS_RESEARCH_MEMORY.md setelah A-46. Dari akar repo. Gagal-tertutup bila A-46 tidak ada tepat satu kali; idempoten; cadangan .pre-a47.bak."""
import re, shutil, sys
from pathlib import Path
D = Path("protocols/E7_preregistration_DRAFT.md"); M = Path("HANFIS_RESEARCH_MEMORY.md")
HEAD = "## Amendemen A-47 (2026-10-08): batas data latih model akhir (koreksi kebocoran temporal)"
SECTION = HEAD + """

Draf dan A-44 menyatakan model akhir dilatih pada semua minggu berlabel <= 2026-08-24. **Itu salah.** Label minggu 2026-08-24 memakai EPSS/KEV sampai 2026-09-21, sehingga jendela label baris latih
menumpuk dengan waktu fitur minggu forward 2026-08-31 .. 2026-09-21 dan dengan jendela label forward. Prosedur E4 (`GroupTimeSplit`, `python_hanfis/splits.py`) menerapkan embargo 30 hari:
latih hanya baris dengan `week_start_utc <= minggu uji pertama - 30 hari`.

Untuk E7: minggu forward pertama 2026-08-31, sehingga cutoff = 2026-08-01 dan **model akhir dilatih pada minggu berlabel <= 2026-07-27** (jendela label terakhirnya berakhir 2026-08-24, sebelum
2026-08-31). `scripts/e7_pipeline.py train` menegakkan aturan ini dan menolak embargo < 28 hari; `predict` menolak minggu sebelum minggu forward pertama model dan memverifikasi hash model terhadap manifest.
Gerbang kecukupan data (>= 10 observasi per parameter, 176 parameter) dihitung ulang oleh skrip. Validasi: 15% baris latih acak dengan seed tetap 20260933; konfigurasi pelatihan identik dengan E4.
Koreksi dibuat **sebelum** pembekuan dan tanpa menyentuh label forward. Lambda (dari prediksi out-of-fold E4, yang sudah memakai embargo) tidak terpengaruh. Semua teks lain yang menyebut 2026-08-24
sebagai batas latih (A-44, draf pendaftaran OSF) digantikan oleh amendemen ini.
"""
ROW = ("| A-47 | 2026-10-08 | Eksperimen E7 | Koreksi kebocoran temporal: batas latih model akhir E7 diganti dari minggu berlabel <= 2026-08-24 menjadi <= 2026-07-27 (minggu forward pertama 2026-08-31 dikurangi embargo 30 hari, "
       "aturan yang sama dengan `GroupTimeSplit` di E4); jendela label latih berakhir 2026-08-24 < 2026-08-31. `scripts/e7_pipeline.py` (`train` dan `predict`) menegakkan aturan, menolak embargo < 28 hari dan minggu sebelum minggu forward pertama, "
       "dan memverifikasi hash model. Supersede A-44 pada butir itu; ditemukan saat membaca `e4_run.py` dan `splits.py` sebelum pembekuan, label forward tidak disentuh. |")
if not D.exists(): sys.exit(f"ABORT: {D} tidak ada")
d = D.read_text(encoding="utf-8"); m_ = M.read_text(encoding="utf-8")
has_row = bool(re.search(r"^\| A-47 \|", m_, re.M))
if HEAD in d and has_row: print("A-47 sudah ada; tidak ada perubahan."); sys.exit(0)
a46 = list(re.finditer(r"^\| A-46 \|.*$", m_, re.M))
if not has_row and len(a46) != 1: sys.exit(f"ABORT: baris A-46 ditemukan {len(a46)}x (harus 1); tidak ada yang ditulis")
if HEAD not in d: shutil.copy(D, str(D) + ".pre-a47.bak"); D.write_text(d.rstrip("\n") + "\n\n" + SECTION, encoding="utf-8"); print("OK: bagian A-47 ditambahkan ke draf E7")
if not has_row:
    m_ = m_[:a46[0].end()] + "\n" + ROW + m_[a46[0].end():]
    h = re.search(r"Versi: (\d+)\.(\d+) · Tanggal: \d{4}-\d{2}-\d{2}", m_)
    if h: m_ = m_.replace(h.group(0), f"Versi: {h.group(1)}.{int(h.group(2)) + 1} · Tanggal: 2026-10-08", 1)
    shutil.copy(M, str(M) + ".pre-a47.bak"); M.write_text(m_, encoding="utf-8"); print("OK: A-47 ditambahkan ke memori repo")

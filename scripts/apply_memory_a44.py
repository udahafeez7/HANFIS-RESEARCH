#!/usr/bin/env python3
"""Catat A-44 (keputusan desain E7 dan penyelarasan naskah) di HANFIS_RESEARCH_MEMORY.md, dari akar repo. Gagal-tertutup bila baris A-43 tidak ada tepat sekali; idempoten; cadangan .pre-a44.bak."""
import re, shutil, sys
from pathlib import Path
P = Path("HANFIS_RESEARCH_MEMORY.md"); s = P.read_text(encoding="utf-8")
if re.search(r"^\| A-44 \|", s, re.M): print("A-44 sudah ada; tidak ada perubahan."); sys.exit(0)
ROW = ("| A-44 | 2026-10-08 | Eksperimen E7, naskah | Keputusan desain E7 (atas delegasi peneliti; dapat diubah sebelum pembekuan): D2 = 2026-11-09 (7 minggu forward matang, t = 2026-08-31 .. 2026-10-12; minimum 6); "
       "hibrida = satu lambda dari kuadrat terkecil pada prediksi out-of-fold E4 (`scripts/e7_fit_lambda.py`; dibekukan sekali di `protocols/E7_lambda_<tanggal>.json`), diterapkan pada model akhir yang dilatih ulang pada semua minggu berlabel <= 2026-08-24; "
       "P7c primer = non-inferioritas presisi@20% (batas bawah CI95 > -0,05); kontras per strata perubahan x2/KEV dilaporkan tanpa kriteria. Pembekuan = komit + tag `e7-prereg-*` + `scripts/verify_prereg_tag.py` LOLOS "
       "(pelajaran E6); label dan snapshot > 2026-09-21 ditarik dan dihitung hanya setelah tag. Naskah: sub-bagian E6 disisipkan di Results sebelum Discussion (`scripts/apply_e6_manuscript.py`), dan klaim edge, kebijakan, serta "
       "\"interpretable\" diselaraskan: C4 dan kerangka kebijakan = dirancang, belum dievaluasi; H5 tetap future work. |")
m = list(re.finditer(r"^\| A-43 \|.*$", s, re.M))
if len(m) != 1: sys.exit(f"ABORT: baris A-43 ditemukan {len(m)}x (harus 1); tidak ada yang ditulis")
s = s[:m[0].end()] + "\n" + ROW + s[m[0].end():]
h = re.search(r"Versi: (\d+)\.(\d+) · Tanggal: \d{4}-\d{2}-\d{2}", s)
if h: s = s.replace(h.group(0), f"Versi: {h.group(1)}.{int(h.group(2)) + 1} · Tanggal: 2026-10-08", 1)
else: print("PERINGATAN: kepala berkas (Versi/Tanggal) tidak ditemukan; perbarui manual")
shutil.copy(P, str(P) + ".pre-a44.bak"); P.write_text(s, encoding="utf-8"); print("OK: A-44 ditambahkan")

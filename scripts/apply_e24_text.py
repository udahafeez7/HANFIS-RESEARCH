#!/usr/bin/env python3
r"""Menambahkan paragraf E24 (stacking linear HANFIS dengan rumus; post hoc) ke subbagian E21 di manuscript/sn-article.tex, tepat sebelum tabel E21 (sesudah paragraf E23), dan mencatat A-61 di HANFIS_RESEARCH_MEMORY.md (versi 2.35).
Gagal-tertutup: jangkar tabel E21 harus tepat sekali dan didahului paragraf E23; baris A-60 dan kepala 'Versi: 2.34 · Tanggal: 2026-10-14' harus ada tepat sekali (jalankan apply_memory_a60.py dahulu); tidak ada yang ditulis bila salah satunya gagal. Idempoten. Cadangan .pre-e24.bak.
   python scripts/apply_e24_text.py [--tex manuscript/sn-article.tex] [--today 2026-10-14]"""
import argparse, re, shutil, sys
from pathlib import Path
E24 = (r"\emph{Stacking (E24).} Does HANFIS carry information that the formula lacks? We fitted label $=a+b_1\times$ formula $+\,b_2\times$ HANFIS on the rows of the other folds, applied it to each fold in turn (cross-fitted), and compared it with the formula recalibrated in the same way (post hoc; intervals clustered by image). "
       r"On all rows the skill of the combination against the recalibrated formula is $-0.001$ ($-0.006$ to $0.004$); the best case, with coefficients fitted on all rows, is $0.0005$ ($-0.002$ to $0.003$), and the weight of HANFIS is $0.030$ (between folds $0.015$ to $0.052$). Persistence as the second predictor instead of HANFIS gives $0.001$ ($-0.022$ to $0.021$). "
       r"On unaffected rows the values are $-0.002$ ($-0.028$ to $0.017$) for HANFIS and $-0.169$ ($-0.224$ to $-0.005$) for persistence; the second reflects unstable coefficients, since the weights of formula and persistence vary widely between folds when both are included. "
       r"A linear combination of the two predictors therefore does not beat the formula: HANFIS adds no information that a straight line can use.")
ap = argparse.ArgumentParser(); ap.add_argument("--tex", default="manuscript/sn-article.tex"); ap.add_argument("--today", default="2026-10-14"); a = ap.parse_args()
ANCH = "\\begin{table}[ht]\n\\caption{Calibration of the four-week out-of-fold predictions (E21, post hoc)"
T = Path(a.tex); s = T.read_text(encoding="utf-8")
if r"\emph{Recalibration (E23).}" not in s: sys.exit("ABORT, tidak ada yang ditulis: paragraf E23 belum ada di naskah (jalankan apply_e22_fix_e23.py dahulu)")
has_tex = r"\emph{Stacking (E24).}" in s
if not has_tex and s.count(ANCH) != 1: sys.exit(f"ABORT, tidak ada yang ditulis: jangkar tabel E21 ditemukan {s.count(ANCH)}x (harus 1)")
new_s = s if has_tex else s.replace(ANCH, E24 + "\n\n" + ANCH, 1)
M = Path("HANFIS_RESEARCH_MEMORY.md"); m = M.read_text(encoding="utf-8")
ROW = ("| A-61 | " + a.today + " | Eksperimen E24, naskah | E24 (stacking linear silang HANFIS dengan rumus, post hoc, tanpa pelatihan, data lama; label = a + b1 rumus + b2 HANFIS dicocokkan pada lipatan lain; pembanding rumus yang direkalibrasi; bootstrap per image): nilai tambah HANFIS di atas rumus -0,001 [-0,006; 0,004] pada semua baris dan -0,002 [-0,028; 0,017] pada baris bersih; batas dalam-sampel +0,0005 [-0,002; 0,003]; bobot HANFIS 0,030 (antar lipatan 0,015 sampai 0,052); "
       "persistence sebagai prediktor kedua: 0,001 [-0,022; 0,021] semua baris dan -0,169 [-0,224; -0,005] baris bersih karena koefisien rumus dan persistence tidak stabil antar lipatan; rumus yang direkalibrasi silang sendiri lebih buruk daripada rumus mentah (MSE 0,2739 lawan 0,2665), jadi selisih FH terhadap rumus mentah (-0,028) berasal dari rekalibrasi; "
       "kesimpulan: HANFIS tidak menambah informasi yang dapat dipakai secara linear di atas rumus; paragraf E24 ditambahkan ke subbagian E21 (apply_e24_text.py); keluaran results_python/e24/e24_all_rows.txt dan e24_clean_rows.txt (komit ac2890b memuat skripnya) |")
if ROW.count("|") != 5: sys.exit("ABORT: baris A-61 harus berisi tepat 5 pipa")
if re.search(r"^\| A-61 \|", m, re.M): new_m = re.sub(r"^\| A-61 \|.*$", lambda x: ROW, m, count=1, flags=re.M)
else:
    r60 = list(re.finditer(r"^\| A-60 \|.*$", m, re.M)); h = list(re.finditer(r"Versi: 2\.34 \u00b7 Tanggal: 2026-10-14", m))
    if len(r60) != 1 or len(h) != 1: sys.exit(f"ABORT, tidak ada yang ditulis: baris A-60 {len(r60)}x, kepala {len(h)}x (harus 1 dan 1; jalankan apply_memory_a60.py dahulu)")
    new_m = m[:r60[0].end()] + "\n" + ROW + m[r60[0].end():]; new_m = new_m.replace("Versi: 2.34 \u00b7 Tanggal: 2026-10-14", f"Versi: 2.35 \u00b7 Tanggal: {a.today}", 1)
changed = []
for P, old, new, name in ((T, s, new_s, "naskah"), (M, m, new_m, "memori")):
    if new != old: shutil.copy(P, str(P) + ".pre-e24.bak"); P.write_text(new, encoding="utf-8"); changed.append(name)
print("OK: " + ", ".join(changed) if changed else "Tidak ada perubahan (sudah sama).")

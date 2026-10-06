#!/usr/bin/env python3
"""Ganti tabel tab:overhead di sn-article.tex (banyak sel '--', meluap 134.7pt) dengan blok tabel dari
manuscript/results_efficiency.tex (dihasilkan otomatis dari paired_effects_v3.csv) -- tanpa mengetik ulang angka.
tabular -> tabularx{\\textwidth} dengan kolom pertama X agar label panjang membungkus. Gagal-tertutup, idempoten."""
import sys, shutil, pathlib
A = pathlib.Path("manuscript/sn-article.tex"); R = pathlib.Path("manuscript/results_efficiency.tex")
s = A.read_text(encoding="utf-8"); r = R.read_text(encoding="utf-8")
if "\\begin{tabularx}{\\textwidth}{@{}Xrrrr@{}}" in s and "\\label{tab:overhead}" in s:
    print("Sudah diterapkan; tidak ada perubahan."); sys.exit(0)
def one(t, x, name):
    if t.count(x) != 1: sys.exit(f"ABORT: {name}: '{x}' ditemukan {t.count(x)}x (harus 1)")
    return t.index(x)
# blok sumber
ri = one(r, "\\label{tab:overhead}", "results_efficiency")
rb = r.rfind("\\begin{table", 0, ri); re_ = r.index("\\end{table}", ri) + len("\\end{table}")
blk = r[rb:re_]
for x in ("\\begin{tabular}{@{}lrrrr@{}}", "\\end{tabular}"):
    if blk.count(x) != 1: sys.exit(f"ABORT: blok sumber: '{x}' {blk.count(x)}x (harus 1)")
if "\\multicolumn{5}" not in blk or "p$" not in blk: sys.exit("ABORT: blok sumber tidak tampak seperti tabel overhead lengkap")
blk = blk.replace("\\begin{tabular}{@{}lrrrr@{}}", "\\begin{tabularx}{\\textwidth}{@{}Xrrrr@{}}").replace("\\end{tabular}", "\\end{tabularx}")
# blok tujuan
si = one(s, "\\label{tab:overhead}", "sn-article")
sb = s.rfind("\\begin{table*}", 0, si); se = s.index("\\end{table*}", si) + len("\\end{table*}")
if not 0 <= sb < si < se: sys.exit("ABORT: batas tabel tujuan tidak jelas")
shutil.copy(A, str(A) + ".pre-overhead-table.bak")
A.write_text(s[:sb] + blk + s[se:], encoding="utf-8"); print("OK: tab:overhead diganti dari results_efficiency.tex")

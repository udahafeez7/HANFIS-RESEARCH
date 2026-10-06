#!/usr/bin/env python3
"""Perbaiki tiga Overfull \\hbox yang tersisa: tab:rules-params (39pt), persamaan X_v/S_{v,a} (65pt),
dan mind map TikZ (54pt). Hanya tata letak; isi tidak berubah. Gagal-tertutup (tiap jangkar tepat 1x), idempoten."""
import sys, shutil, pathlib
P = pathlib.Path("manuscript/sn-article.tex")
s = P.read_text(encoding="utf-8")
if "\\begin{tabularx}{\\textwidth}{@{}lXcccc@{}}" in s:
    print("Sudah diterapkan; tidak ada perubahan."); sys.exit(0)
def once(x):
    n = s.count(x)
    if n != 1: sys.exit(f"ABORT: jangkar {n}x (harus 1): {x[:70]!r}")
    return s.index(x)
# 1. tabel rules-params: hanya di dalam bloknya
li = once("\\label{tab:rules-params}")
tb = s.index("\\begin{tabular}{@{}lccccc@{}}", li); te = s.index("\\end{tabular}", tb)
if s.count("\\begin{tabular}{@{}lccccc@{}}", li, te + 20) != 1 or tb - li > 200: sys.exit("ABORT: blok tab:rules-params tidak seperti yang diharapkan")
s = s[:tb] + "\\begin{tabularx}{\\textwidth}{@{}lXcccc@{}}" + s[tb + len("\\begin{tabular}{@{}lccccc@{}}"):te] + "\\end{tabularx}" + s[te + len("\\end{tabular}"):]
# 2. persamaan
OLD_EQ = ("\\begin{equation}\nX_v(\\tau)=\\max\\big(\\mathrm{EPSS}_v(\\tau),\\,\\mathbb{1}[v\\in\\mathrm{KEV}(\\tau)]\\big),\\qquad\n"
          "S_{v,a}(\\tau)=\\rho_{v,a}\\cdot\\mathbb{1}[v\\text{ affected and reachable on }a\\text{ at }\\tau],\n\\end{equation}")
NEW_EQ = ("\\begin{equation}\n\\begin{aligned}\nX_v(\\tau)&=\\max\\big(\\mathrm{EPSS}_v(\\tau),\\,\\mathbb{1}[v\\in\\mathrm{KEV}(\\tau)]\\big),\\\\\n"
          "S_{v,a}(\\tau)&=\\rho_{v,a}\\cdot\\mathbb{1}[v\\text{ affected and reachable on }a\\text{ at }\\tau],\n\\end{aligned}\n\\end{equation}")
once(OLD_EQ); s = s.replace(OLD_EQ, NEW_EQ)
# 3. mind map
A1 = "\\centering\n\\begin{tikzpicture}[\n  mindmap,"
A2 = "\\end{tikzpicture}\n\n\\caption{Methodological mind map"
once(A1); once(A2)
s = s.replace(A1, "\\centering\n\\resizebox{\\textwidth}{!}{%\n\\begin{tikzpicture}[\n  mindmap,")
s = s.replace(A2, "\\end{tikzpicture}}\n\n\\caption{Methodological mind map")
shutil.copy(P, str(P) + ".pre-layout.bak")
P.write_text(s, encoding="utf-8"); print("OK")

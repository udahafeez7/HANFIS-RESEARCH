#!/usr/bin/env python3
"""Patch 0073: buang sisa template Springer yang tampil di PDF: (a) blok 'Supplementary information'
(teks gels/blots), (b) blok 'Editorial Policies for:' + kotak komentar presentasi.
Bagian Acknowledgements dan Declarations tidak disentuh. Gagal-tertutup, idempoten."""
import sys, shutil, pathlib
P = pathlib.Path("manuscript/sn-article.tex")
s = P.read_text(encoding="utf-8")
if "\\bmhead{Supplementary information}" not in s and "Editorial Policies for:" not in s:
    print("Sudah diterapkan; tidak ada perubahan."); sys.exit(0)
def once(x):
    if s.count(x) != 1: sys.exit(f"ABORT: jangkar {s.count(x)}x (harus 1): {x[:60]!r}")
    return s.index(x)
# (a)
a0 = once("\\bmhead{Supplementary information}"); a1 = once("\\section*{Acknowledgements}")
if not a0 < a1: sys.exit("ABORT: urutan (a)")
s2 = s[:a0] + s[a1:]
# (b)
p = s2.index("%% For presentation purpose") if s2.count("%% For presentation purpose") == 1 else sys.exit("ABORT: 'presentation purpose' bukan 1x")
b0 = s2.rfind("%%=====", 0, p)
e = "\\end{flushleft}\n"
if s2.count(e) != 1: sys.exit(f"ABORT: \\end{{flushleft}} {s2.count(e)}x")
b1 = s2.index(e) + len(e)
if not (0 <= b0 < p < b1): sys.exit("ABORT: urutan (b)")
s2 = s2[:b0] + s2[b1:]
shutil.copy(P, str(P) + ".pre-0073.bak")
P.write_text(s2, encoding="utf-8"); print("OK")

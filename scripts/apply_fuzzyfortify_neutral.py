#!/usr/bin/env python3
"""Koreksi A-40: buang klaim 'skor terbit Fuzzyfortify tidak dapat direproduksi' (berasal dari port Python yang keliru; aplikasi web asli
mereproduksi level terbit pada 4/4 kasus yang berkeluaran). Alasan sah tidak memakai Fuzzyfortify = input asli tidak tersedia + larangan pemetaan proksi.
Gagal-tertutup (tiap jangkar tepat 1x), idempoten."""
import sys, shutil, pathlib
P = pathlib.Path("manuscript/sn-article.tex"); s = P.read_text(encoding="utf-8")
R = [
 ("a Fuzzyfortify comparison is not claimed because its published benchmark scores could not be reproduced.}",
  "a Fuzzyfortify comparison is not claimed because its native inputs are not available for the present assets.}"),
 ("As an external check, the implementation available to us was\nrun on the five published benchmark cases of the original paper; its scores fall below the published ones\n"
  "in every case, by 5.9 to 21.0 points on the 0--100 scale (mean absolute difference 12.0), and four of the\n"
  "five reproduced scores are identical (49.5). We therefore neither use it as a baseline nor report a\nFuzzyfortify comparison.",
  "We therefore neither use it as a baseline nor report a Fuzzyfortify comparison."),
]
if all(new in s for _, new in R): print("Sudah diterapkan; tidak ada perubahan."); sys.exit(0)
for old, _ in R:
    n = s.count(old)
    if n != 1: sys.exit(f"ABORT: jangkar {n}x (harus 1): {old[:80]!r}")
for old, new in R: s = s.replace(old, new)
shutil.copy(P, str(P) + ".pre-ffneutral.bak"); P.write_text(s, encoding="utf-8"); print("OK")

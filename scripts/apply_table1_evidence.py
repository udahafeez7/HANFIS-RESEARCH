#!/usr/bin/env python3
"""Patch 0068: kolom evidence Tabel 1 (sec. 3.2) diselaraskan ke external-v3.0 (Run 7-16);
tambah jumlah resampel bootstrap (10.000, analyze_pairs.py) di subseksi protokol.
Gagal-tertutup: tiap jangkar tepat 1x, jika tidak, tidak ada yang ditulis. Idempoten."""
import sys, shutil, pathlib
P = pathlib.Path("manuscript/sn-article.tex")
s = P.read_text(encoding="utf-8")
if "Evidence (Runs~7--16)" in s:
    print("Sudah diterapkan; tidak ada perubahan."); sys.exit(0)
R = [
 ("\\textbf{Current evidence}", "\\textbf{Evidence (Runs~7--16)}"),
 ("loss of schedulability & Passed at B4.10 and B4.11A \\\\", "loss of schedulability & Gate passed in all ten pairs \\\\"),
 ("across monitoring conditions & Passed through B4.11B \\\\", "across monitoring conditions & Gate passed in all ten pairs \\\\"),
 ("before and after state transitions & Passed through B4.11B \\\\", "before and after state transitions & Gate passed in all ten pairs \\\\"),
 ("partially deployed stack & Passed at B4.10 and B4.11A \\\\", "partially deployed stack & Gate passed in all ten pairs \\\\"),
 ("residual collector workloads & Passed at B4.11B \\\\", "residual collector workloads & Gate passed in all ten pairs \\\\"),
 ("unrecorded procedural drift between runs & Passed at B4.10 \\\\", "unrecorded procedural drift between runs & Applied to Runs~7--16; two aborted attempts logged as incidents \\\\"),
 ("& Passed at B4.10 and revalidated at B4.11A \\\\", "& SHA-256 manifest retained for each of the ten run archives \\\\"),
 ("time-dependent bias & Run~2 OFF--ON validated \\\\", "time-dependent bias & Five ON--OFF and five OFF--ON pairs \\\\"),
 ("together with a bootstrap confidence interval for the mean difference",
  "together with a 10{,}000-resample bootstrap confidence interval (fixed seed) for the mean difference"),
]
for old, new in R:
    n = s.count(old)
    if n != 1: sys.exit(f"ABORT: jangkar {n}x (harus 1): {old[:70]!r}")
for old, new in R: s = s.replace(old, new)
shutil.copy(P, str(P) + ".pre-0068.bak")
P.write_text(s, encoding="utf-8"); print("OK")

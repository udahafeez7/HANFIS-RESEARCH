#!/usr/bin/env python3
"""Tambah satu kalimat utilisasi node ke paragraf batasan sec. 3 (Validity Safeguards). Angka dari cumulative_effect_summary.csv (jumlah rerata dua node:
229,64 mCPU OFF, 329,00 mCPU ON) dan kapasitas 16 inti logis (docker info 2026-10-08; metadata kolektor v4.2). Gagal-tertutup, idempoten."""
import sys, shutil, pathlib
P = pathlib.Path("manuscript/sn-article.tex"); s = P.read_text(encoding="utf-8")
OLD = "and the two-node topology and P0 workload constrain external validity."
NEW = (OLD + " The two nodes together used on average about 230~mCPU without and 329~mCPU with the monitoring stack, i.e.\\ 1.4\\% and 2.1\\% of the host's 16 logical cores "
       "(capacity from the v4.2 collector metadata and \\texttt{docker info}; it was not logged during Runs~7--16), so the absence of a latency effect was observed at low utilisation "
       "and need not extend to saturated nodes.")
if "1.4\\% and 2.1\\% of the host" in s: print("Sudah diterapkan; tidak ada perubahan."); sys.exit(0)
if s.count(OLD) != 1: sys.exit(f"ABORT: jangkar {s.count(OLD)}x (harus 1)")
shutil.copy(P, str(P) + ".pre-util.bak"); P.write_text(s.replace(OLD, NEW), encoding="utf-8"); print("OK")

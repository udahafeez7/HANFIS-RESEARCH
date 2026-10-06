#!/usr/bin/env python3
"""Perbarui kalimat penutup paragraf H1b di sec. 4.3 agar sesuai dengan analisis rezim di sec. 4.5. Gagal-tertutup, idempoten."""
import sys, shutil, pathlib
P = pathlib.Path("manuscript/sn-article.tex"); s = P.read_text(encoding="utf-8")
OLD = ("and the honest reading is that the strongly autocorrelated label remains the hardest bar\nin this study, not that H1b has failed outright.")
NEW = ("and the honest reading is that the strongly autocorrelated label remains the hardest bar\nin this study. The post hoc analysis in Section~\\ref{subssec4.5} indicates why: HANFIS outperforms persistence\nwhen the label moves and underperforms it when the label is stable.")
if NEW in s: print("Sudah diterapkan; tidak ada perubahan."); sys.exit(0)
if s.count(OLD) != 1: sys.exit(f"ABORT: jangkar {s.count(OLD)}x (harus 1)")
shutil.copy(P, str(P) + ".pre-h1b.bak"); P.write_text(s.replace(OLD, NEW), encoding="utf-8"); print("OK")

#!/usr/bin/env python3
"""Patch kecil: scripts/e4_run.py menyimpan argumen run ke meta_*.json (kunci 'args'), agar run bisa
direproduksi tanpa menebak default. Hanya MENAMBAH satu kunci; tidak mengubah prediksi. Gagal-tertutup, idempoten."""
import sys, shutil, pathlib
P = pathlib.Path("scripts/e4_run.py")
s = P.read_text(encoding="utf-8")
if '"args":' in s and "vars(a)" in s:
    print("Sudah diterapkan; tidak ada perubahan."); sys.exit(0)
OLD = '"saved_models": [] if a.save_models else None}'
NEW = ('"saved_models": [] if a.save_models else None,\n'
       '            "args": {k: (v if isinstance(v, (int, float, str, bool, list, type(None))) else str(v))\n'
       '                     for k, v in vars(a).items()}}')
if s.count(OLD) != 1: sys.exit(f"ABORT: jangkar {s.count(OLD)}x (harus 1)")
shutil.copy(P, str(P) + ".pre-meta-args.bak")
P.write_text(s.replace(OLD, NEW), encoding="utf-8"); print("OK")

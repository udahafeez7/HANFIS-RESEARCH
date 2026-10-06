#!/usr/bin/env python3
"""Patch 0071: tests/test_telemetry_pipeline.py memakai PROJECT_ROOT / "telemetry" (huruf kecil),
folder sebenarnya 'Telemetry' -> ModuleNotFoundError di Linux ext4 (peka huruf besar-kecil).
Gagal-tertutup (tepat 1 kemunculan), idempoten."""
import sys, shutil, pathlib
P = pathlib.Path("tests/test_telemetry_pipeline.py")
s = P.read_text(encoding="utf-8")
OLD, NEW = 'PROJECT_ROOT / "telemetry"', 'PROJECT_ROOT / "Telemetry"'
if NEW in s and OLD not in s:
    print("Sudah diterapkan; tidak ada perubahan."); sys.exit(0)
if s.count(OLD) != 1:
    sys.exit(f"ABORT: jangkar {s.count(OLD)}x (harus 1)")
shutil.copy(P, str(P) + ".pre-0071.bak")
P.write_text(s.replace(OLD, NEW), encoding="utf-8"); print("OK")

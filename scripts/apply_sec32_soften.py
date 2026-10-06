#!/usr/bin/env python3
"""Patch 0070: lunakkan satu kalimat di sec. 3.2 (isi faktual tetap). Gagal-tertutup, idempoten."""
import sys, shutil, pathlib
P = pathlib.Path("manuscript/sn-article.tex")
s = P.read_text(encoding="utf-8")
OLD = ("The first gates of the protocol-development phase (O5--B4.10 to O5--B4.11B) are retained as scripts "
       "but are not used as evidence in this paper, because their original console output cannot be independently re-verified. ")
NEW = ("The first gates of the protocol-development phase (O5--B4.10 to O5--B4.11B) are kept in the repository as scripts "
       "and describe the procedure only; since one of their gate reports could not be reconstructed after the fact, "
       "they are not cited as evidence of passing. ")
if NEW in s: print("Sudah diterapkan; tidak ada perubahan."); sys.exit(0)
if s.count(OLD) != 1: sys.exit(f"ABORT: jangkar {s.count(OLD)}x (harus 1)")
shutil.copy(P, str(P) + ".pre-0070.bak")
P.write_text(s.replace(OLD, NEW), encoding="utf-8"); print("OK")

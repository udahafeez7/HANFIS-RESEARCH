#!/usr/bin/env python3
"""Patch 0072: kalimat basi 'Scaling the inventory toward the 120 images ... open item' (sec. 3.5)
diganti pernyataan bahwa inventaris 120 aset adalah inventaris final. Gagal-tertutup, idempoten."""
import sys, shutil, pathlib
P = pathlib.Path("manuscript/sn-article.tex")
s = P.read_text(encoding="utf-8")
OLD = ("Scaling the inventory toward the\n120 images targeted for the final manuscript remains an open item, tracked as unlikely to change the\n"
       "qualitative confirmatory picture in Section~\\ref{subssec4.3} given the gate margin already achieved.")
NEW = ("The 120-asset inventory described here is the final inventory used for every result in\n"
       "Section~\\ref{sec4}; no further scaling of the inventory is planned for this paper.")
if NEW in s: print("Sudah diterapkan; tidak ada perubahan."); sys.exit(0)
if s.count(OLD) != 1: sys.exit(f"ABORT: jangkar {s.count(OLD)}x (harus 1)")
shutil.copy(P, str(P) + ".pre-0072.bak")
P.write_text(s.replace(OLD, NEW), encoding="utf-8"); print("OK")

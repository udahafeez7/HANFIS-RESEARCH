#!/usr/bin/env python3
"""Tambah DOI hasil verifikasi Crossref (KANDIDAT-OK, semua medan cocok) ke ojha2019heuristic dan lee2003hierarchical.
Gagal-tertutup: kunci tepat 1x; bila entri sudah punya doi yang berbeda -> berhenti. Idempoten."""
import re, sys, shutil, pathlib
P = pathlib.Path("manuscript/sn-bibliography.bib"); s = P.read_text(encoding="utf-8")
ADD = {"ojha2019heuristic": "10.1016/j.engappai.2019.08.010", "lee2003hierarchical": "10.1016/S0165-0114(02)00517-1"}
changed = False
for key, doi in ADD.items():
    ms = list(re.finditer(r"^@\w+\s*\{\s*" + re.escape(key) + r"\s*,", s, re.M))
    if len(ms) != 1: sys.exit(f"ABORT: {key} ditemukan {len(ms)}x (harus 1)")
    st = ms[0].end(); d, j = 1, st
    while j < len(s) and d: d += {"{": 1, "}": -1}.get(s[j], 0); j += 1
    body = s[st:j - 1]
    m = re.search(r"\bdoi\s*=\s*\{([^}]*)\}", body, re.I)
    if m:
        if m.group(1).strip().lower() != doi.lower(): sys.exit(f"ABORT: {key} sudah punya doi berbeda: {m.group(1)}")
        continue
    nb = body.rstrip(); nb = nb if nb.endswith(",") else nb + ","
    s = s[:st] + nb + f"\n  doi = {{{doi}}}\n" + s[j - 1:]; changed = True
if not changed: print("Sudah diterapkan; tidak ada perubahan."); sys.exit(0)
shutil.copy(P, str(P) + ".pre-dois.bak"); P.write_text(s, encoding="utf-8"); print("OK")

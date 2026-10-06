#!/usr/bin/env python3
"""Perbaiki DOI raju1991 dan wang1998hierarchical berdasarkan pencocokan Crossref (judul, penulis, tahun, jurnal,
volume, halaman cocok persis). Gagal-tertutup: DOI lama harus persis sama dengan yang diharapkan. Idempoten."""
import re, sys, shutil, pathlib
P = pathlib.Path("manuscript/sn-bibliography.bib"); s = P.read_text(encoding="utf-8")
FIX = {"raju1991": ("10.1080/00207179108934202", "10.1080/00207179108934205"),
       "wang1998hierarchical": ("10.1016/S0165-0114(96)00218-1", "10.1016/S0165-0114(96)00197-2")}
changed = False
for key, (old, new) in FIX.items():
    ms = list(re.finditer(r"^@\w+\s*\{\s*" + re.escape(key) + r"\s*,", s, re.M))
    if len(ms) != 1: sys.exit(f"ABORT: {key} ditemukan {len(ms)}x (harus 1)")
    st = ms[0].end(); d, j = 1, st
    while j < len(s) and d: d += {"{": 1, "}": -1}.get(s[j], 0); j += 1
    body = s[st:j - 1]; m = re.search(r"(\bdoi\s*=\s*\{)([^}]*)(\})", body, re.I)
    if not m: sys.exit(f"ABORT: {key} tidak punya doi")
    cur = m.group(2).strip()
    if cur.lower() == new.lower(): continue
    if cur.lower() != old.lower(): sys.exit(f"ABORT: {key} doi sekarang '{cur}', bukan '{old}'")
    body = body[:m.start(2)] + new + body[m.end(2):]; s = s[:st] + body + s[j - 1:]; changed = True
if not changed: print("Sudah diterapkan; tidak ada perubahan."); sys.exit(0)
shutil.copy(P, str(P) + ".pre-fixes2.bak"); P.write_text(s, encoding="utf-8"); print("OK")

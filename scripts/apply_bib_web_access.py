#!/usr/bin/env python3
"""Ganti catatan 'verify the access date...' (tercetak di PDF) pada kubernetes_pod_lifecycle_2026 dan tambahkan
tanggal akses pada first_cvss40. Pakai SETELAH Anda benar-benar membuka kedua URL:
  python scripts/apply_bib_web_access.py --accessed 2026-10-06
Gagal-tertutup, idempoten."""
import argparse, datetime, re, sys, shutil, pathlib
ap = argparse.ArgumentParser(); ap.add_argument("--accessed", required=True); a = ap.parse_args()
d = datetime.date.fromisoformat(a.accessed)
M = ["January","February","March","April","May","June","July","August","September","October","November","December"]
txt = f"Accessed {d.day} {M[d.month-1]} {d.year}"
P = pathlib.Path("manuscript/sn-bibliography.bib"); s = P.read_text(encoding="utf-8")
def entry(key):
    ms = list(re.finditer(r"^@\w+\s*\{\s*" + re.escape(key) + r"\s*,", s, re.M))
    if len(ms) != 1: sys.exit(f"ABORT: {key} ditemukan {len(ms)}x (harus 1)")
    st = ms[0].end(); dd, j = 1, st
    while j < len(s) and dd: dd += {"{": 1, "}": -1}.get(s[j], 0); j += 1
    return st, j - 1
changed = False
st, en = entry("kubernetes_pod_lifecycle_2026"); body = s[st:en]
m = re.search(r"(\bnote\s*=\s*\{)([^}]*)(\})", body)
if not m: sys.exit("ABORT: kubernetes entry tanpa note")
if m.group(2) != txt:
    if "verify" not in m.group(2) and not m.group(2).startswith("Accessed"): sys.exit(f"ABORT: note tak dikenal: {m.group(2)!r}")
    body = body[:m.start(2)] + txt + body[m.end(2):]; s = s[:st] + body + s[en:]; changed = True
st, en = entry("first_cvss40"); body = s[st:en]
if not re.search(r"\bnote\s*=", body):
    nb = body.rstrip(); nb = nb if nb.endswith(",") else nb + ","
    s = s[:st] + nb + f"\n  note          = {{{txt}}}\n" + s[en:]; changed = True
if not changed: print("Sudah diterapkan; tidak ada perubahan."); sys.exit(0)
shutil.copy(P, str(P) + ".pre-access.bak"); P.write_text(s, encoding="utf-8"); print("OK:", txt)

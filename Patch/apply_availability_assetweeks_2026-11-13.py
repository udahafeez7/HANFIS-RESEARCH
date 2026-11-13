#!/usr/bin/env python3
r"""apply_availability_assetweeks_2026-11-13.py - tabel asset-week turunan kini ada di arsip Zenodo v2 (HANFIS_asset_week_tables_2026-11-13.tar.gz, 39 berkas dari data/processed).

Lapisan (P1): naskah (pelaporan). Dokumen: manuscript/sn-article.tex. Lanjutan apply_availability_zenodo_v2_2026-11-13.py (harus sudah terpasang).
Teks-persis, gagal-tertutup; idempoten; CRLF dipertahankan; cadangan .pre-assetweeks.bak. Jalankan dari root repo:  python3 Patch/apply_availability_assetweeks_2026-11-13.py
"""
import os, re, sys

P = os.path.join("manuscript", "sn-article.tex")
if not (os.path.isfile(P) and os.path.isdir(".git")):
    sys.exit("ABORT: jalankan dari root repo")
PAIRS = [
 (r"Additional file~1, and the Trivy scan outputs of a subset of the images.",
  r"Additional file~1, the derived asset-week tables from which the analyses were run, and the Trivy scan outputs of a subset of the images."),
 (r"The full set of scan outputs, the derived asset-week tables and the raw telemetry outputs of the ten paired observability-overhead runs (Runs~7--16) are not part of the archive.",
  r"The full set of scan outputs and the raw telemetry outputs of the ten paired observability-overhead runs (Runs~7--16) are not part of the archive."),
]


def rx(text):
    return re.compile(r"\s+".join(re.escape(t) for t in text.split()))


raw = open(P, "rb").read(); crlf = b"\r\n" in raw; s = raw.decode("utf-8").replace("\r\n", "\n")
nrm = lambda z: " ".join(z.split()); state = []
for n, (old, new) in enumerate(PAIRS, 1):
    co, cn = len(rx(old).findall(s)), len(rx(new).findall(s))
    if co == 1 and cn == 0: state.append("old")
    elif cn >= 1 and (co == 0 or nrm(old) in nrm(new)): state.append("new")
    else: sys.exit(f"ABORT: pasangan {n}: teks lama cocok {co} kali, teks baru {cn} kali; tidak ada yang ditulis")
if all(x == "new" for x in state):
    print("SUDAH TERPASANG: semua", len(PAIRS), "suntingan; tidak ada yang ditulis"); sys.exit(0)
if any(x == "new" for x in state):
    sys.exit("ABORT: keadaan campuran; tidak ada yang ditulis")
for n, (old, new) in enumerate(PAIRS, 1):
    s, k = rx(old).subn(lambda m, new=new: new, s, count=1)
    if k != 1: sys.exit(f"ABORT: pasangan {n} gagal; tidak ada yang ditulis")
open(P + ".pre-assetweeks.bak", "wb").write(raw); open(P, "wb").write((s.replace("\n", "\r\n") if crlf else s).encode("utf-8"))
print("OK", len(PAIRS), "suntingan |", "CRLF" if crlf else "LF", "| cadangan", P + ".pre-assetweeks.bak")

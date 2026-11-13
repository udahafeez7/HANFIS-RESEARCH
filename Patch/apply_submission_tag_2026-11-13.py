#!/usr/bin/env python3
r"""apply_submission_tag_2026-11-13.py - Code availability menyebut tag pengiriman manuscript-submission-2026-11.

Lapisan (P1): naskah (pelaporan). Dokumen: manuscript/sn-article.tex. Tag dibuat pada komit yang memuat suntingan ini (komit akhir naskah).
Teks-persis, gagal-tertutup; idempoten; CRLF dipertahankan; cadangan .pre-subtag.bak. Jalankan dari root repo:  python3 Patch/apply_submission_tag_2026-11-13.py
"""
import os, re, sys

P = os.path.join("manuscript", "sn-article.tex")
if not (os.path.isfile(P) and os.path.isdir(".git")):
    sys.exit("ABORT: jalankan dari root repo")
PAIRS = [
 (r"and developed in the public repository \texttt{github.com/udahafeez7/HANFIS-RESEARCH}.",
  r"and developed in the public repository \texttt{github.com/udahafeez7/HANFIS-RESEARCH}, where the tag \texttt{manuscript-submission-2026-11} marks the submitted version."),
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
    print("SUDAH TERPASANG; tidak ada yang ditulis"); sys.exit(0)
for n, (old, new) in enumerate(PAIRS, 1):
    s, k = rx(old).subn(lambda m, new=new: new, s, count=1)
    if k != 1: sys.exit(f"ABORT: pasangan {n} gagal")
open(P + ".pre-subtag.bak", "wb").write(raw); open(P, "wb").write((s.replace("\n", "\r\n") if crlf else s).encode("utf-8"))
print("OK", len(PAIRS), "suntingan |", "CRLF" if crlf else "LF")

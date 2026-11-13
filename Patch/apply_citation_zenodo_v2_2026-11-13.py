#!/usr/bin/env python3
r"""apply_citation_zenodo_v2_2026-11-13.py - CITATION.cff dan README.md ke Zenodo v2.0 (DOI 10.5281/zenodo.24133609, terbit; doi.org membalas HTTP 200 pada 2026-11-13).

Lapisan (P1): prosedur mutu (arsip dan sitasi). Dokumen: CITATION.cff, README.md. Bukan berkas beku E7.
Teks-persis, gagal-tertutup; idempoten; CRLF dipertahankan; cadangan .pre-zenodov2.bak. Jalankan dari root repo:  python3 Patch/apply_citation_zenodo_v2_2026-11-13.py
"""
import os, re, sys

if not os.path.isdir(".git"):
    sys.exit("ABORT: jalankan dari root repo")
FILES = {
 "CITATION.cff": [
  ('title: "HANFIS-RESEARCH: code, frozen evaluation protocol and derived data for hierarchical neuro-fuzzy risk scoring of Kubernetes deployments"\nversion: "v1.0"\ndate-released: "2026-10-14"\ndoi: "10.5281/zenodo.23357118"',
   'title: "HANFIS-RESEARCH: code, frozen evaluation protocols, saved models and results for hierarchical neuro-fuzzy risk scoring of Kubernetes deployments"\nversion: "v2.0"\ndate-released: "2026-11-11"\ndoi: "10.5281/zenodo.24133609"'),
 ],
 "README.md": [
  ("**Status:** research code under active development; private during review; archived at Zenodo (DOI 10.5281/zenodo.23357118).",
   "**Status:** research code, public; archived at Zenodo (version 2.0, DOI 10.5281/zenodo.24133609; all versions 10.5281/zenodo.23357117)."),
  ("Archived copy: https://doi.org/10.5281/zenodo.23357118 (open access). Please cite the manuscript once it is available.",
   "Archived copy: https://doi.org/10.5281/zenodo.24133609 (version 2.0, open access; version 1.0 is https://doi.org/10.5281/zenodo.23357118). Please cite the manuscript once it is available."),
 ],
}


def rx(text):
    return re.compile(r"\s+".join(re.escape(t) for t in text.split()))


plan, nrm = [], (lambda z: " ".join(z.split()))
for path, pairs in FILES.items():
    raw = open(path, "rb").read(); crlf = b"\r\n" in raw; s = raw.decode("utf-8").replace("\r\n", "\n"); state = []
    for n, (old, new) in enumerate(pairs, 1):
        co, cn = len(rx(old).findall(s)), len(rx(new).findall(s))
        if co == 1 and cn == 0: state.append("old")
        elif cn >= 1 and (co == 0 or nrm(old) in nrm(new)): state.append("new")
        else: sys.exit(f"ABORT: {path} pasangan {n}: teks lama cocok {co} kali, teks baru {cn} kali; tidak ada yang ditulis")
    plan.append((path, pairs, raw, crlf, s, state))
allstate = [x for p in plan for x in p[5]]
if all(x == "new" for x in allstate):
    print("SUDAH TERPASANG; tidak ada yang ditulis"); sys.exit(0)
if any(x == "new" for x in allstate):
    sys.exit("ABORT: keadaan campuran; tidak ada yang ditulis")
for path, pairs, raw, crlf, s, _ in plan:
    for n, (old, new) in enumerate(pairs, 1):
        s, k = rx(old).subn(lambda m, new=new: new, s, count=1)
        if k != 1: sys.exit(f"ABORT: {path} pasangan {n} gagal")
    open(path + ".pre-zenodov2.bak", "wb").write(raw); open(path, "wb").write((s.replace("\n", "\r\n") if crlf else s).encode("utf-8"))
    print("OK", path, "|", "CRLF" if crlf else "LF")

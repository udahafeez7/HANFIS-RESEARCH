#!/usr/bin/env python3
r"""Mencatat arsip Zenodo pada pernyataan 'Data availability' dan 'Code availability' di manuscript/sn-article.tex dan pada README.md, setelah DOI Zenodo ada (boleh DOI cadangan/reserved dari draf).
--access open        : rekaman terbuka.   --access restricted : rekaman dibatasi/embargo sampai terbit; pengulas dapat meminta akses.
Gagal-tertutup: tepat satu baris 'Data availability' dan satu 'Code availability' di naskah, dan kalimat README (asli atau hasil skrip ini) harus ada tepat sekali; tidak ada yang ditulis bila salah satu gagal. Idempoten; DOI/pilihan akses dapat diganti dengan menjalankan ulang. Cadangan .pre-zenodo.bak.
   python scripts/apply_zenodo_doi.py --doi 10.5281/zenodo.1234567 [--access open|restricted] [--tex manuscript/sn-article.tex] [--readme README.md]"""
import argparse, re, shutil, sys
from pathlib import Path
ap = argparse.ArgumentParser(); ap.add_argument("--doi", required=True); ap.add_argument("--access", choices=["open", "restricted"], default="open")
ap.add_argument("--tex", default="manuscript/sn-article.tex"); ap.add_argument("--readme", default="README.md"); a = ap.parse_args()
if not re.fullmatch(r"10\.5281/zenodo\.\d{4,10}", a.doi): sys.exit("ABORT: --doi harus berbentuk 10.5281/zenodo.<angka> (tanpa https://doi.org/)")
OSF = r"10.17605/OSF.IO/AHCVS"
acc = "" if a.access == "open" else r"; access is restricted until publication and is granted to reviewers on request"
DATA = (r"\item \textbf{Data availability.} The sealed EPSS/KEV evidence manifests, container-image vulnerability scan bundles, derived asset-week tables, frozen model files and analysis scripts are archived at Zenodo (DOI \texttt{" + a.doi + "}" + acc + r"); the forward-evaluation protocol is registered at the Open Science Framework (DOI \texttt{" + OSF + r"}). Redistribution of the underlying EPSS and CISA KEV feeds follows their licensing terms.")
CODE = (r"\item \textbf{Code availability.} The HANFIS implementation, data pipeline and experiment scripts are archived at Zenodo (DOI \texttt{" + a.doi + "}" + acc + r") and developed at \texttt{udahafeez7/HANFIS-RESEARCH} (private during review).")
T = Path(a.tex); s = T.read_text(encoding="utf-8"); R = Path(a.readme); r = R.read_text(encoding="utf-8")
rx = lambda name: re.compile(r"^\\item \\textbf\{" + name + r"\.\}.*$", re.M)
cd, cc = rx("Data availability").findall(s), rx("Code availability").findall(s)
if len(cd) != 1 or len(cc) != 1: sys.exit(f"ABORT, tidak ada yang ditulis: baris Data availability {len(cd)}x, Code availability {len(cc)}x (harus 1 dan 1)")
ORIG = "An archived copy with a DOI is planned. Until it exists, please do not cite this repository; cite the manuscript once it is available."
NEWR = f"Archived copy: https://doi.org/{a.doi} ({'open access' if a.access == 'open' else 'restricted access until publication'}). Please cite the manuscript once it is available."
RXR = re.compile(r"Archived copy: https://doi\.org/10\.5281/zenodo\.\d+ \([a-z ]+\)\. Please cite the manuscript once it is available\.")
nr = r.count(ORIG) + len(RXR.findall(r))
if nr != 1: sys.exit(f"ABORT, tidak ada yang ditulis: kalimat README ditemukan {nr}x (harus 1)")
s2 = rx("Data availability").sub(lambda m: DATA, s, count=1); s2 = rx("Code availability").sub(lambda m: CODE, s2, count=1)
r2 = r.replace(ORIG, NEWR, 1) if ORIG in r else RXR.sub(lambda m: NEWR, r, count=1)
if s2 == s and r2 == r: print("Tidak ada perubahan (sudah sama)."); sys.exit(0)
if s2 != s: shutil.copy(T, str(T) + ".pre-zenodo.bak"); T.write_text(s2, encoding="utf-8")
if r2 != r: shutil.copy(R, str(R) + ".pre-zenodo.bak"); R.write_text(r2, encoding="utf-8")
print(f"OK: DOI {a.doi} ({a.access}) dicatat di naskah dan README")

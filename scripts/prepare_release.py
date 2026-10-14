#!/usr/bin/env python3
r"""Menyiapkan berkas rilis untuk arsip Zenodo: (1) README.md (baris Status dan bagian License), (2) LICENSE untuk kode, (3) CITATION.cff dengan DOI Zenodo yang sudah dipesan.
Kode: --code apache (butuh berkas LICENSE berisi teks Apache-2.0; bila belum ada, skrip mencoba mengunduhnya dari apache.org) atau --code mit (menulis LICENSE).
Data, dokumentasi, protokol, dan teks naskah: CC BY 4.0 (dinyatakan di README dan CITATION.cff).
Gagal-tertutup: semua jangkar README harus ada (asli atau hasil skrip ini) tepat sekali; LICENSE/CITATION.cff yang sudah ada dan berbeda tidak ditimpa tanpa --force; tidak ada yang ditulis bila salah satu gagal. Idempoten. Cadangan README.pre-release.bak.
   python scripts/prepare_release.py --code apache|mit --doi 10.5281/zenodo.NNNNNNN [--date 2026-10-14] [--version v1.0] [--force]"""
import argparse, re, shutil, sys, urllib.request
from pathlib import Path
ap = argparse.ArgumentParser(); ap.add_argument("--code", required=True, choices=["apache", "mit"]); ap.add_argument("--doi", required=True); ap.add_argument("--date", default="2026-10-14")
ap.add_argument("--version", default="v1.0"); ap.add_argument("--readme", default="README.md"); ap.add_argument("--force", action="store_true"); a = ap.parse_args()
if not re.fullmatch(r"10\.5281/zenodo\.\d{4,10}", a.doi): sys.exit("ABORT: --doi harus berbentuk 10.5281/zenodo.<angka> (tanpa https://doi.org/)")
NAME = {"apache": "Apache License 2.0", "mit": "MIT License"}[a.code]; SPDX = {"apache": "Apache-2.0", "mit": "MIT"}[a.code]
R = Path(a.readme); r = R.read_text(encoding="utf-8")
ST_OLD = "**Status:** research code under active development; private repository; no reuse license yet (see [License](#license-and-citation))."
ST_NEW = f"**Status:** research code under active development; private during review; archived at Zenodo (DOI {a.doi}). Licenses: see [License](#license-and-citation)."
LC_OLD = "<!-- TODO: choose a code license and decide what applies to data and derived artifacts before the repository is made public -->"
LC_NEW = (f"Code: {NAME} (see `LICENSE`). Documentation, protocols, derived data tables and manuscript text: Creative Commons Attribution 4.0 International (https://creativecommons.org/licenses/by/4.0/). "
          "The underlying EPSS scores and CISA KEV catalog follow the terms of their providers, and third-party files (for example the kube-prometheus-stack default values) keep their own licenses.")
LC_RX = re.compile(r"^Code: (Apache License 2\.0|MIT License) \(see `LICENSE`\)\. Documentation, protocols.*$", re.M)
ST_RX = re.compile(r"^\*\*Status:\*\* research code under active development; private during review; archived at Zenodo \(DOI 10\.5281/zenodo\.\d+\)\. Licenses: see \[License\]\(#license-and-citation\)\.$", re.M)
n_st = r.count(ST_OLD) + len(ST_RX.findall(r)); n_lc = r.count(LC_OLD) + len(LC_RX.findall(r))
if n_st != 1 or n_lc != 1: sys.exit(f"ABORT, tidak ada yang ditulis: baris Status {n_st}x, bagian License {n_lc}x (harus 1 dan 1)")
r2 = r.replace(ST_OLD, ST_NEW, 1) if ST_OLD in r else ST_RX.sub(lambda m: ST_NEW, r, count=1)
r2 = r2.replace(LC_OLD, LC_NEW, 1) if LC_OLD in r2 else LC_RX.sub(lambda m: LC_NEW, r2, count=1)
LIC = Path("LICENSE")
MIT = ("MIT License\n\nCopyright (c) 2026 The HANFIS-RESEARCH authors (Mohammad Hafiz Hersyah, Derisma, Budi Rahmadya)\n\n"
       "Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the \"Software\"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:\n\n"
       "The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.\n\n"
       "THE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.\n")
lic_text = None
if a.code == "mit":
    if LIC.exists() and LIC.read_text(encoding="utf-8") != MIT and not a.force: sys.exit("ABORT: LICENSE sudah ada dan berbeda dari teks MIT (gunakan --force untuk menimpa)")
    lic_text = MIT
else:
    if LIC.exists():
        t = LIC.read_text(encoding="utf-8")
        if "Apache License" not in t or "Version 2.0" not in t: sys.exit("ABORT: LICENSE ada tetapi bukan teks Apache-2.0 (gunakan --force dengan teks yang benar, atau hapus berkas itu)")
    else:
        try: t = urllib.request.urlopen("https://www.apache.org/licenses/LICENSE-2.0.txt", timeout=30).read().decode("utf-8")
        except Exception as e: sys.exit(f"ABORT: tidak bisa mengunduh teks Apache-2.0 ({e}); jalankan: curl -sSfL https://www.apache.org/licenses/LICENSE-2.0.txt -o LICENSE")
        if "Apache License" not in t or "Version 2.0" not in t or len(t) < 9000: sys.exit("ABORT: unduhan bukan teks Apache-2.0 yang utuh")
        lic_text = t
CFF = (f'cff-version: 1.2.0\nmessage: "If you use this repository, please cite it as below, and cite the manuscript once it is available."\n'
       'title: "HANFIS-RESEARCH: code, frozen evaluation protocol and derived data for hierarchical neuro-fuzzy risk scoring of Kubernetes deployments"\n'
       f'version: "{a.version}"\ndate-released: "{a.date}"\ndoi: "{a.doi}"\n'
       'authors:\n  - family-names: "Hersyah"\n    given-names: "Mohammad Hafiz"\n    affiliation: "Universitas Andalas"\n    orcid: "https://orcid.org/0000-0001-5985-6821"\n'
       '  - family-names: "Derisma"\n    given-names: "Derisma"\n    affiliation: "Universitas Andalas"\n'
       '  - family-names: "Rahmadya"\n    given-names: "Budi"\n    affiliation: "Universitas Andalas"\n'
       'repository-code: "https://github.com/udahafeez7/HANFIS-RESEARCH"\n'
       f'license:\n  - "{SPDX}"\n  - "CC-BY-4.0"\n'
       'identifiers:\n  - type: doi\n    value: "10.17605/OSF.IO/AHCVS"\n    description: "OSF registration of the forward-evaluation protocol (E7)"\n')
CF = Path("CITATION.cff")
if CF.exists() and CF.read_text(encoding="utf-8") != CFF and not a.force: sys.exit("ABORT: CITATION.cff sudah ada dan berbeda (gunakan --force untuk menimpa)")
changed = []
if r2 != r: shutil.copy(R, str(R) + ".pre-release.bak"); R.write_text(r2, encoding="utf-8"); changed.append("README")
if lic_text is not None and (not LIC.exists() or LIC.read_text(encoding="utf-8") != lic_text): LIC.write_text(lic_text, encoding="utf-8"); changed.append("LICENSE")
if not CF.exists() or CF.read_text(encoding="utf-8") != CFF: CF.write_text(CFF, encoding="utf-8"); changed.append("CITATION.cff")
print("OK: " + ", ".join(changed) if changed else "Tidak ada perubahan (sudah sama).")

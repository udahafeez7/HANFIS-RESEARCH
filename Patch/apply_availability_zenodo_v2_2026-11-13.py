#!/usr/bin/env python3
r"""apply_availability_zenodo_v2_2026-11-13.py - pernyataan Availability dan Code availability sesuai isi arsip Zenodo v2 (DOI cadangan 10.5281/zenodo.24133609).

Lapisan (P1): naskah (pelaporan). Dokumen: manuscript/sn-article.tex.
Isi arsip v2 (diperiksa dari zip kode komit 4d82bea dan tarball hasil): protokol beku, manifes SHA-256 snapshot, 25 model E4-bis, lima model akhir E7 dan keluaran D2,
hasil E25 sampai E27, Additional file 1, sebagian keluaran Trivy (15 image). Tidak ada: berkas snapshot EPSS/KEV (tidak boleh didistribusikan ulang, keputusan peneliti 2026-11-13),
keluaran Trivy lengkap, tabel asset-week turunan, keluaran mentah telemetri Runs 7-16. Repositori GitHub dibuat publik (keputusan peneliti); kalimat 'private during review' dihapus.
Teks-persis, gagal-tertutup; idempoten; CRLF dipertahankan; cadangan .pre-zenodov2.bak. Jalankan dari root repo:  python3 Patch/apply_availability_zenodo_v2_2026-11-13.py
"""
import os, re, sys

P = os.path.join("manuscript", "sn-article.tex")
if not (os.path.isfile(P) and os.path.isdir(".git")):
    sys.exit("ABORT: jalankan dari root repo")

PAIRS = [
 (r"\item \textbf{Availability of data and materials.} The sealed EPSS/KEV evidence manifests, container-image vulnerability scan bundles, derived asset-week tables, frozen model files and analysis scripts are archived at Zenodo (DOI \texttt{10.5281/zenodo.23357118}); the forward-evaluation protocol is registered at the Open Science Framework (DOI \texttt{10.17605/OSF.IO/AHCVS}). Redistribution of the underlying EPSS and CISA KEV feeds follows their licensing terms. The raw telemetry outputs of the ten paired observability-overhead runs (Runs~7--16) are not included in version~1.0 of that record and will be deposited with a later version.",
  r"\item \textbf{Availability of data and materials.} The Zenodo archive (version 2.0, DOI \texttt{10.5281/zenodo.24133609}; version 1.0 is \texttt{10.5281/zenodo.23357118}) holds the frozen protocols, the SHA-256 manifests of the sealed weekly EPSS snapshots and of the KEV catalogue, the 25 saved models of the confirmatory run, the five final models and the outputs of the forward evaluation, the results of the computational-cost measurement and of the two post hoc analyses of Sections~\ref{subsec:e25} to~\ref{subsec:e27}, Additional file~1, and the Trivy scan outputs of a subset of the images. The weekly EPSS and KEV snapshot files are not redistributed; they can be obtained from their publishers and checked against the manifests. The full set of scan outputs, the derived asset-week tables and the raw telemetry outputs of the ten paired observability-overhead runs (Runs~7--16) are not part of the archive. The forward-evaluation protocol is registered at the Open Science Framework~\cite{osf_ahcvs}."),
 (r"\item \textbf{Code availability.} The HANFIS implementation, data pipeline and experiment scripts are archived at Zenodo (DOI \texttt{10.5281/zenodo.23357118}) and developed at \texttt{udahafeez7/HANFIS-RESEARCH} (private during review).",
  r"\item \textbf{Code availability.} The HANFIS implementation, data pipeline and experiment scripts are archived at Zenodo (DOI \texttt{10.5281/zenodo.24133609}) and developed in the public repository \texttt{github.com/udahafeez7/HANFIS-RESEARCH}."),
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
open(P + ".pre-zenodov2.bak", "wb").write(raw); open(P, "wb").write((s.replace("\n", "\r\n") if crlf else s).encode("utf-8"))
print("OK", len(PAIRS), "suntingan |", "CRLF" if crlf else "LF", "| cadangan", P + ".pre-zenodov2.bak")

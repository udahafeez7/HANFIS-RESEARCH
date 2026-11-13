#!/usr/bin/env python3
r"""apply_final_checks_2026-11-13.py - dua temuan pemeriksaan akhir sebelum kirim.

Lapisan (P1): naskah (pelaporan). Dokumen: manuscript/sn-article.tex, manuscript/sn-bibliography.bib.
(1) Abstrak: interval dan skill ditulis dengan tiga desimal persis seperti Table tab:e9 (-0.135, [-0.336, 0.046]; -0.534, [-1.438, -0.208]) agar
    setiap angka abstrak terlacak huruf demi huruf ke tabel badan (pembulatan dua desimal 0.14/0.34/0.53/1.44/0.21 tidak ada di tabel). Jumlah kata tetap.
(2) Entri bib osf_ahcvs: judul disamakan dengan judul registrasi di OSF/Crossref ('HANFIS prospective evaluation (E7)'), bukan judul karangan.
Teks-persis, gagal-tertutup; idempoten; CRLF dipertahankan; cadangan .pre-finalchk.bak. Jalankan dari root repo:  python3 Patch/apply_final_checks_2026-11-13.py
"""
import os, re, sys

if not os.path.isdir(".git"):
    sys.exit("ABORT: jalankan dari root repo")
FILES = {
 os.path.join("manuscript", "sn-article.tex"): [
  (r"without them HANFIS has no skill over CVSS (skill $-0.14$, interval $-0.34$ to $0.05$).",
   r"without them HANFIS has no skill over CVSS (skill $-0.135$, interval $-0.336$ to $0.046$)."),
  (r"beats HANFIS at four weeks (skill $-0.53$, interval $-1.44$ to $-0.21$).",
   r"beats HANFIS at four weeks (skill $-0.534$, interval $-1.438$ to $-0.208$)."),
 ],
 os.path.join("manuscript", "sn-bibliography.bib"): [
  ("  title = {{HANFIS} forward evaluation ({E7}): pre-registered protocol},\n  howpublished = {Open Science Framework registration},",
   "  title = {{HANFIS} prospective evaluation ({E7})},\n  howpublished = {Open Science Framework registration of the pre-registered forward-evaluation protocol},"),
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
    open(path + ".pre-finalchk.bak", "wb").write(raw); open(path, "wb").write((s.replace("\n", "\r\n") if crlf else s).encode("utf-8"))
    print("OK", path, "|", "CRLF" if crlf else "LF")

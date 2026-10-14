#!/usr/bin/env python3
"""Amandemen A-60 pada HANFIS_RESEARCH_MEMORY.md: arsip Zenodo terbit (publik) pada 2026-10-14; versi 2.34. Dijalankan lagi memperbarui baris A-60 yang sama.
Gagal-tertutup (baris A-59 dan kepala 'Versi: 2.33 · Tanggal: 2026-10-14' harus ada tepat sekali); cadangan .pre-a60.bak.
   python scripts/apply_memory_a60.py --commit 534de7d [--md5 <32 heks>] [--sha256 <heks>] [--today 2026-10-14]"""
import argparse, re, shutil, sys
from pathlib import Path
ap = argparse.ArgumentParser(); ap.add_argument("--commit", required=True); ap.add_argument("--md5", default=None); ap.add_argument("--sha256", default=None); ap.add_argument("--today", default="2026-10-14"); a = ap.parse_args()
if not re.fullmatch(r"[0-9a-f]{7,12}", a.commit): sys.exit("ABORT: --commit harus 7 sampai 12 karakter heksadesimal huruf kecil")
if a.md5 and not re.fullmatch(r"[0-9a-f]{32}", a.md5): sys.exit("ABORT: --md5 harus 32 karakter heksadesimal huruf kecil")
if a.sha256 and not re.fullmatch(r"[0-9a-f]{16,64}", a.sha256): sys.exit("ABORT: --sha256 harus 16 sampai 64 karakter heksadesimal huruf kecil")
P = Path("HANFIS_RESEARCH_MEMORY.md"); s = P.read_text(encoding="utf-8")
extra = (f"; md5 {a.md5}" if a.md5 else "") + (f"; sha256 {a.sha256}" if a.sha256 else "")
ROW = ("| A-60 | " + a.today + " | Arsip, Zenodo | Arsip Zenodo terbit dan publik (Open) pada 2026-10-14: versi v1.0, DOI versi 10.5281/zenodo.23357118, DOI semua versi 10.5281/zenodo.23357117 (resolve ke versi terbaru); berkas HANFIS-RESEARCH_" + a.commit + ".zip (komit " + a.commit + ", cabang research/amend-a02-a06, 5,8 MB" + extra + "); "
       "penulis Hersyah, Derisma, Rahmadya; lisensi CC BY 4.0 dan Apache-2.0; related works: registrasi OSF 10.17605/OSF.IO/AHCVS; Data availability, Code availability, README, dan CITATION.cff memuat DOI versi; berkas tidak dapat diubah setelah terbit, perubahan lewat versi baru; hasil D2 (2026-11-02) akan diarsipkan sebagai versi baru dari rekaman yang sama |")
if ROW.count("|") != 5: sys.exit("ABORT: baris A-60 harus berisi tepat 5 pipa")
if re.search(r"^\| A-60 \|", s, re.M): new = re.sub(r"^\| A-60 \|.*$", lambda m: ROW, s, count=1, flags=re.M); msg = "baris A-60 diperbarui"
else:
    r59 = list(re.finditer(r"^\| A-59 \|.*$", s, re.M)); h = list(re.finditer(r"Versi: 2\.33 \u00b7 Tanggal: 2026-10-14", s))
    if len(r59) != 1 or len(h) != 1: sys.exit(f"ABORT, tidak ada yang ditulis: baris A-59 {len(r59)}x, kepala {len(h)}x (harus 1 dan 1)")
    new = s[:r59[0].end()] + "\n" + ROW + s[r59[0].end():]; new = new.replace("Versi: 2.33 \u00b7 Tanggal: 2026-10-14", f"Versi: 2.34 \u00b7 Tanggal: {a.today}", 1); msg = "A-60 ditambahkan; versi 2.34"
if new == s: print("Tidak ada perubahan."); sys.exit(0)
shutil.copy(P, str(P) + ".pre-a60.bak"); P.write_text(new, encoding="utf-8"); print("OK:", msg)

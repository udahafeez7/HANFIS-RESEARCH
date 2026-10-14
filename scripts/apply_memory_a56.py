#!/usr/bin/env python3
"""Amandemen A-56 pada HANFIS_RESEARCH_MEMORY.md: registrasi OSF E7 (versi 2.30). Dijalankan dengan --url (dan --doi). Dijalankan lagi memperbarui baris A-56 yang sama.
Gagal-tertutup (baris A-55 dan kepala harus ada tepat sekali); cadangan .pre-a56.bak.
  python scripts/apply_memory_a56.py --url https://osf.io/ahcvs/ [--doi 10.17605/OSF.IO/AHCVS] [--time '2026-10-13 13:46 (+0700)'] [--project https://osf.io/62vq4] [--today 2026-10-14]"""
import argparse, re, shutil, sys
from pathlib import Path
ap = argparse.ArgumentParser(); ap.add_argument("--url", required=True); ap.add_argument("--doi", default=None); ap.add_argument("--time", default="2026-10-13 13:46 (+0700)")
ap.add_argument("--project", default="https://osf.io/62vq4"); ap.add_argument("--today", default="2026-10-14"); a = ap.parse_args()
if not re.fullmatch(r"https://osf\.io/[A-Za-z0-9]{3,10}/?", a.url): sys.exit("ABORT: --url harus berbentuk https://osf.io/<kode>")
if a.url.rstrip("/").split("/")[-1].lower() in ("9ezg4", "62vq4"): sys.exit("ABORT: kode itu adalah proyek (9ezg4 atau 62vq4), bukan registrasi; gunakan https://osf.io/ahcvs/")
if a.doi and not re.fullmatch(r"10\.\d{4,9}/[A-Za-z0-9._/-]+", a.doi): sys.exit("ABORT: --doi tidak berbentuk DOI (mis. 10.17605/OSF.IO/ABCDE)")
P = Path("HANFIS_RESEARCH_MEMORY.md"); s = P.read_text(encoding="utf-8")
ROW = (f"| A-56 | {a.time[:10]} | Eksperimen E7, registrasi | E7 didaftarkan secara publik di OSF (OSF Preregistration, registry OSF Registries; registrasi {a.url}; DOI {a.doi if a.doi else 'belum ada'}; proyek terkait {a.project}) pada {a.time}, "
       "sesudah tag e7-prereg-2026-10-12 (2026-10-12 15:04:42 +0700) dan sebelum D2 (2026-11-02); percobaan pertama (diinisiasi 2026-10-12 16:59 +0700, draf 6acca8dcad5cbbc6a330cf43, proyek 9ezg4) tidak selesai dan diganti atas saran OSF Support; "
       "Foreknowledge opsi 6 (penulis telah melihat data tetapi belum menjalankan analisis yang diusulkan); jenis studi non-acak prospektif; analisis pasca-beku E15 sampai E20 diungkap dalam registrasi, sedangkan E14c (commit 1b6bbf7, sesudah pembekuan) tidak tercantum dan diungkap di naskah; "
       "berkas protokol dan catatan pembekuan (SHA-256 dari 23 berkas) terlampir; analisis berikutnya (E21 dan seterusnya) dijalankan setelah registrasi |")
if re.search(r"^\| A-56 \|", s, re.M):
    new = re.sub(r"^\| A-56 \|.*$", lambda m: ROW, s, count=1, flags=re.M); msg = "baris A-56 diperbarui"
else:
    m = list(re.finditer(r"^\| A-55 \|.*$", s, re.M)); h = list(re.finditer(r"Versi: 2\.29 \u00b7 Tanggal: 2026-10-12", s))
    if len(m) != 1 or len(h) != 1: sys.exit(f"ABORT, tidak ada yang ditulis: baris A-55 {len(m)}x, kepala {len(h)}x (harus 1 dan 1)")
    new = s[:m[0].end()] + "\n" + ROW + s[m[0].end():]; new = new.replace("Versi: 2.29 \u00b7 Tanggal: 2026-10-12", f"Versi: 2.30 \u00b7 Tanggal: {a.today}", 1); msg = "A-56 ditambahkan; versi 2.30"
if new == s: print("Tidak ada perubahan."); sys.exit(0)
shutil.copy(P, str(P) + ".pre-a56.bak"); P.write_text(new, encoding="utf-8"); print("OK:", msg)

#!/usr/bin/env python3
"""Memperbaiki dua kesalahan pada referensi HANFIS terdahulu (Soozanchi-K. dkk., 2010) setelah apply_soozanchi_ref.py:
(1) entri BibTeX menukar judul buku dan seri (Crossref mendaftar seri lebih dulu): seharusnya booktitle = Artificial Intelligence in Theory and Practice III dan series = IFIP Advances in Information and Communication Technology;
(2) baris A-59 di HANFIS_RESEARCH_MEMORY.md menyebut dua penulis; metadata Crossref memuat empat (Soozanchi-K., Akbarzadeh-T., Yaghoobi, Rahati).
Gagal-tertutup: entri soozanchi2010hanfis harus ada dengan pasangan baris lama atau baru tepat satu kali, dan baris A-59 tepat sekali; tidak ada yang ditulis bila salah satunya gagal. Idempoten. Cadangan .pre-soozfix.bak.
   python scripts/fix_soozanchi_ref.py [--today 2026-10-14]"""
import argparse, re, shutil, sys
from pathlib import Path
ap = argparse.ArgumentParser(); ap.add_argument("--bib", default="manuscript/sn-bibliography.bib"); ap.add_argument("--today", default="2026-10-14"); a = ap.parse_args()
KEY = "soozanchi2010hanfis"
OLD = "  booktitle = {IFIP Advances in Information and Communication Technology},\n  series = {Artificial Intelligence in Theory and Practice III},"
NEW = "  booktitle = {Artificial Intelligence in Theory and Practice III},\n  series = {IFIP Advances in Information and Communication Technology},"
B = Path(a.bib); b = B.read_text(encoding="utf-8")
ents = list(re.finditer(r"@\w+\{" + KEY + r",.*?\n\}", b, re.S))
if len(ents) != 1: sys.exit(f"ABORT, tidak ada yang ditulis: entri {KEY} ditemukan {len(ents)}x (harus 1)")
e = ents[0].group(0); n_old, n_new = e.count(OLD), e.count(NEW)
if n_old + n_new != 1: sys.exit(f"ABORT, tidak ada yang ditulis: pasangan booktitle/series ditemukan lama {n_old}x, baru {n_new}x (harus 1 total)")
new_b = b if n_new else b.replace(e, e.replace(OLD, NEW, 1), 1)
M = Path("HANFIS_RESEARCH_MEMORY.md"); m = M.read_text(encoding="utf-8")
ROW = ("| A-59 | " + a.today + " | Naskah, referensi | Referensi HANFIS terdahulu diverifikasi lewat Crossref: Soozanchi-K., Akbarzadeh-T., Yaghoobi dan Rahati (2010), Speaker Verification System Using a Hierarchical Adaptive Network-Based Fuzzy Inference Systems (HANFIS), dalam Artificial Intelligence in Theory and Practice III (IFIP AICT, Springer), hlm. 233-237, DOI 10.1007/978-3-642-15286-3_23; "
       "makalah itu tentang verifikasi penutur dengan tiga kelompok fitur suara, BUKAN fitur kerentanan; kalimat naskah yang menyebut vulnerability-adjacent features dan tidak bisa memverifikasi sumbernya keliru dan diganti dengan sitasi " + KEY + "; "
       "klaim subtractive clustering untuk makalah itu tidak terverifikasi (teks itu ada pada bab 2012 oleh penulis yang sama) dan tidak dipakai; entri BibTeX awal menukar judul buku dan seri dan sudah diperbaiki; nama HANFIS-DRS tetap |")
if ROW.count("|") != 5: sys.exit("ABORT: baris A-59 harus berisi tepat 5 pipa")
rows = list(re.finditer(r"^\| A-59 \|.*$", m, re.M))
if len(rows) != 1: sys.exit(f"ABORT, tidak ada yang ditulis: baris A-59 ditemukan {len(rows)}x (harus 1)")
new_m = m[:rows[0].start()] + ROW + m[rows[0].end():]
changed = []
for P, old, new, name in ((B, b, new_b, "bib"), (M, m, new_m, "memori")):
    if new != old: shutil.copy(P, str(P) + ".pre-soozfix.bak"); P.write_text(new, encoding="utf-8"); changed.append(name)
print("OK: " + ", ".join(changed) if changed else "Tidak ada perubahan (sudah sama).")

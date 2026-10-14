#!/usr/bin/env python3
r"""Dua perbaikan kecil pada entri yang baru ditambahkan lewat bib_from_doi.py (14 Okt):
  shapley1953value   : judul dari DOI berawalan nomor bab '17. A Value for n-Person Games' -> 'A Value for $n$-Person Games';
  efron1979bootstrap : metadata DOI tidak memuat halaman; ditambah pages = {1--26} (dari pengetahuan umum, BUKAN dari metadata DOI: periksa di halaman DOI sebelum dikomit).
Gagal-tertutup, tidak ada yang ditulis bila salah satu syarat gagal: tiap kunci tepat sekali; judul Shapley sama persis dengan yang diperiksa; entri Efron belum punya pages dan memuat 'number = {1},'.
Idempoten. Akhir baris dipertahankan. Cadangan .pre-fix2.bak.
   python scripts/apply_bib_fixes2.py [--bib manuscript/sn-bibliography.bib]"""
import argparse, re, shutil, sys
from pathlib import Path
ap = argparse.ArgumentParser(); ap.add_argument("--bib", default="manuscript/sn-bibliography.bib"); a = ap.parse_args()
p = Path(a.bib)
if not p.exists(): sys.exit(f"ABORT: {p} tidak ada")
text = open(p, encoding="utf-8", newline="").read(); eol = "\r\n" if "\r\n" in text else "\n"
def span(key):
    m = list(re.finditer(r"@\w+\s*\{\s*" + re.escape(key) + r"\s*,", text))
    if len(m) != 1: sys.exit(f"ABORT, tidak ada yang ditulis: {key} ditemukan {len(m)}x (harus 1)")
    depth, j = 0, m[0].start()
    while j < len(text):
        c = text[j]; j += 1
        if c == "{": depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0: return m[0].start(), j
    sys.exit(f"ABORT, tidak ada yang ditulis: kurung tidak seimbang di {key}")
s_sh, e_sh = span("shapley1953value"); s_ef, e_ef = span("efron1979bootstrap")
sh, ef = text[s_sh:e_sh], text[s_ef:e_ef]
old_t, new_t = "title = {17. A Value for n-Person Games},", "title = {A Value for $n$-Person Games},"
old_n = "number = {1}," + eol
if new_t in sh and "pages = {1--26}" in ef: print("Tidak ada perubahan (sudah diterapkan)."); sys.exit(0)
if sh.count(old_t) != 1: sys.exit("ABORT, tidak ada yang ditulis: judul Shapley bukan yang diperiksa")
if ef.count(old_n) != 1 or "pages" in ef: sys.exit("ABORT, tidak ada yang ditulis: entri Efron bukan yang diperiksa (tanpa pages dan dengan 'number = {1},')")
edits = sorted([(s_sh, e_sh, sh.replace(old_t, new_t)), (s_ef, e_ef, ef.replace(old_n, old_n + "  pages = {1--26}," + eol))], reverse=True)
new = text
for s, e, rep in edits: new = new[:s] + rep + new[e:]
shutil.copy(p, str(p) + ".pre-fix2.bak"); open(p, "w", encoding="utf-8", newline="").write(new)
print("OK: judul Shapley dan halaman Efron diperbarui")

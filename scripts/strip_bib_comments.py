#!/usr/bin/env python3
r"""Menghapus baris komentar (diawali %) di luar entri dari manuscript/sn-bibliography.bib: judul-judul contoh templat Springer dan catatan sisa 'confidence' yang kini usang.
BibTeX mengabaikan teks di luar entri, jadi isi bibliografi tidak berubah. Gagal-tertutup: daftar entri (tipe, kunci, semua kolom) sebelum dan sesudah harus identik, kalau tidak
tidak ada yang ditulis. Baris di dalam entri tidak disentuh. Akhir baris dipertahankan. Cadangan: .pre-strip.bak.
   python scripts/strip_bib_comments.py [--bib manuscript/sn-bibliography.bib] [--dry-run]"""
import argparse, importlib.util, shutil, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location("audit_bib_dois", Path(__file__).with_name("audit_bib_dois.py"))
A = importlib.util.module_from_spec(spec); spec.loader.exec_module(A)

def strip(text):
    out, depth, removed, prev_blank = [], 0, 0, True
    for line in text.splitlines(keepends=True):
        if depth == 0 and line.lstrip().startswith("%"):
            removed += 1; continue
        blank = line.strip() == ""
        if depth == 0 and blank:
            if prev_blank: continue
            prev_blank = True
        elif depth == 0: prev_blank = False
        out.append(line)
        i = 0
        while i < len(line):
            c = line[i]
            if c == "\\": i += 2; continue
            if depth > 0 or c == "@" or c == "{":
                if c == "{": depth += 1
                elif c == "}": depth = max(0, depth - 1)
            i += 1
    return "".join(out), removed

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bib", default="manuscript/sn-bibliography.bib"); ap.add_argument("--dry-run", action="store_true"); a = ap.parse_args(argv)
    bp = Path(a.bib)
    if not bp.exists(): sys.exit(f"ABORT: {bp} tidak ada")
    text = open(bp, encoding="utf-8", newline="").read()
    new, removed = strip(text)
    before, after = A.parse_bib(text), A.parse_bib(new)
    if before != after: sys.exit("ABORT, tidak ada yang ditulis: daftar entri berubah setelah penghapusan komentar")
    if not before: sys.exit("ABORT: tidak ada entri terbaca")
    print(f"{removed} baris komentar; {len(before)} entri tidak berubah; {len(text.splitlines())} -> {len(new.splitlines())} baris")
    if a.dry_run or new == text: print("(dry-run atau tidak ada perubahan; tidak ada yang ditulis)"); return 0
    shutil.copy(bp, str(bp) + ".pre-strip.bak"); open(bp, "w", encoding="utf-8", newline="").write(new); print("OK: komentar dihapus")
    return 0

if __name__ == "__main__":
    sys.exit(main())

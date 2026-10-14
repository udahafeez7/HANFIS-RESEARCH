#!/usr/bin/env python3
r"""Menyisipkan \cite{...} pada dua kemunculan yang anchor-nya terlihat penuh di keluaran grep 14 Okt:
  baris 367 : 'digest-pinned Trivy vulnerability scan'        -> ~\cite{aqua_trivy}
  baris 837 : 'exact interventional Shapley values'            -> ~\cite{shapley1953value}
Gagal-tertutup, tidak ada yang ditulis bila salah satu syarat gagal: baris itu harus memuat anchor tepat sekali; kunci harus ada di .bib; baris belum memuat kutipan yang sama
(idempoten: yang sudah ada dilewati). Hanya baris-baris itu yang berubah; akhir baris dipertahankan. Cadangan: .pre-cite1.bak.
   python scripts/apply_cites_1.py [--tex manuscript/sn-article.tex] [--bib manuscript/sn-bibliography.bib]"""
import argparse, re, shutil, sys
from pathlib import Path
EDITS = [
 (367, "digest-pinned Trivy vulnerability scan", "digest-pinned Trivy~\\cite{aqua_trivy} vulnerability scan", "aqua_trivy"),
 (837, "exact interventional Shapley values", "exact interventional Shapley values~\\cite{shapley1953value}", "shapley1953value"),
]
ap = argparse.ArgumentParser(); ap.add_argument("--tex", default="manuscript/sn-article.tex"); ap.add_argument("--bib", default="manuscript/sn-bibliography.bib"); a = ap.parse_args()
tp, bp = Path(a.tex), Path(a.bib)
for p in (tp, bp):
    if not p.exists(): sys.exit(f"ABORT: {p} tidak ada")
text = open(tp, encoding="utf-8", newline="").read(); lines = text.split("\n")
keys = set(re.findall(r"@\w+\s*\{\s*([^,\s]+)\s*,", open(bp, encoding="utf-8", newline="").read()))
problems, todo, done = [], [], []
for ln, anchor, repl, key in EDITS:
    if key not in keys: problems.append(f"baris {ln}: kunci {key} tidak ada di {bp.name}"); continue
    if ln > len(lines): problems.append(f"baris {ln}: berkas hanya {len(lines)} baris"); continue
    cur = lines[ln - 1]
    if "\\cite{" + key + "}" in cur: done.append(ln); continue
    if cur.count(anchor) != 1: problems.append(f"baris {ln}: anchor '{anchor}' ditemukan {cur.count(anchor)}x (harus 1); nomor baris bergeser?"); continue
    todo.append((ln, cur.replace(anchor, repl, 1)))
if problems: sys.exit("ABORT, tidak ada yang ditulis:\n  " + "\n  ".join(problems))
if not todo: print("Tidak ada perubahan (sudah diterapkan: baris " + ", ".join(map(str, done)) + ")."); sys.exit(0)
for ln, new in todo: lines[ln - 1] = new
out = "\n".join(lines)
if out.count("\n") != text.count("\n"): sys.exit("ABORT, tidak ada yang ditulis: jumlah baris berubah")
shutil.copy(tp, str(tp) + ".pre-cite1.bak"); open(tp, "w", encoding="utf-8", newline="").write(out)
print("OK: kutipan disisipkan pada baris " + ", ".join(str(l) for l, _ in todo) + (f"; sudah ada: {', '.join(map(str, done))}" if done else ""))

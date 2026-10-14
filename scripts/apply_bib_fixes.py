#!/usr/bin/env python3
r"""Memperbaiki tiga entri BibTeX berdasarkan keluaran audit kelengkapan 14 Okt (metadata resmi doi.org yang ditampilkan di terminal):
  first_epss          : urutan penulis 4 dan 5 tertukar (resmi: Adjerid lalu Roytman);
  ojha2019heuristic   : 'and others' diganti tiga penulis lengkap; tambah volume 85 dan halaman 845--864;
  lee2003hierarchical : nama depan Chung dan Yu dilengkapi; tambah volume 138, nomor 2, halaman 343--361.
Gagal-tertutup, tidak ada yang ditulis bila salah satu syarat gagal: setiap kunci tepat sekali; DOI entri sama dengan yang diharapkan; kolom author saat ini sama persis dengan yang
diperiksa (bukan hasil suntingan lain); kolom baru belum ada. Sesudah penulisan, entri lain harus identik dan jumlah entri tetap. Idempoten. Akhir baris dipertahankan. Cadangan .pre-fix.bak.
Nama non-ASCII memakai aksen LaTeX agar aman bagi BibTeX.
   python scripts/apply_bib_fixes.py [--bib manuscript/sn-bibliography.bib]"""
import argparse, importlib.util, re, shutil, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location("audit_bib_dois", Path(__file__).with_name("audit_bib_dois.py"))
A = importlib.util.module_from_spec(spec); spec.loader.exec_module(A)

FIXES = {
 "first_epss": {"doi": "10.1145/3436242",
   "old_author": "Jacobs, Jay and Romanosky, Sasha and Edwards, Benjamin and Roytman, Michael and Adjerid, Idris",
   "author": "Jacobs, Jay and Romanosky, Sasha and Edwards, Benjamin and Adjerid, Idris and Roytman, Michael", "add": {}},
 "ojha2019heuristic": {"doi": "10.1016/j.engappai.2019.08.010", "old_author": "Ojha, Varun and others",
   "author": "Ojha, Varun and Abraham, Ajith and Sn{\\'a}{\\v{s}}el, V{\\'a}clav", "add": {"volume": "85", "pages": "845--864"}},
 "lee2003hierarchical": {"doi": "10.1016/S0165-0114(02)00517-1", "old_author": "Lee, Ming-Ling and Chung and Yu",
   "author": "Lee, Ming-Ling and Chung, Hung-Yuan and Yu, Fang-Ming", "add": {"volume": "138", "number": "2", "pages": "343--361"}},
}
ORDER_AFTER = ("journal", "title")

def entry_span(text, key):
    ms = list(re.finditer(r"@\w+\s*\{\s*" + re.escape(key) + r"\s*,", text))
    if len(ms) != 1: return None
    depth, j = 0, ms[0].start()
    while j < len(text):
        c = text[j]
        if c == "{": depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0: return ms[0].start(), j + 1
        j += 1
    return None

def render(e, new_author, add, eol):
    f = dict(e["f"]); out = {}
    for k, v in f.items():
        out[k] = new_author if k == "author" else v
        if k in ORDER_AFTER and k == next((x for x in ORDER_AFTER if x in f), None):
            for nk, nv in add.items(): out[nk] = nv
    for nk, nv in add.items(): out.setdefault(nk, nv)
    lines = [f"@{e['type']}{{{e['key']},"] + [f"  {k} = {{{v}}}," for k, v in out.items()]
    lines[-1] = lines[-1].rstrip(",") ; lines.append("}")
    return eol.join(lines)

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bib", default="manuscript/sn-bibliography.bib"); a = ap.parse_args(argv)
    bp = Path(a.bib)
    if not bp.exists(): sys.exit(f"ABORT: {bp} tidak ada")
    text = open(bp, encoding="utf-8", newline="").read(); eol = "\r\n" if "\r\n" in text else "\n"
    ents = {e["key"]: e for e in A.parse_bib(text)}; problems, plan = [], []
    for key, fx in FIXES.items():
        e = ents.get(key); sp = entry_span(text, key)
        if e is None or sp is None: problems.append(f"{key}: tidak ditemukan tepat sekali"); continue
        if A.clean_doi(e["f"].get("doi", "")).lower() != fx["doi"].lower(): problems.append(f"{key}: DOI berbeda dari yang diperiksa"); continue
        cur = re.sub(r"\s+", " ", e["f"].get("author", "")).strip()
        if cur == fx["author"]:
            if all(e["f"].get(k) == v for k, v in fx["add"].items()): continue
            problems.append(f"{key}: author sudah baru tetapi kolom lain belum lengkap"); continue
        if cur != fx["old_author"]: problems.append(f"{key}: author saat ini '{cur[:60]}' bukan yang diperiksa (disunting lain?)"); continue
        clash = [k for k in fx["add"] if k in e["f"]]
        if clash: problems.append(f"{key}: kolom sudah ada: {', '.join(clash)}"); continue
        plan.append((sp, key, render(e, fx["author"], fx["add"], eol)))
    if problems: sys.exit("ABORT, tidak ada yang ditulis:\n  " + "\n  ".join(problems))
    if not plan: print("Tidak ada perubahan (sudah diterapkan)."); return 0
    new = text
    for (s, e_), key, ent in sorted(plan, reverse=True): new = new[:s] + ent + new[e_:]
    before, after = {e["key"]: e for e in A.parse_bib(text)}, {e["key"]: e for e in A.parse_bib(new)}
    changed = {k for k in before if before[k] != after.get(k)}
    if set(before) != set(after) or changed != {k for _, k, _ in plan}: sys.exit("ABORT, tidak ada yang ditulis: pemeriksaan sesudah penulisan gagal (entri lain berubah atau jumlah berbeda)")
    for k in changed:
        for fk, fv in FIXES[k]["add"].items():
            if after[k]["f"].get(fk) != fv: sys.exit(f"ABORT, tidak ada yang ditulis: {k}.{fk} tidak sesuai setelah penulisan")
        if after[k]["f"].get("author") != FIXES[k]["author"]: sys.exit(f"ABORT, tidak ada yang ditulis: {k}.author tidak sesuai setelah penulisan")
    shutil.copy(bp, str(bp) + ".pre-fix.bak"); open(bp, "w", encoding="utf-8", newline="").write(new)
    print(f"OK: {len(plan)} entri diperbaiki ({', '.join(k for _, k, _ in sorted(plan))}); {len(after)} entri total")
    return 0

if __name__ == "__main__":
    sys.exit(main())

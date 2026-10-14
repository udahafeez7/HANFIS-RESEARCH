#!/usr/bin/env python3
r"""Menghapus entri BibTeX yang tidak dikutip (mis. sisa contoh templat Springer) dari manuscript/sn-bibliography.bib.
Gagal-tertutup, tidak ada yang ditulis bila salah satu syarat gagal: setiap kunci harus ada tepat sekali di .bib, tidak ada di .bbl, tidak dikutip di berkas .tex mana pun
(\cite, \citep, \citet, dan varian), dan naskah tidak boleh memakai \nocite{*}. Sisa berkas dipertahankan byte demi byte (akhir baris tetap). Cadangan: .pre-prune.bak.
   python scripts/remove_bib_entries.py --keys bib3 bib4 ... [--bib manuscript/sn-bibliography.bib] [--tex-glob 'manuscript/*.tex'] [--bbl manuscript/sn-article.bbl]"""
import argparse, glob, re, shutil, sys
from pathlib import Path

def span(text, key):
    ms = list(re.finditer(r"@\w+\s*\{\s*" + re.escape(key) + r"\s*,", text))
    if len(ms) != 1: return None, len(ms)
    start, depth, j = ms[0].start(), 0, ms[0].start()
    while j < len(text):
        c = text[j]
        if c == "{": depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0: j += 1; break
        j += 1
    while j < len(text) and text[j] in "\r\n" and text[start:j].count("\n") >= 0:
        j += 1
        if text[j - 1] == "\n" and j < len(text) and text[j] not in "\r\n": break
    return (start, j), 1

def cited_keys(tex):
    keys = set()
    for m in re.finditer(r"\\[A-Za-z]*cite[A-Za-z]*\*?\s*(?:\[[^\]]*\]\s*)*\{([^}]*)\}", tex):
        keys.update(k.strip() for k in m.group(1).split(","))
    return keys

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--keys", nargs="+", required=True); ap.add_argument("--bib", default="manuscript/sn-bibliography.bib")
    ap.add_argument("--tex-glob", default="manuscript/*.tex"); ap.add_argument("--bbl", default="manuscript/sn-article.bbl"); a = ap.parse_args(argv)
    bp = Path(a.bib)
    if not bp.exists(): sys.exit(f"ABORT: {bp} tidak ada")
    text = open(bp, encoding="utf-8", newline="").read()
    tex = "".join(open(p, encoding="utf-8", errors="replace").read() for p in sorted(glob.glob(a.tex_glob)))
    if not tex: sys.exit(f"ABORT: tidak ada berkas .tex untuk pola {a.tex_glob}")
    if re.search(r"\\nocite\s*\{\s*\*\s*\}", tex): sys.exit("ABORT: naskah memakai \\nocite{*}; semua entri dianggap dikutip")
    bbl = open(a.bbl, encoding="utf-8", errors="replace").read() if Path(a.bbl).exists() else None
    if bbl is None: sys.exit(f"ABORT: {a.bbl} tidak ada; kompilasi naskah dahulu agar daftar kutipan diketahui")
    cited, problems, spans = cited_keys(tex), [], []
    for k in a.keys:
        sp, n = span(text, k)
        if n != 1: problems.append(f"{k}: ada {n}x di .bib (harus 1)"); continue
        if "{" + k + "}" in bbl: problems.append(f"{k}: muncul di .bbl (dikutip)")
        if k in cited: problems.append(f"{k}: dikutip di berkas .tex")
        spans.append((sp, k))
    if problems: sys.exit("ABORT, tidak ada yang ditulis:\n  " + "\n  ".join(problems))
    new = text
    for (s, e), k in sorted(spans, reverse=True): new = new[:s] + new[e:]
    shutil.copy(bp, str(bp) + ".pre-prune.bak"); open(bp, "w", encoding="utf-8", newline="").write(new)
    left = len(re.findall(r"^@\w+\s*\{", new, re.M))
    print(f"OK: {len(spans)} entri dihapus ({', '.join(k for _, k in sorted(spans, key=lambda x: x[0]))}); sisa {left} entri")
    return 0

if __name__ == "__main__":
    sys.exit(main())

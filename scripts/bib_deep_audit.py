#!/usr/bin/env python3
r"""Audit bibliografi tahap dua: untuk setiap entri ber-DOI, bandingkan KELENGKAPAN kolom dengan metadata resmi doi.org (Crossref atau DataCite): daftar penulis lengkap
(jumlah, nama keluarga, nama depan yang hilang), jurnal atau buku, volume, nomor, halaman. Hanya membaca; mencetak usulan nilai dari sumber resmi untuk disalin sendiri.
   python scripts/bib_deep_audit.py [--bib manuscript/sn-bibliography.bib] [--mailto surel] [--pause 0.3]"""
import argparse, difflib, importlib.util, re, sys, time
from pathlib import Path
spec = importlib.util.spec_from_file_location("audit_bib_dois", Path(__file__).with_name("audit_bib_dois.py"))
A = importlib.util.module_from_spec(spec); spec.loader.exec_module(A)

def split_authors(s):
    parts, depth, cur, i = [], 0, "", 0
    while i < len(s):
        c = s[i]
        depth += (c == "{") - (c == "}")
        if depth == 0 and s[i:i + 5].lower() == " and ": parts.append(cur.strip()); cur = ""; i += 5; continue
        cur += c; i += 1
    if cur.strip(): parts.append(cur.strip())
    return parts

def parse_author(a):
    a = a.strip()
    if a.startswith("{") and a.endswith("}"): return {"family": a.strip("{}").strip(), "given": None, "corp": True}
    if "," in a: fam, giv = a.split(",", 1); return {"family": fam.strip(), "given": giv.strip(), "corp": False}
    t = a.split()
    return {"family": t[-1] if t else "", "given": " ".join(t[:-1]) if len(t) > 1 else "", "corp": False}

def canon(csl_authors):
    out = []
    for x in csl_authors or []:
        if x.get("family"): out.append(x["family"] + (", " + x["given"] if x.get("given") else ""))
        elif x.get("literal"): out.append("{" + x["literal"] + "}")
    return " and ".join(out)

def digits(s): return re.findall(r"\d+", s or "")

def deep(entry, csl):
    f, notes = entry["f"], []
    bib_au = [parse_author(x) for x in split_authors(f.get("author", ""))]
    ref_au = csl.get("author") or []
    if ref_au and len(bib_au) != len(ref_au): notes.append(f"jumlah penulis: bib {len(bib_au)}, resmi {len(ref_au)}")
    for i, b in enumerate(bib_au):
        if not b["corp"] and (b["given"] is None or b["given"] == "") and b["family"]: notes.append(f"penulis {i + 1} ({b['family']}) tanpa nama depan")
    if ref_au and len(bib_au) == len(ref_au):
        for i, (b, r) in enumerate(zip(bib_au, ref_au)):
            nb, nr = A.norm(b["family"]), A.norm(r.get("family") or r.get("literal") or "")
            if nb and nr and nb != nr and nb not in nr and nr not in nb: notes.append(f"penulis {i + 1}: bib '{b['family']}', resmi '{r.get('family') or r.get('literal')}'")
    if any("penulis" in n for n in notes) and ref_au: notes.append("usulan: author = {" + canon(ref_au) + "}")
    cont = csl.get("container-title") or ""; cont = cont[0] if isinstance(cont, list) else cont
    jb = f.get("journal") or f.get("booktitle") or ""
    if cont and jb and difflib.SequenceMatcher(None, A.norm(jb), A.norm(cont)).ratio() < 0.6: notes.append(f"jurnal/buku: bib '{jb[:40]}', resmi '{cont[:50]}'")
    if cont and not jb and entry["type"] in ("article", "inproceedings", "incollection"): notes.append(f"jurnal/buku hilang; resmi '{cont[:60]}'")
    for fld, key in (("volume", "volume"), ("number", "issue")):
        rv, bv = str(csl.get(key) or "").strip(), (f.get(fld) or "").strip()
        if rv and not bv and entry["type"] == "article": notes.append(f"{fld} hilang; usulan {fld} = {{{rv}}}")
        elif rv and bv and digits(rv) != digits(bv): notes.append(f"{fld}: bib {bv}, resmi {rv}")
    rp, bp = str(csl.get("page") or "").strip(), (f.get("pages") or "").strip()
    if rp and not bp and entry["type"] in ("article", "incollection", "inproceedings"): notes.append("halaman hilang; usulan pages = {" + re.sub(r"[-\u2013\u2014]+", "--", rp) + "}")
    elif rp and bp and digits(rp) != digits(bp): notes.append(f"halaman: bib {bp}, resmi {rp}")
    return notes

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bib", default="manuscript/sn-bibliography.bib"); ap.add_argument("--mailto"); ap.add_argument("--pause", type=float, default=0.3); a = ap.parse_args(argv)
    bp = Path(a.bib)
    if not bp.exists(): sys.exit(f"ABORT: {bp} tidak ada")
    ents = A.parse_bib(bp.read_text(encoding="utf-8")); n_bad = n_checked = 0
    for e in ents:
        doi = A.clean_doi(e["f"].get("doi", ""))
        if not doi: print(f"{e['key']}: tanpa DOI (dilewati)"); continue
        csl, err = A.fetch_csl(doi, a.mailto); n_checked += 1
        if err: print(f"{e['key']}: {err}"); n_bad += 1; continue
        notes = deep(e, csl)
        if notes: n_bad += 1; print(f"{e['key']}  ({doi})"); [print("   -", x) for x in notes]
        else: print(f"{e['key']}: lengkap")
        time.sleep(a.pause)
    print(f"\n{n_checked} entri ber-DOI diperiksa; {n_bad} perlu perhatian")
    return 0 if n_bad == 0 else 1

if __name__ == "__main__":
    sys.exit(main())

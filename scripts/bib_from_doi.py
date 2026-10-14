#!/usr/bin/env python3
r"""Membuat entri BibTeX dari DOI memakai metadata resmi doi.org (Crossref atau DataCite). Tidak menebak apa pun: semua kolom berasal dari sumber resmi.
Secara bawaan hanya mencetak entri. Dengan --append, entri ditambahkan ke .bib setelah pemeriksaan: DOI atau kunci yang sudah ada dilewati (tidak ditimpa); berkas lain tidak berubah.
Nama non-ASCII diberi aksen LaTeX; kata berhuruf kapital ganda dalam judul (EPSS, KEV) diberi kurung {..} agar kapitalnya terjaga.
   python scripts/bib_from_doi.py DOI [DOI ...] [--append manuscript/sn-bibliography.bib] [--mailto surel]"""
import argparse, importlib.util, re, sys, time, unicodedata
from pathlib import Path
spec = importlib.util.spec_from_file_location("audit_bib_dois", Path(__file__).with_name("audit_bib_dois.py"))
A = importlib.util.module_from_spec(spec); spec.loader.exec_module(A)
ACC = {"\u0301": "'", "\u0300": "`", "\u0302": "^", "\u0308": '"', "\u0303": "~", "\u030c": "v", "\u0327": "c", "\u030a": "r", "\u0304": "=", "\u0307": ".", "\u0306": "u", "\u030b": "H", "\u0328": "k"}
SPECIAL = {"\u00f8": "{\\o}", "\u00d8": "{\\O}", "\u0142": "{\\l}", "\u0141": "{\\L}", "\u00df": "{\\ss}", "\u00e6": "{\\ae}", "\u00c6": "{\\AE}", "\u0131": "{\\i}"}
STOP = {"a", "an", "the", "of", "on", "for", "and", "in", "to", "with", "by", "from", "at"}
TYPES = {"journal-article": "article", "book": "book", "book-chapter": "incollection", "proceedings-article": "inproceedings", "report": "techreport", "monograph": "book", "posted-content": "misc"}

def tex(s):
    out = []
    for ch in unicodedata.normalize("NFD", s or ""):
        if ch in ACC and out:
            base = out.pop(); cmd = ACC[ch]
            out.append("{\\" + cmd + ("{" + base + "}" if cmd.isalpha() else base) + "}")
        elif ord(ch) < 128 or ch in SPECIAL: out.append(SPECIAL.get(ch, ch))
        else: out.append(ch)
    return "".join(out)

def protect(title):
    return re.sub(r"\b([A-Z][A-Za-z0-9]*[A-Z][A-Za-z0-9]*)\b", r"{\1}", title)

def ascii_word(s): return re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFKD", s.lower()).encode("ascii", "ignore").decode())

def make_key(csl, year):
    au = (csl.get("author") or [{}])[0]; fam = ascii_word(au.get("family") or au.get("literal") or "anon")
    words = [w for w in re.findall(r"[A-Za-z]+", csl.get("title") or "") if w.lower() not in STOP]
    return f"{fam}{year}{ascii_word(words[0]) if words else ''}"

def to_bib(doi, csl):
    typ = TYPES.get(csl.get("type"), "misc"); year = A.csl_year(csl); f = {}
    au = []
    for x in csl.get("author") or []:
        if x.get("family"): au.append(tex(x["family"]) + (", " + tex(x["given"]) if x.get("given") else ""))
        elif x.get("literal"): au.append("{" + tex(x["literal"]) + "}")
    if au: f["author"] = " and ".join(au)
    f["title"] = protect(tex(csl.get("title") or ""))
    cont = csl.get("container-title"); cont = cont[0] if isinstance(cont, list) and cont else cont
    if cont: f["journal" if typ == "article" else "booktitle"] = tex(cont)
    for k, ck in (("volume", "volume"), ("number", "issue")):
        if csl.get(ck): f[k] = str(csl[ck])
    if csl.get("page"): f["pages"] = re.sub(r"[-\u2013\u2014]+", "--", str(csl["page"]))
    if csl.get("publisher") and typ in ("book", "incollection", "techreport", "misc", "inproceedings"): f["publisher"] = tex(csl["publisher"])
    f["year"] = year; f["doi"] = doi
    return typ, make_key(csl, year), f

def render(typ, key, f, eol="\n"):
    lines = [f"@{typ}{{{key},"] + [f"  {k} = {{{v}}}," for k, v in f.items()]
    lines[-1] = lines[-1].rstrip(","); lines.append("}")
    return eol.join(lines)

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dois", nargs="+"); ap.add_argument("--append"); ap.add_argument("--mailto"); a = ap.parse_args(argv)
    bp = Path(a.append) if a.append else None; text = open(bp, encoding="utf-8", newline="").read() if bp and bp.exists() else ""
    eol = "\r\n" if "\r\n" in text else "\n"; have = A.parse_bib(text) if text else []
    dois_have = {A.clean_doi(e["f"].get("doi", "")).lower() for e in have}; keys_have = {e["key"] for e in have}; new, rc = [], 0
    for d in a.dois:
        doi = A.clean_doi(d); csl, err = A.fetch_csl(doi, a.mailto)
        if err: print(f"GAGAL {doi}: {err}"); rc = 1; continue
        typ, key, f = to_bib(doi, csl); print(render(typ, key, f) + "\n")
        if bp:
            if doi.lower() in dois_have: print(f"  -> dilewati: DOI sudah ada di {bp}"); continue
            if key in keys_have: print(f"  -> dilewati: kunci {key} sudah ada; ganti kunci secara manual"); rc = 1; continue
            new.append(render(typ, key, f, eol)); keys_have.add(key); dois_have.add(doi.lower())
        time.sleep(0.3)
    if bp and new:
        body = text.rstrip("\r\n") + eol + eol + (eol + eol).join(new) + eol if text else (eol + eol).join(new) + eol
        before = A.parse_bib(text)
        if A.parse_bib(body)[:len(before)] != before: sys.exit("ABORT, tidak ada yang ditulis: entri lama berubah setelah penambahan")
        import shutil
        if bp.exists(): shutil.copy(bp, str(bp) + ".pre-add.bak")
        open(bp, "w", encoding="utf-8", newline="").write(body); print(f"OK: {len(new)} entri ditambahkan ke {bp}")
    return rc

if __name__ == "__main__":
    sys.exit(main())

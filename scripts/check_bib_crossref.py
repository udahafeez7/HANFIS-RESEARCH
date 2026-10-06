#!/usr/bin/env python3
"""Periksa entri .bib terhadap Crossref (metadata DOI terbuka). Hanya MEMBACA; tidak mengubah .bib.
Entri ber-DOI: bandingkan judul, tahun, volume, halaman awal, nama belakang penulis pertama.
Entri tanpa DOI: cari lewat judul+penulis dan tampilkan kandidat terbaik (HARUS dikonfirmasi manual).
Keluaran: ringkasan di layar + CSV. Jalankan dari akar repo:  python scripts/check_bib_crossref.py [--mailto alamat@contoh]"""
import argparse, csv, difflib, json, re, sys, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path

def parse_bib(text):
    out, i = [], 0
    while True:
        m = re.search(r"^@(\w+)\s*\{\s*([^,\s]+)\s*,", text[i:], re.M)
        if not m: break
        typ, key = m.group(1).lower(), m.group(2)
        start = i + m.end(); depth, j = 1, start
        while j < len(text) and depth:
            depth += {"{": 1, "}": -1}.get(text[j], 0); j += 1
        body = text[start:j - 1]; i = j
        if typ in ("comment", "string", "preamble"): continue
        fields = {}
        for fm in re.finditer(r"(\w+)\s*=\s*", body):
            k = fm.group(1).lower(); p = fm.end()
            if p >= len(body): continue
            if body[p] == "{":
                d, q = 1, p + 1
                while q < len(body) and d: d += {"{": 1, "}": -1}.get(body[q], 0); q += 1
                v = body[p + 1:q - 1]
            elif body[p] == '"':
                q = body.index('"', p + 1); v = body[p + 1:q]
            else:
                q = re.search(r"[,\n}]", body[p:]); v = body[p:p + (q.start() if q else len(body))]
            fields.setdefault(k, re.sub(r"\s+", " ", v.replace("{", "").replace("}", "")).strip())
        out.append((typ, key, fields))
    return out

norm = lambda s: re.sub(r"[^a-z0-9]", "", (s or "").lower())
def first_surname(auth):
    a = (auth or "").split(" and ")[0]
    return norm(a.split(",")[0] if "," in a else a.split()[-1] if a.split() else "")

def fetch(url, mailto):
    ua = "bib-check/1.0" + (f" (mailto:{mailto})" if mailto else "")
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": ua}), timeout=30) as r:
        return json.load(r)["message"]

def cr_fields(msg):
    t = (msg.get("title") or [""])[0]
    yr = ((msg.get("issued") or {}).get("date-parts") or [[None]])[0][0]
    au = ", ".join(a.get("family", "") for a in msg.get("author", [])[:3])
    return dict(title=t, year=str(yr or ""), volume=str(msg.get("volume") or ""),
                page=str(msg.get("page") or ""), authors=au, doi=msg.get("DOI", ""),
                container=(msg.get("container-title") or [""])[0])

def compare(f, c):
    issues = []
    if f.get("title") and difflib.SequenceMatcher(None, norm(f["title"]), norm(c["title"])).ratio() < 0.9: issues.append("judul")
    if f.get("year") and c["year"] and f["year"].strip() != c["year"]: issues.append(f"tahun({f['year']}!={c['year']})")
    if f.get("volume") and c["volume"] and norm(f["volume"]) != norm(c["volume"]): issues.append(f"volume({f['volume']}!={c['volume']})")
    fp = re.split(r"[-–—]", f.get("pages", ""))[0].strip(); cp = re.split(r"[-–—]", c["page"])[0].strip()
    if fp and cp and norm(fp) != norm(cp): issues.append(f"halaman({fp}!={cp})")
    if f.get("author") and c["authors"] and first_surname(f["author"]) not in norm(c["authors"]): issues.append("penulis")
    return issues

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--bib", default="manuscript/sn-bibliography.bib")
    ap.add_argument("--tex", default="manuscript/sn-article.tex")
    ap.add_argument("--out", default="results_python/bib_check/bib_crossref_check.csv")
    ap.add_argument("--mailto", default="")
    ap.add_argument("--sleep", type=float, default=0.5)
    a = ap.parse_args(argv)
    entries = parse_bib(Path(a.bib).read_text(encoding="utf-8"))
    cited = set()
    if Path(a.tex).exists():
        for m in re.finditer(r"\\cite\w*\{([^}]*)\}", Path(a.tex).read_text(encoding="utf-8")):
            cited.update(k.strip() for k in m.group(1).split(","))
    rows = []
    for typ, key, f in entries:
        if cited and key not in cited: continue
        doi = f.get("doi", "").strip(); status, detail = "", ""
        try:
            if doi:
                c = cr_fields(fetch("https://api.crossref.org/works/" + urllib.parse.quote(doi), a.mailto))
                iss = compare(f, c); status = "OK" if not iss else "BEDA"; detail = ",".join(iss)
            else:
                q = urllib.parse.urlencode({"query.bibliographic": f"{f.get('title','')} {f.get('author','')}", "rows": 1})
                items = fetch("https://api.crossref.org/works?" + q, a.mailto).get("items", [])
                if items:
                    c = cr_fields(items[0]); iss = compare(f, c); status = "KANDIDAT-OK" if not iss else "KANDIDAT-BEDA"
                    detail = f"doi={c['doi']}; " + ",".join(iss)
                else: status, detail = "TAK-DITEMUKAN", ""
        except urllib.error.HTTPError as e:
            status, detail = ("DOI-404", "DOI tidak ada di Crossref (salah ketik atau bukan DOI Crossref)") if (e.code == 404 and doi) else ("GALAT-HTTP", f"HTTP {e.code}")
        except Exception as e:
            status, detail = "GALAT-JARINGAN", str(e)[:80]
        rows.append(dict(key=key, type=typ, has_doi=bool(doi), status=status, detail=detail, title=f.get("title", "")[:70]))
        print(f"{status:14} {key:36} {detail[:70]}"); time.sleep(a.sleep)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with open(a.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["key", "type", "has_doi", "status", "detail", "title"]); w.writeheader(); w.writerows(rows)
    from collections import Counter
    print("\nRingkasan:", dict(Counter(r["status"] for r in rows)), "->", a.out)
    return 0
if __name__ == "__main__": sys.exit(main())

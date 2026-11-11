#!/usr/bin/env python3
r"""Audit bibliografi: untuk setiap entri BibTeX yang punya DOI, ambil metadata resmi lewat negosiasi konten doi.org (berlaku untuk Crossref dan DataCite,
termasuk Zenodo dan OSF) lalu bandingkan judul, tahun, dan nama keluarga penulis pertama. Hanya membaca; tidak mengubah berkas .bib.
Entri tanpa DOI dicatat terpisah untuk diperiksa manual. Hasil: tabel di layar dan CSV di results_python/bib_audit/.
Status: OK, PERIKSA (ada selisih), TIDAK_DITEMUKAN (DOI tidak terselesaikan), GALAT_JARINGAN, TANPA_DOI, DOI_GANDA.
   python scripts/audit_bib_dois.py [--bib manuscript/sn-bibliography.bib] [--mailto surel@contoh.id] [--out results_python/bib_audit]
Hanya pustaka standar Python. Keputusan akhir tetap di tangan manusia: selisih bisa berasal dari BibTeX atau dari metadata."""
import argparse, csv, datetime as dt, difflib, json, re, sys, time, unicodedata, urllib.error, urllib.request
from pathlib import Path

def parse_bib(text):
    out = []
    for m in re.finditer(r"@(\w+)\s*\{\s*([^,\s]+)\s*,", text):
        typ, key = m.group(1).lower(), m.group(2)
        if typ in ("comment", "string", "preamble"): continue
        i, depth, j = m.end(), 1, m.end()
        while j < len(text) and depth:
            c = text[j]
            depth += (c == "{") - (c == "}")
            j += 1
        body, fields, p = text[i:j - 1], {}, 0
        while True:
            fm = re.compile(r"\s*,?\s*([A-Za-z][\w-]*)\s*=\s*").match(body, p)
            if not fm: break
            p = fm.end()
            if p >= len(body): break
            if body[p] == "{":
                d, q = 0, p
                while q < len(body):
                    d += (body[q] == "{") - (body[q] == "}")
                    q += 1
                    if d == 0: break
                val = body[p + 1:q - 1]; p = q
            elif body[p] == '"':
                q = p + 1
                while q < len(body) and not (body[q] == '"' and body[q - 1] != "\\"): q += 1
                val = body[p + 1:q]; p = q + 1
            else:
                q = p
                while q < len(body) and body[q] not in ",\n": q += 1
                val = body[p:q].strip(); p = q
            fields[fm.group(1).lower()] = val.strip()
        out.append({"type": typ, "key": key, "f": fields})
    return out

def norm(s):
    s = re.sub(r"\\[`'^\"~=.uvHcdbk]\s*\{?(\w)\}?", r"\1", s or "")
    s = re.sub(r"\\[A-Za-z]+\s*", " ", s).replace("{", "").replace("}", "")
    s = unicodedata.normalize("NFKD", s); s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()

def first_family(authors):
    if not authors: return ""
    a = re.split(r"\s+and\s+", authors.strip())[0].strip()
    fam = a.split(",")[0] if "," in a else (a.split()[-1] if a.split() else "")
    return norm(fam)

def clean_doi(d):
    d = (d or "").strip()
    d = re.sub(r"^(https?://(dx\.)?doi\.org/)", "", d, flags=re.I)
    return d.strip().rstrip(".,;")

def fetch_csl(doi, mailto=None, tries=3):
    h = {"Accept": "application/vnd.citationstyles.csl+json", "User-Agent": "hanfis-bib-audit/1.0" + (f" (mailto:{mailto})" if mailto else "")}
    last = None
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request("https://doi.org/" + urllib.request.quote(doi, safe="/()-._;:<>"), headers=h), timeout=30) as r:
                return json.loads(r.read().decode("utf-8")), None
        except urllib.error.HTTPError as e:
            if e.code in (404, 400, 410): return None, "TIDAK_DITEMUKAN"
            last = f"HTTP {e.code}"
        except Exception as e:
            last = type(e).__name__
        time.sleep(1.5 * (k + 1))
    return None, "GALAT_JARINGAN:" + str(last)

def csl_year(c):
    for k in ("issued", "published-print", "published-online", "created"):
        try:
            y = c[k]["date-parts"][0][0]
            if y is not None: return str(y)
        except Exception: pass
    return ""

def compare(entry, csl):
    f, notes, status = entry["f"], [], "OK"
    tb, tr = norm(f.get("title", "")), norm(csl.get("title", ""))
    ratio = difflib.SequenceMatcher(None, tb, tr).ratio() if tb and tr else 0.0
    if ratio < 0.85: status = "PERIKSA"; notes.append(f"judul mirip {ratio:.2f}")
    yb, yr = (f.get("year") or "").strip(), csl_year(csl)
    if yb and yr and abs(int(re.sub(r"\D", "", yb) or 0) - int(yr)) > 1: status = "PERIKSA"; notes.append(f"tahun {yb} lawan {yr}")
    ab = first_family(f.get("author", ""))
    ar = norm((csl.get("author") or [{}])[0].get("family", "") or (csl.get("author") or [{}])[0].get("literal", ""))
    if ab and ar and ab != ar and ab not in ar and ar not in ab: status = "PERIKSA"; notes.append(f"penulis pertama {ab} lawan {ar}")
    cont = csl.get("container-title") or ""
    cont = cont[0] if isinstance(cont, list) else cont
    return status, ratio, yr, ar, cont, "; ".join(notes)

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bib", default="manuscript/sn-bibliography.bib"); ap.add_argument("--mailto"); ap.add_argument("--out", default="results_python/bib_audit")
    ap.add_argument("--pause", type=float, default=0.3); a = ap.parse_args(argv)
    bp = Path(a.bib)
    if not bp.exists(): sys.exit(f"ABORT: {bp} tidak ada")
    entries = parse_bib(bp.read_text(encoding="utf-8")); rows, seen = [], {}
    print(f"{len(entries)} entri di {bp}")
    for e in entries:
        f = e["f"]; doi = clean_doi(f.get("doi", ""))
        base = {"key": e["key"], "type": e["type"], "doi": doi, "title_bib": norm(f.get("title", ""))[:60], "year_bib": f.get("year", ""), "author_bib": first_family(f.get("author", ""))}
        if not doi:
            rows.append({**base, "status": "TANPA_DOI", "note": "periksa manual (buku, standar, situs, atau DOI belum ditulis)"}); continue
        if doi.lower() in seen:
            rows.append({**base, "status": "DOI_GANDA", "note": f"sama dengan {seen[doi.lower()]}"}); continue
        seen[doi.lower()] = e["key"]
        csl, err = fetch_csl(doi, a.mailto)
        if err: rows.append({**base, "status": err.split(":")[0], "note": err}); time.sleep(a.pause); continue
        st, ratio, yr, ar, cont, note = compare(e, csl)
        rows.append({**base, "status": st, "title_ratio": f"{ratio:.2f}", "year_ref": yr, "author_ref": ar, "container_ref": cont[:60], "note": note}); time.sleep(a.pause)
    outd = Path(a.out); outd.mkdir(parents=True, exist_ok=True)
    cp = outd / f"bib_audit_{dt.datetime.now().strftime('%Y%m%dT%H%M%S')}.csv"
    cols = ["key", "type", "doi", "status", "title_ratio", "year_bib", "year_ref", "author_bib", "author_ref", "container_ref", "title_bib", "note"]
    with open(cp, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols); w.writeheader(); [w.writerow(r) for r in rows]
    cnt = {}
    for r in rows: cnt[r["status"]] = cnt.get(r["status"], 0) + 1
    print("Ringkasan:", ", ".join(f"{k}={v}" for k, v in sorted(cnt.items())))
    for r in rows:
        if r["status"] != "OK": print(f"  {r['status']:<16} {r['key']:<28} {r['doi'][:34]:<34} {r.get('note','')}")
    print(f"CSV: {cp}")
    return 0 if not any(r["status"] in ("PERIKSA", "TIDAK_DITEMUKAN", "GALAT_JARINGAN") for r in rows) else 1

if __name__ == "__main__":
    sys.exit(main())

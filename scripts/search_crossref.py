#!/usr/bin/env python3
"""Cari karya di Crossref berdasarkan judul/penulis dan tampilkan N kandidat teratas. Hanya MEMBACA.
Pakai:  python scripts/search_crossref.py "Hierarchical fuzzy control Raju Zhou Kisner" [N]"""
import json, sys, urllib.parse, urllib.request
q = sys.argv[1]; n = int(sys.argv[2]) if len(sys.argv) > 2 else 5
url = "https://api.crossref.org/works?" + urllib.parse.urlencode({"query.bibliographic": q, "rows": n})
with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "bib-search/1.0"}), timeout=30) as r:
    items = json.load(r)["message"]["items"]
for i, m in enumerate(items, 1):
    yr = ((m.get("issued") or {}).get("date-parts") or [[None]])[0][0]
    au = ", ".join(a.get("family", "") for a in m.get("author", [])[:4])
    print(f"[{i}] {m.get('DOI')}\n    {(m.get('title') or [''])[0]}\n    {au} | {yr} | {(m.get('container-title') or [''])[0]} | vol {m.get('volume','')} | hlm {m.get('page','')}")

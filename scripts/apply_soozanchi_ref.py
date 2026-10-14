#!/usr/bin/env python3
r"""Menambahkan referensi HANFIS terdahulu (Soozanchi-K. dan Yaghoobi, 2010, verifikasi penutur) ke manuscript/sn-bibliography.bib, mengganti kalimat naskah yang keliru ("grouping vulnerability-adjacent features ... reportedly ... unable to verify or cite") dengan sitasi yang benar, dan mencatat A-59 di HANFIS_RESEARCH_MEMORY.md (versi 2.33).
Metadata diambil dari Crossref (atau dari berkas --json). Penjaga: DOI harus sama dan judul harus memuat HANFIS atau 'Hierarchical Adaptive Network-Based Fuzzy Inference'; kunci/DOI yang sudah ada di .bib tidak ditimpa.
Gagal-tertutup: semua jangkar dan data diperiksa lebih dulu; tidak ada yang ditulis bila salah satunya gagal. Idempoten. Cadangan .pre-sooz.bak.
   python scripts/apply_soozanchi_ref.py --doi 10.1007/978-3-642-15286-3_23 [--key soozanchi2010hanfis] [--json crossref.json] [--today 2026-10-14] [--no-memory]"""
import argparse, json, re, shutil, sys, urllib.request
from pathlib import Path
ap = argparse.ArgumentParser(); ap.add_argument("--doi", required=True); ap.add_argument("--key", default="soozanchi2010hanfis"); ap.add_argument("--json", default=None)
ap.add_argument("--tex", default="manuscript/sn-article.tex"); ap.add_argument("--bib", default="manuscript/sn-bibliography.bib"); ap.add_argument("--today", default="2026-10-14"); ap.add_argument("--no-memory", action="store_true"); a = ap.parse_args()
if not re.fullmatch(r"10\.\d{4,9}/[A-Za-z0-9._()/:;-]+", a.doi): sys.exit("ABORT: --doi tidak berbentuk DOI")
if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_:-]{3,60}", a.key): sys.exit("ABORT: --key tidak valid")
try:
    raw = open(a.json, encoding="utf-8").read() if a.json else urllib.request.urlopen(urllib.request.Request("https://api.crossref.org/works/" + a.doi, headers={"User-Agent": "HANFIS-RESEARCH/1.0 (mailto:mohammadhafizhersyah02@it.unand.ac.id)"}), timeout=30).read().decode("utf-8")
    m = json.loads(raw)["message"]
except Exception as e: sys.exit(f"ABORT: tidak bisa membaca metadata Crossref ({e}); simpan https://api.crossref.org/works/{a.doi} sebagai berkas lalu pakai --json")
if m.get("DOI", "").lower() != a.doi.lower(): sys.exit(f"ABORT: DOI metadata ({m.get('DOI')}) tidak sama dengan --doi")
title = " ".join((m.get("title") or [""])[0].split())
if not re.search(r"HANFIS|Hierarchical Adaptive Network-Based Fuzzy Inference", title, re.I): sys.exit(f"ABORT: judul bukan makalah HANFIS yang dimaksud: {title!r}")
try: year = str(m["issued"]["date-parts"][0][0])
except Exception: sys.exit("ABORT: tahun tidak ada pada metadata")
au = m.get("author") or []
if not au: sys.exit("ABORT: penulis tidak ada pada metadata")
authors = " and ".join(f"{x.get('family', '').strip()}, {x.get('given', '').strip()}" if x.get("given") else x.get("family", "").strip() for x in au)
prot = lambda s: re.sub(r"\b([A-Z]{3,})\b", r"{\1}", s)
ct = m.get("container-title") or []; typ = m.get("type", "")
fields = [("author", authors), ("title", prot(title))]
if typ == "proceedings-article": etype = "inproceedings"; fields.append(("booktitle", ct[0] if ct else ""))
else:
    etype = "incollection"; fields.append(("booktitle", ct[0] if ct else ""))
    if len(ct) > 1: fields.append(("series", ct[1]))
for k in ("volume", "page"):
    if m.get(k): fields.append(("pages" if k == "page" else k, m[k].replace("-", "--") if k == "page" else m[k]))
if m.get("publisher"): fields.append(("publisher", m["publisher"]))
fields += [("year", year), ("doi", a.doi)]
if not dict(fields).get("booktitle"): fields = [f for f in fields if f[0] != "booktitle"]
ENTRY = f"@{etype}{{{a.key},\n" + ",\n".join(f"  {k} = {{{v}}}" for k, v in fields) + "\n}\n"
print("Entri BibTeX yang akan ditambahkan:\n" + ENTRY)
T, B = Path(a.tex), Path(a.bib); s = T.read_text(encoding="utf-8"); b = B.read_text(encoding="utf-8")
CITE = "\\cite{" + a.key + "}"
OLD = re.compile(r"\ba\s+prior\s+hierarchical\s+ANFIS\s+grouping\s+vulnerability-adjacent\s+features\s+has\s+reportedly\s+been\s+published\s+under\s+this\s+name\s+\(Soozanchi\s+et\s+al\.\),\s+though\s+we\s+were\s+unable\s+to\s+independently\s+verify\s+or\s+cite\s+the\s+specific\s+source;\s+and\s+the")
NEW = "a hierarchical ANFIS under this name has been applied to speaker verification, with three groups of sound features~" + CITE + "; and the"
done_tex = (NEW in s); n_old = len(OLD.findall(s))
if not done_tex and n_old != 1: sys.exit(f"ABORT, tidak ada yang ditulis: kalimat lama di naskah ditemukan {n_old}x (harus 1)")
has_key = re.search(r"@\w+\{" + re.escape(a.key) + r"\s*,", b) is not None; has_doi = a.doi.lower() in b.lower()
if has_key != has_doi and (has_key or has_doi): sys.exit("ABORT, tidak ada yang ditulis: kunci atau DOI sudah ada di .bib tetapi tidak keduanya (periksa entri yang ada)")
new_b = b if has_key else (b if b.endswith("\n") else b + "\n") + "\n" + ENTRY
new_s = s if done_tex else OLD.sub(lambda x: NEW, s, count=1)
mem_old = mem_new = None
if not a.no_memory:
    M = Path("HANFIS_RESEARCH_MEMORY.md"); mem_old = M.read_text(encoding="utf-8")
    ROW = ("| A-59 | " + a.today + " | Naskah, referensi | Referensi HANFIS terdahulu diverifikasi: Soozanchi-K. dan Yaghoobi (2010), Speaker Verification System Using a Hierarchical Adaptive Network-Based Fuzzy Inference Systems (HANFIS), DOI " + a.doi + "; makalah itu tentang verifikasi penutur dengan tiga kelompok fitur suara, BUKAN fitur kerentanan; "
           "kalimat naskah yang menyebut vulnerability-adjacent features dan tidak bisa memverifikasi sumbernya keliru dan diganti dengan sitasi " + a.key + "; klaim subtractive clustering untuk makalah itu tidak terverifikasi dalam indeks (teks itu ada pada bab 2012 oleh penulis yang sama) dan tidak dipakai; nama HANFIS-DRS tetap |")
    ROW = ROW.rstrip(" |") + " |"
    if ROW.count("|") != 5: sys.exit("ABORT: baris A-59 harus berisi tepat 5 pipa")
    if re.search(r"^\| A-59 \|", mem_old, re.M): mem_new = re.sub(r"^\| A-59 \|.*$", lambda x: ROW, mem_old, count=1, flags=re.M)
    else:
        r58 = list(re.finditer(r"^\| A-58 \|.*$", mem_old, re.M)); h = list(re.finditer(r"Versi: 2\.32 \u00b7 Tanggal: 2026-10-14", mem_old))
        if len(r58) != 1 or len(h) != 1: sys.exit(f"ABORT, tidak ada yang ditulis: baris A-58 {len(r58)}x, kepala {len(h)}x (harus 1 dan 1; gunakan --no-memory untuk melewati)")
        mem_new = mem_old[:r58[0].end()] + "\n" + ROW + mem_old[r58[0].end():]; mem_new = mem_new.replace("Versi: 2.32 \u00b7 Tanggal: 2026-10-14", f"Versi: 2.33 \u00b7 Tanggal: {a.today}", 1)
changed = []
for P, old, new, name in ((T, s, new_s, "naskah"), (B, b, new_b, "bib")) + (((Path("HANFIS_RESEARCH_MEMORY.md"), mem_old, mem_new, "memori"),) if mem_new is not None else ()):
    if new != old: shutil.copy(P, str(P) + ".pre-sooz.bak"); P.write_text(new, encoding="utf-8"); changed.append(name)
print("OK: " + ", ".join(changed) if changed else "Tidak ada perubahan (sudah sama).")

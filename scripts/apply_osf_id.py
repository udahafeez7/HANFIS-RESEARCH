#!/usr/bin/env python3
"""Mencantumkan registrasi OSF di naskah (Methods E7, paragraf pertama sub-bagian 'Prospective evaluation (E7)'): menambah satu kalimat setelah 'and runs only once.' dengan URL (dan DOI bila ada) registrasi.
--disclose-e14c menambah satu kalimat pengungkapan (E14c dan E15-E20 dijalankan setelah pembekuan dan sebelum registrasi) tepat sesudah kalimat registrasi.\nIdempoten: dijalankan lagi dengan --doi memperbarui kalimat yang sama. Gagal-tertutup (jangkar tepat sekali); cadangan .pre-osfid.bak.
  python scripts/apply_osf_id.py --url https://osf.io/XXXXX [--doi 10.17605/OSF.IO/XXXXX] [--date 2026-10-13] [--disclose-e14c]"""
import argparse, re, shutil, sys
from pathlib import Path
ap = argparse.ArgumentParser(); ap.add_argument("--url", required=True); ap.add_argument("--doi", default=None); ap.add_argument("--date", default="2026-10-13"); ap.add_argument("--disclose-e14c", action="store_true"); ap.add_argument("--tex", default="manuscript/sn-article.tex"); a = ap.parse_args()
if not re.fullmatch(r"https://osf\.io/[A-Za-z0-9]{3,10}/?", a.url): sys.exit("ABORT: --url harus berbentuk https://osf.io/<kode>")
if a.url.rstrip("/").split("/")[-1].lower() in ("9ezg4", "62vq4"): sys.exit("ABORT: kode itu adalah proyek (9ezg4 atau 62vq4), bukan registrasi; gunakan https://osf.io/ahcvs/")
if a.doi and not re.fullmatch(r"10\.\d{4,9}/[A-Za-z0-9._/-]+", a.doi): sys.exit("ABORT: --doi tidak berbentuk DOI (mis. 10.17605/OSF.IO/ABCDE)")
P = Path(a.tex); s = P.read_text(encoding="utf-8"); flex = lambda t: r"\s+".join(map(re.escape, t.split()))
detail = f"registration date {a.date}; \\texttt{{{a.url}}}" + (f"; DOI \\texttt{{{a.doi}}}" if a.doi else "")
SENT = f"The protocol was also registered on the Open Science Framework before any forward label was computed ({detail})."
RX = r"The protocol was also registered on the Open Science Framework before any forward label was computed \([^)]*\)\."
if re.search(RX, s):
    new = re.sub(RX, lambda m: SENT, s, count=1); msg = "kalimat registrasi diperbarui"
else:
    m = list(re.finditer(flex("and runs only once."), s))
    if len(m) != 1: sys.exit(f"ABORT, tidak ada yang ditulis: jangkar 'and runs only once.' ditemukan {len(m)}x (harus 1)")
    new = s[:m[0].end()] + " " + SENT + s[m[0].end():]; msg = "kalimat registrasi ditambahkan"
DISC = "The analyses E14c and E15 to E20 were run on earlier data after the freeze and before the registration; the registration lists E15 to E20 and does not list E14c."
if a.disclose_e14c and DISC not in new:
    k = new.find(SENT)
    if k < 0: sys.exit("ABORT, tidak ada yang ditulis: kalimat registrasi tidak ditemukan untuk pengungkapan E14c")
    new = new[:k + len(SENT)] + " " + DISC + new[k + len(SENT):]; msg += "; kalimat pengungkapan E14c ditambahkan"
if new == s: print("Tidak ada perubahan (sudah sama)."); sys.exit(0)
shutil.copy(P, str(P) + ".pre-osfid.bak"); P.write_text(new, encoding="utf-8"); print(f"OK: {msg}")

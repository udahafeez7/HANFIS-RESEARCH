#!/usr/bin/env python3
"""apply_overleaf_merge_2026-11-11.py - menjadikan sumber Overleaf (zip 2026-11-11) sebagai satu sumber kebenaran di repositori.

Lapisan (P1): naskah (pelaporan). Dokumen: manuscript/sn-article.tex, manuscript/sn-bibliography.bib.
Masukan: direktori hasil ekstraksi zip Overleaf (argumen 1). Hash kedua berkas masukan diperiksa terhadap nilai yang dicatat di bawah
(gagal-tertutup: zip lain ditolak). Berkas repositori diganti utuh, lalu Patch/apply_gate_review_fixes.py dijalankan ulang di atasnya
(tiga perbaikan 11 November yang belum ada di Overleaf). Cadangan: *.pre-overleafmerge.bak. Idempoten: bila hash repositori sudah sama
dengan hasil akhir, keluar 0 tanpa menulis.
Jalankan dari root repo:  python3 Patch/apply_overleaf_merge_2026-11-11.py DIR_EKSTRAK
"""
import hashlib, os, shutil, subprocess, sys

EXPECT = {"sn-article.tex": "05ce5b82d286", "sn-bibliography.bib": "e51c7491611f"}   # 12 heksa pertama sha256 berkas Overleaf
if len(sys.argv) != 2 or not os.path.isdir(sys.argv[1]) or not os.path.isdir(".git"):
    sys.exit("ABORT: pakai  python3 Patch/apply_overleaf_merge_2026-11-11.py DIR_EKSTRAK  dari root repo")
src = sys.argv[1]


def h(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


for name, exp in EXPECT.items():
    p = os.path.join(src, name)
    if not os.path.isfile(p):
        sys.exit(f"ABORT: {p} tidak ada")
    if h(p)[:12] != exp:
        sys.exit(f"ABORT: hash {name} di {src} adalah {h(p)[:12]}, bukan {exp} (zip berbeda); tidak ada yang ditulis")

for name in EXPECT:
    dst = os.path.join("manuscript", name); p = os.path.join(src, name)
    if h(dst) == h(p):
        print(f"{name}: sudah identik dengan Overleaf")
        continue
    shutil.copyfile(dst, dst + ".pre-overleafmerge.bak"); shutil.copyfile(p, dst)
    print(f"{name}: diganti dengan versi Overleaf ({h(p)[:12]}); cadangan {dst}.pre-overleafmerge.bak")

r = subprocess.run([sys.executable, os.path.join("Patch", "apply_gate_review_fixes.py")], capture_output=True, text=True)
print(r.stdout.strip() or r.stderr.strip())
if r.returncode != 0:
    sys.exit("ABORT: perbaikan gerbang gagal diterapkan di atas teks Overleaf: " + (r.stderr.strip() or r.stdout.strip()))
print("STATUS=OVERLEAF_MERGE_DONE", "sn-article.tex", h(os.path.join("manuscript", "sn-article.tex"))[:12])

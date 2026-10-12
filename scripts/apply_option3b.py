#!/usr/bin/env python3
"""Tambahan empiris untuk Opsi 3: CI bootstrap per minggu pada prediksi out-of-fold (45 minggu) sekitar tiga kali lebih lebar daripada CI per image; aturan pelaporan bila sensitivitas per minggu tidak sejalan.
Menambah satu kalimat pada butir 'Ketergantungan antar minggu' (protokol bagian 6) dan pada paragraf Power di teks OSF. Tidak mengubah hipotesis, ambang, atau keputusan. Gagal-tertutup, idempoten, cadangan .pre-opt3b.bak.
  python scripts/apply_option3b.py [--protocol ...] [--osf ...]"""
import argparse, re, shutil, sys
from pathlib import Path
ap = argparse.ArgumentParser(); ap.add_argument("--protocol", default="protocols/E7_preregistration_CANDIDATE.md"); ap.add_argument("--osf", default="protocols/E7_osf_registration_DRAFT.md"); a = ap.parse_args()
flex = lambda t: r"\s+".join(map(re.escape, t.split()))
JOBS = [(a.protocol, "bootstrap per minggu dilaporkan sebagai sensitivitas, tanpa kriteria.", " Pada prediksi out-of-fold (45 minggu), CI95 keunggulan rumus terhadap persistence dengan bootstrap per minggu, [+0,127; +0,672], sekitar tiga kali lebih lebar daripada dengan bootstrap per image, [+0,263; +0,425]. Keputusan konfirmatori mengikuti prosedur per image yang didaftarkan; bila kriteria terpenuhi menurut prosedur per image tetapi tidak menurut sensitivitas per minggu, hasilnya dilaporkan sebagai terkonfirmasi menurut inferensi per image dan rapuh menurut inferensi per minggu.", "sekitar tiga kali lebih lebar"),
        (a.osf, "with six weeks the effective number of time points is six.", " In out-of-fold data (45 weeks) the week-clustered 95% CI for the formula's skill against persistence ([+0.127, +0.672]) was about three times wider than the image-clustered one ([+0.263, +0.425]); a result that meets its criterion under image-clustered inference but not under the week-clustered sensitivity will be reported as such (confirmed by image-clustered inference, fragile by week-clustered inference).", "about three times wider")]
plans = []
for path, anchor, add, marker in JOBS:
    p = Path(path)
    if not p.exists(): print(f"DILEWATI (berkas tidak ada): {path}"); continue
    s = p.read_text(encoding="utf-8")
    if marker in s: print(f"sudah diterapkan: {path}"); continue
    m = list(re.finditer(flex(anchor), s))
    if len(m) != 1: print(f"ABORT, tidak ada yang ditulis: jangkar di {path} ditemukan {len(m)}x (harus 1)"); sys.exit(2)
    plans.append((p, s[:m[0].end()] + add + s[m[0].end():]))
for p, new in plans: shutil.copy(p, str(p) + ".pre-opt3b.bak"); p.write_text(new, encoding="utf-8"); print(f"OK: kalimat ditambahkan di {p}")

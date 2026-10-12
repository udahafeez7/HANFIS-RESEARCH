#!/usr/bin/env python3
"""Perinci kontribusi penulis pada Declarations (Author contribution): D.D. (jaringan saraf tiruan) dan B.R. (arsitektur jaringan). Teks lama: 'D.D. and B.R.: supervision, methodology review, writing -- review and editing.'
Peran M.H.H. tidak diubah. Gagal-tertutup (jangkar tepat sekali); idempoten; cadangan .pre-contrib.bak. Rumusan harus dikonfirmasi oleh kedua ko-penulis.  Dari akar repo."""
import re, shutil, sys
from pathlib import Path
P = Path("manuscript/sn-article.tex"); s = P.read_text(encoding="utf-8")
flex = lambda t: r"\s+".join(map(re.escape, t.split()))
OLD = "D.D. and B.R.: supervision, methodology review, writing -- review and editing."
NEW = ("D.D.: supervision, contribution to the neural network component, methodology review, writing -- review and editing. "
       "B.R.: supervision, contribution to the network architecture, methodology review, writing -- review and editing.")
if "contribution to the neural network component" in s: print("Sudah diterapkan."); sys.exit(0)
m = list(re.finditer(flex(OLD), s))
if len(m) != 1: print(f"ABORT, tidak ada yang ditulis: kalimat kontribusi ditemukan {len(m)}x (harus 1)"); sys.exit(2)
shutil.copy(P, str(P) + ".pre-contrib.bak"); P.write_text(s[:m[0].start()] + NEW + s[m[0].end():], encoding="utf-8"); print("OK: kontribusi D.D. dan B.R. dirinci di Declarations")

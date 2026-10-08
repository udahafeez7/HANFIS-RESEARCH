#!/usr/bin/env python3
"""Sisipkan satu kalimat definisi 'pre-registered' di awal subbagian Training configuration (tepat setelah \\label bila ada). Dari akar repo. Gagal-tertutup; idempoten; cadangan .pre-prereg.bak."""
import re, shutil, sys
from pathlib import Path
P = Path("manuscript/sn-article.tex"); s = P.read_text(encoding="utf-8")
SENT = (r"Throughout, ``pre-registered'' means that a dated protocol was committed to the project's version-controlled repository and tagged before the corresponding training run; "
        r"it does not refer to an entry in an external registry. The confirmatory protocol was committed on 30 September 2026 and tagged the same day "
        r"(tag \texttt{e4-prereg-2026-09-29}, whose name carries the nominal date of the protocol file), and the first confirmatory training run took place on 2 October 2026." "\n")
if "means that a dated protocol was committed" in s: print("Sudah diterapkan; tidak ada perubahan."); sys.exit(0)
pat = re.compile(r"(\\subsection\{Training configuration\}[ \t]*\n(?:\\label\{[^}]*\}[ \t]*\n)?)")
m = list(pat.finditer(s))
if len(m) != 1: sys.exit(f"ABORT: \\subsection{{Training configuration}} ditemukan {len(m)}x (harus 1); tidak ada yang ditulis")
shutil.copy(P, str(P) + ".pre-prereg.bak"); P.write_text(s[:m[0].end()] + SENT + s[m[0].end():], encoding="utf-8"); print("OK: definisi pre-registered ditambahkan")

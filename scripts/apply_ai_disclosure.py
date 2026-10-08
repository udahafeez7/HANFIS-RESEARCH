#!/usr/bin/env python3
"""Tambah butir 'Use of AI tools' di akhir daftar Declarations (sebelum \\end{itemize} pertama setelah \\section*{Declarations}).
JALANKAN HANYA setelah Anda memeriksa kebijakan Springer Nature / jurnal dan memastikan setiap klaim di kalimat ini benar untuk Anda
(alat, versi, dan fungsinya); sunting kalimat di bawah bila perlu. Gagal-tertutup; idempoten; cadangan .pre-ai.bak. Dari akar repo."""
import re, shutil, sys
from pathlib import Path
P = Path("manuscript/sn-article.tex"); s = P.read_text(encoding="utf-8")
ITEM = (r"\item \textbf{Use of AI tools.} During the preparation of this work the authors used an AI assistant (Claude, Anthropic) to help write and test analysis and utility code, "
        r"to draft and revise manuscript text, and to review study protocols. The authors ran and verified all code and results, reviewed and edited all text, "
        r"and take full responsibility for the content of the publication.")
if "Use of AI tools" in s: print("Sudah diterapkan; tidak ada perubahan."); sys.exit(0)
a = [m.start() for m in re.finditer(re.escape(r"\section*{Declarations}"), s)]
if len(a) != 1: sys.exit(f"ABORT: \\section*{{Declarations}} ditemukan {len(a)}x (harus 1); tidak ada yang ditulis")
e = s.find(r"\end{itemize}", a[0])
if e < 0: sys.exit("ABORT: \\end{itemize} setelah Declarations tidak ditemukan")
shutil.copy(P, str(P) + ".pre-ai.bak"); P.write_text(s[:e] + ITEM + "\n" + s[e:], encoding="utf-8"); print("OK: butir Use of AI tools ditambahkan")

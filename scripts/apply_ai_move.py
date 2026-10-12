#!/usr/bin/env python3
"""Pindahkan paragraf 'Use of AI tools' dari awal bagian Results (tempat apply_ai_methods.py menyisipkannya secara keliru, tepat setelah \\section{Results}) ke akhir Methods sebagai \\subsection*{Use of AI tools},
yaitu sebelum \\section{Results} (setelah sub-bagian E7 bila sudah ada). Teks paragraf tidak diubah. Gagal-tertutup (paragraf dan jangkar harus ada tepat sekali); idempoten; cadangan .pre-aimove.bak.  Dari akar repo."""
import re, shutil, sys
from pathlib import Path
P = Path("manuscript/sn-article.tex"); s = P.read_text(encoding="utf-8")
flex = lambda t: r"\s+".join(map(re.escape, t.split()))
if "\\subsection*{Use of AI tools}" in s: print("Sudah diterapkan."); sys.exit(0)
PARA = ("\\paragraph{Use of AI tools.} An AI assistant (Claude, Anthropic) was used to help write and test analysis and utility code, to draft and revise manuscript text, and to review study protocols. "
        "All experiments were run by the authors, who verified the code and the results, reviewed and edited all text, and take full responsibility for the content; the assistant is not an author (see Declarations).")
m = list(re.finditer(flex(PARA), s)); a = list(re.finditer(re.escape("\\section{Results}\\label{sec4}"), s))
if len(m) != 1 or len(a) != 1: print(f"ABORT, tidak ada yang ditulis: paragraf ditemukan {len(m)}x, jangkar Results {len(a)}x (harus 1 dan 1)"); sys.exit(2)
if not (a[0].end() < m[0].start()): print("ABORT: paragraf tidak berada setelah \\section{Results}; sudah di tempat lain? periksa manual"); sys.exit(2)
text = PARA.replace("\\paragraph{Use of AI tools.} ", "", 1)
new = s[:a[0].start()] + "\\subsection*{Use of AI tools}\n" + text + "\n\n" + s[a[0].start():m[0].start()] + s[m[0].end():].lstrip("\n")
shutil.copy(P, str(P) + ".pre-aimove.bak"); P.write_text(new, encoding="utf-8"); print("OK: paragraf dipindah ke akhir Methods (sebelum \\section{Results})")

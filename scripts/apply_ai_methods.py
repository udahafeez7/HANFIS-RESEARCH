#!/usr/bin/env python3
"""Tambah paragraf 'Use of AI tools' di Methods (sebelum sub-bagian 'Observability overhead'), mencerminkan butir di Declarations. Alasan: kebijakan penerbit (sejauh
yang saya ingat; VERIFIKASI di halaman panduan penulis jurnal) meminta penggunaan LLM yang substantif didokumentasikan di Methods, bukan hanya di Declarations.
Jangkar fleksibel terhadap pemisah baris; gagal-tertutup (tepat 1 kecocokan); idempoten; cadangan .pre-aimethods.bak. Dari akar repo."""
import re, shutil, sys
from pathlib import Path
P = Path("manuscript/sn-article.tex"); s = P.read_text(encoding="utf-8")
flex = lambda t: r"\s+".join(map(re.escape, t.split()))
NEW = (r"\paragraph{Use of AI tools.} An AI assistant (Claude, Anthropic) was used to help write and test analysis and utility code, to draft and revise manuscript text, and to review study protocols. "
       r"All experiments were run by the authors, who verified the code and the results, reviewed and edited all text, and take full responsibility for the content; the assistant is not an author (see Declarations).")
if "\\paragraph{Use of AI tools.}" in s: print("Sudah diterapkan."); sys.exit(0)
m = list(re.finditer(flex(r"\subsection{Observability overhead}"), s))
if len(m) != 1: print(f"ABORT: jangkar '\\subsection{{Observability overhead}}' ditemukan {len(m)}x (harus 1); tidak ada yang ditulis"); sys.exit(2)
shutil.copy(P, str(P) + ".pre-aimethods.bak"); P.write_text(s[:m[0].start()] + NEW + "\n\n" + s[m[0].start():], encoding="utf-8"); print("OK: paragraf ditambahkan sebelum \\subsection{Observability overhead}")

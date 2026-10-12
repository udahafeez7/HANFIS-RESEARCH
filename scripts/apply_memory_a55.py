#!/usr/bin/env python3
"""Amandemen A-55 pada HANFIS_RESEARCH_MEMORY.md: perubahan naskah sesudah pembekuan E7 (Methods evaluasi prospektif, pernyataan AI dipindah ke Methods, Limitations Red Hat, kontribusi penulis D.D. dan B.R.); versi 2.29.
Baris disisipkan setelah baris A-54. Gagal-tertutup; idempoten; cadangan .pre-a55.bak.  Komit: 'memory: A-55 ...'"""
import re, shutil, sys
from pathlib import Path
P = Path("HANFIS_RESEARCH_MEMORY.md"); s = P.read_text(encoding="utf-8")
if re.search(r"^\| A-55 \|", s, re.M): print("Sudah diterapkan (A-55 ada)."); sys.exit(0)
ROW = "| A-55 | 2026-10-12 | Naskah | Sesudah pembekuan E7: sub-bagian Methods `Prospective evaluation (E7): pre-registered design` (label subsec:e7; merujuk tag e7-prereg-2026-10-12; hasil menunggu D2); kalimat Discussion dinyatakan pre-registered; kalimat Limitations tentang mekanisme INSUFFICIENT_EVIDENCE (status under_investigation pada CVE Red Hat baru); pernyataan penggunaan AI dipindah dari awal Results ke akhir Methods (`\\subsection*{Use of AI tools}`); kontribusi penulis dirinci: D.D. (komponen jaringan saraf tiruan) dan B.R. (arsitektur jaringan) (komit ed0bf06 dan berikutnya) |"
m = list(re.finditer(r"^\| A-54 \|.*$", s, re.M)); h = list(re.finditer(r"Versi: 2\.28 · Tanggal: 2026-10-12", s))
if len(m) != 1 or len(h) != 1: print(f"ABORT, tidak ada yang ditulis: baris A-54 {len(m)}x, kepala {len(h)}x (harus 1 dan 1)"); sys.exit(2)
s = s[:m[0].end()] + "\n" + ROW + s[m[0].end():]; s = s.replace("Versi: 2.28 · Tanggal: 2026-10-12", "Versi: 2.29 · Tanggal: 2026-10-12", 1)
shutil.copy(P, str(P) + ".pre-a55.bak"); P.write_text(s, encoding="utf-8"); print("OK: A-55 ditambahkan; versi 2.29")

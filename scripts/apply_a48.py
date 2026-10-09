#!/usr/bin/env python3
"""A-48: koreksi 6.833 (total baris) vs 6.357 (berlabel) di naskah, dan penyelarasan baris 'Model akhir' draf E7 dengan A-47. Dari akar repo.
Gagal-tertutup: bila SATU jangkar tidak cocok tepat sekali, tidak ada berkas yang ditulis. Idempoten. Cadangan .pre-a48.bak."""
import re, shutil, sys
from pathlib import Path
MS, DR, ME = Path("manuscript/sn-article.tex"), Path("protocols/E7_preregistration_DRAFT.md"), Path("HANFIS_RESEARCH_MEMORY.md")
EDITS = [
    ("gerbang-data (Limitations)", r"($6{,}833$ rows against 176 parameters)", r"($6{,}357$ labelled rows against 176 parameters)"),
    ("Conclusion (baris 6.833 labelled)", r"6{,}833 labelled", r"6{,}357 labelled"),
    ("Limitations (pengulangan frasa)", r"On the full 120-asset inventory (6{,}357 labelled rows;", r"On the same inventory (6{,}357 labelled rows;"),
]
ROWFIX = ("| Model akhir | dilatih ulang pada minggu berlabel **<= 2026-07-27** (minggu forward pertama 2026-08-31 dikurangi embargo 30 hari; A-47), konfigurasi A-09 + A-10, lima seed yang sama; "
          "hash berkas dicatat sebelum tag | cek gerbang >= 10 observasi per parameter (sekitar 33: sekitar 5.880 baris latih / 176 parameter) |")
ROW = ("| A-48 | 2026-10-09 | Naskah, E7 | Koreksi angka: 6.833 adalah total baris event_id (berkas status: non-NA 0,9303, positif 0,8882, 119 grup image), 6.357 berlabel; observasi per parameter pada sampel gabungan "
       "6.357/176 = 36,1 (bukan 38,8). Naskah diperbaiki di Limitations (gerbang kecukupan data) dan Conclusion (\"6.833 labelled\"); letaknya BUKAN di abstrak seperti tertulis di laporan harian 2026-10-08. "
       "Baris 'Model akhir' draf E7 diselaraskan dengan A-47 (latih <= 2026-07-27, sekitar 5.880 baris, sekitar 33 observasi/parameter) agar protokol yang dibekukan tidak memuat dua batas yang saling bertentangan. |")
ms, dr, me = (p.read_text(encoding="utf-8") for p in (MS, DR, ME))
errors, todo = [], []
for name, old, new in EDITS:
    n = ms.count(old)
    if n == 1: todo.append((old, new)); print(f"akan diterapkan: {name}")
    elif n == 0 and ms.count(new) >= 1: print(f"sudah: {name}")
    else: errors.append(f"{name}: jangkar ditemukan {n}x (harus 1)")
rows = list(re.finditer(r"^\| Model akhir \|.*$", dr, re.M))
if len(rows) == 1 and rows[0].group(0) != ROWFIX: print("akan diterapkan: baris 'Model akhir' draf E7")
elif len(rows) == 1: print("sudah: baris 'Model akhir'")
else: errors.append(f"baris 'Model akhir' di draf E7 ditemukan {len(rows)}x (harus 1)")
has48 = bool(re.search(r"^\| A-48 \|", me, re.M)); a47 = list(re.finditer(r"^\| A-47 \|.*$", me, re.M))
if not has48 and len(a47) != 1: errors.append(f"baris A-47 di memori ditemukan {len(a47)}x (harus 1)")
if errors:
    print("ABORT, tidak ada yang ditulis:"); [print("  -", e) for e in errors]; sys.exit(2)
changed = False
if todo:
    for old, new in todo: ms = ms.replace(old, new)
    shutil.copy(MS, str(MS) + ".pre-a48.bak"); MS.write_text(ms, encoding="utf-8"); changed = True
if rows[0].group(0) != ROWFIX:
    dr = dr[:rows[0].start()] + ROWFIX + dr[rows[0].end():]; shutil.copy(DR, str(DR) + ".pre-a48.bak"); DR.write_text(dr, encoding="utf-8"); changed = True
if not has48:
    me = me[:a47[0].end()] + "\n" + ROW + me[a47[0].end():]
    h = re.search(r"Versi: (\d+)\.(\d+) · Tanggal: \d{4}-\d{2}-\d{2}", me)
    if h: me = me.replace(h.group(0), f"Versi: {h.group(1)}.{int(h.group(2)) + 1} · Tanggal: 2026-10-09", 1)
    shutil.copy(ME, str(ME) + ".pre-a48.bak"); ME.write_text(me, encoding="utf-8"); changed = True
print("OK: A-48 diterapkan" if changed else "Sudah diterapkan seluruhnya; tidak ada perubahan.")

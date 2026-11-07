#!/usr/bin/env python3
"""apply_e7_table_width_fix.py - memendekkan sel keputusan P7a dan P7f di tabel hasil E7 ('Supported (HANFIS not better)' menjadi 'Supported (not better)') karena versi panjang membuat tabel melebihi lebar teks (Overfull 36 pt).

Lapisan (P1): naskah (tata letak). Dokumen: manuscript/sn-article.tex. Kalimat teks 'P7a supported: HANFIS not better' tidak berubah. Tidak ada angka, kutipan, atau rujukan yang berubah.
Teks-persis, gagal-tertutup: tiap teks lama harus cocok TEPAT SATU KALI (spasi dan baris baru dinormalkan) sebelum apa pun ditulis.
Idempoten: bila semua teks baru sudah terpasang, keluar 0 tanpa menulis. Keadaan campuran = ABORT.
Akhir baris (LF/CRLF) dipertahankan. Cadangan: manuscript/sn-article.tex.pre-width.bak.
Jalankan dari root repo:  python3 Patch/apply_e7_table_width_fix.py
"""
import os, re, sys

P = os.path.join("manuscript", "sn-article.tex")
if not (os.path.isfile(P) and os.path.isdir(".git")):
    sys.exit("ABORT: jalankan dari root repo (harus ada .git dan manuscript/sn-article.tex)")

PAIRS = [('[$-$9.177, $-$1.594] & Supported (HANFIS not better) \\\\', '[$-$9.177, $-$1.594] & Supported (not better) \\\\'),
 ('[$-$13.677, $-$3.188] & Supported (HANFIS not better) \\\\', '[$-$13.677, $-$3.188] & Supported (not better) \\\\')]


def rx(text):
    return re.compile(r"\s+".join(re.escape(t) for t in text.split()))


raw = open(P, "rb").read()
crlf = b"\r\n" in raw
s = raw.decode("utf-8").replace("\r\n", "\n")

state = []
for n, (old, new) in enumerate(PAIRS, 1):
    co, cn = len(rx(old).findall(s)), len(rx(new).findall(s))
    nrm = lambda z: " ".join(z.split())
    if co == 1 and cn == 0:
        state.append("old")
    elif cn >= 1 and (co == 0 or nrm(old) in nrm(new)):
        state.append("new")
    else:
        sys.exit(f"ABORT: pasangan {n}: teks lama cocok {co} kali, teks baru {cn} kali; tidak ada yang ditulis")
if all(x == "new" for x in state):
    print("SUDAH TERPASANG: semua", len(PAIRS), "suntingan; tidak ada yang ditulis")
    sys.exit(0)
if any(x == "new" for x in state):
    sys.exit("ABORT: keadaan campuran (sebagian suntingan sudah terpasang); tidak ada yang ditulis")

for n, (old, new) in enumerate(PAIRS, 1):
    s, k = rx(old).subn(lambda m, new=new: new, s, count=1)
    if k != 1:
        sys.exit(f"ABORT: pasangan {n} tidak dapat diterapkan; tidak ada yang ditulis")

out = (s.replace("\n", "\r\n") if crlf else s).encode("utf-8")
with open(P + ".pre-width.bak", "wb") as f:
    f.write(raw)
with open(P, "wb") as f:
    f.write(out)
print("OK", len(PAIRS), "suntingan |", "CRLF" if crlf else "LF", "| cadangan", P + ".pre-width.bak")

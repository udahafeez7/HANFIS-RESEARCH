#!/usr/bin/env python3
"""apply_gate_review_fixes.py - tiga perbaikan dari pemeriksaan ulang gerbang 2026-11-11.

Lapisan (P1): naskah (pelaporan). Dokumen: manuscript/sn-article.tex. (1) tanda '>' di luar mode matematika tercetak sebagai tanda tanya terbalik di PDF; (2) 'C1/H2' menjadi 'C1 and H2/H3' agar konsisten dengan label protokol;
(3) kalimat pembekuan E4 dibuat persis: tag e4-prereg-2026-09-29 (komit 7b09a4b, 2026-09-30 11:35 WIB) memuat protokol, seed, kode split dan model HANFIS, tetapi flat_anfis_matched.py (b2a2b47, 2026-09-30 11:58) dan e4_run.py (86bf494, 2026-10-01 11:00) dikomit sesudahnya dan sebelum run pertama (prediksi 2026-10-01T04:00Z); run 120 aset yang dilaporkan 2026-10-02. Tidak ada angka hasil yang berubah.
Teks-persis, gagal-tertutup: tiap teks lama harus cocok TEPAT SATU KALI (spasi dan baris baru dinormalkan) sebelum apa pun ditulis.
Idempoten: bila semua teks baru sudah terpasang, keluar 0 tanpa menulis. Keadaan campuran = ABORT.
Akhir baris (LF/CRLF) dipertahankan. Cadangan: manuscript/sn-article.tex.pre-gatefix.bak.
Jalankan dari root repo:  python3 Patch/apply_gate_review_fixes.py
"""
import os, re, sys

P = os.path.join("manuscript", "sn-article.tex")
if not (os.path.isfile(P) and os.path.isdir(".git")):
    sys.exit("ABORT: jalankan dari root repo (harus ada .git dan manuscript/sn-article.tex)")

PAIRS = [('(ratio >$1{,}000\\times$ in the most extreme case)', '(ratio $>1{,}000\\times$ in the most extreme case)'),
 ('We read this as suggestive of the mechanism claimed in C1/H2, not as a methodological artefact',
  'We read this as suggestive of the mechanism claimed in C1 and H2/H3, not as a methodological artefact'),
 ('The confirmatory protocol was committed on 30 September 2026 and tagged the same day (tag \\texttt{e4-prereg-2026-09-29}, whose name carries the '
  'nominal date of the protocol file), and the first confirmatory training run took place on 2 October 2026.',
  'The confirmatory protocol was committed on 30 September 2026 and tagged the same day (tag \\texttt{e4-prereg-2026-09-29}, whose name carries the '
  'nominal date of the protocol file). The tag covers the protocol, the seed list, the split code and the HANFIS model code. The parameter-matched '
  'flat comparator and the training script were committed on 30 September and 1 October 2026, after the tag but before the first confirmatory run on '
  '1 October 2026 (109-asset inventory); the 120-asset run reported here took place on 2 October 2026. Later additions to the training script '
  '(saving models, recording the normalisation) do not change its predictions.')]


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
with open(P + ".pre-gatefix.bak", "wb") as f:
    f.write(raw)
with open(P, "wb") as f:
    f.write(out)
print("OK", len(PAIRS), "suntingan |", "CRLF" if crlf else "LF", "| cadangan", P + ".pre-gatefix.bak")

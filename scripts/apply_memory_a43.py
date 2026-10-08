#!/usr/bin/env python3
"""Catat amendemen A-43 (E6: hasil, deviasi prosedural pembekuan) di HANFIS_RESEARCH_MEMORY.md. Jalankan dari akar repo (/mnt/c/Research/ANFIS).
Gagal-tertutup bila baris A-42 tidak ditemukan tepat sekali (tidak ada yang ditulis); idempoten; membuat cadangan .pre-a43.bak.
Dua perubahan lain bersifat opsional (peringatan, bukan abort): versi/tanggal kepala berkas dan penandaan klaim 'penjelasan berlapis' di bagian 3."""
import re, shutil, sys
from pathlib import Path
P = Path("HANFIS_RESEARCH_MEMORY.md")
s = P.read_text(encoding="utf-8")
if re.search(r"^\| A-43 \|", s, re.M): print("A-43 sudah ada; tidak ada perubahan."); sys.exit(0)
ROW = ("| A-43 | 2026-10-08 | Eksperimen E6, proses | E6 (kesetiaan penjelasan; `scripts/e6_explain.py` sha256 `bcb63a70b3ef32e9…`; `--smoke` lulus: replikasi `y_hanfis` E4 dari 25 model tersimpan, "
       "selisih ≤ 1,44e-06, agregasi rata-rata 5 seed; run 5 Okt vs 2 Okt: selisih 0 pada 1.080 baris). Run pertama 2026-10-08T06:24:34Z, k = 3, rasio ≥ 2, proporsi ≥ 0,90, 100 undian, seed 20261007: "
       "H6-0, H6-neg, H6a, H6b lulus; **H6c gagal** (rasio 4,11 lulus; proporsi 0,835 < 0,90; 5.400 baris, 456 degenerat) → klaim \"penjelasan berlapis\" tidak masuk naskah (konsekuensi praregistrasi); "
       "hasil dilaporkan apa adanya, ambang tidak diubah. **Deviasi prosedural:** tag `e6-prereg-20261008` dibuat pada `f99437a` sebelum komit yang memuat skrip dan teks protokol (`git commit` pertama gagal, "
       "\"no changes added\"; skrip pembeku tidak pernah sampai ke `Patch`); teks protokol saat run = `protocols/E6_preregistration_DRAFT.md` (8.104 byte, sha256 `9a388a64de994777…`, masih bertanda DRAFT dan [PUTUSKAN]); "
       "ambang diumumkan sebelum run dan tercatat di argumen JSON hasil; komit `13bfe44` memuat skrip, teks protokol, dan hasil; tag tidak dipindahkan. Penjaga `--run` hanya memeriksa nama tag, bukan isi pohonnya. |")
m = list(re.finditer(r"^\| A-42 \|.*$", s, re.M))
if len(m) != 1: sys.exit(f"ABORT: baris A-42 ditemukan {len(m)}x (harus 1); tidak ada yang ditulis")
s = s[:m[0].end()] + "\n" + ROW + s[m[0].end():]
h = re.search(r"Versi: (\d+)\.(\d+) · Tanggal: \d{4}-\d{2}-\d{2}", s)
if h: s = s.replace(h.group(0), f"Versi: {h.group(1)}.{int(h.group(2)) + 1} · Tanggal: 2026-10-08", 1)
else: print("PERINGATAN: kepala berkas (Versi/Tanggal) tidak ditemukan; perbarui manual")
OLD = "penjelasan berlapis (jejak, masking, permukaan)"
if s.count(OLD) == 1:
    s = s.replace(OLD, OLD + " [DICABUT 2026-10-08 oleh A-43: H6c gagal; jejak aturan (H6-0 lulus) boleh dideskripsikan, kesetiaan atribusi/masking tidak boleh diklaim]")
else: print(f"PERINGATAN: frasa klaim di bagian 3 ditemukan {s.count(OLD)}x; tandai manual")
shutil.copy(P, str(P) + ".pre-a43.bak"); P.write_text(s, encoding="utf-8"); print("OK: A-43 ditambahkan")

#!/usr/bin/env python3
"""Tambahan kecil pada protokol E7 sebelum pembekuan: (1) bagian 1: paragraf 'Peran rumus bentuk-maks'; (2) bagian 6: butir E12 (post hoc, deskriptif) dan butir daya P7e/P7f.
Tidak mengubah hipotesis, ambang, atau angka mana pun. Gagal-tertutup (bagian 1 dan 6 harus ada), idempoten (berhenti bila 'E12 (post hoc' sudah ada), cadangan .pre-sec16.bak.
  python scripts/apply_e7_sec1_6.py [--file protocols/E7_preregistration_CANDIDATE.md]"""
import argparse, re, shutil, sys
from pathlib import Path
ap = argparse.ArgumentParser(); ap.add_argument("--file", default="protocols/E7_preregistration_CANDIDATE.md"); a = ap.parse_args()
P = Path(a.file); s = P.read_text(encoding="utf-8")
if "E12 (post hoc" in s: print("Sudah diterapkan."); sys.exit(0)
S1 = ("**Peran rumus bentuk-maks.** Analisis post hoc E11 dan E12 (out-of-fold, bukan konfirmatori) menunjukkan bahwa rumus empat parameter dari x2 dan x7 memiliki kesalahan lebih kecil daripada HANFIS dan daripada persistence, "
      "dan bahwa campuran lintas-fold antara rumus dan persistence atau HANFIS tidak memperbaikinya. E7 karena itu juga menguji rumus itu secara prospektif (P7e dan P7f, bagian 5), di samping hipotesis reaktivitas HANFIS di atas.")
S6 = ("- **E12 (post hoc, deskriptif).** Campuran rumus dengan persistence (bobot rumus 1,0 pada kelima fold) dan dengan HANFIS (bobot rumus 0,91 sampai 0,98), dengan bobot dipasang pada fold lain, tidak menurunkan kesalahan rumus "
      "(SS campuran rumus+HANFIS terhadap rumus -0,001, CI95 [-0,010; +0,003]); pada data out-of-fold persistence dan HANFIS tidak menambah informasi di luar rumus. Ini bukan hipotesis E7 dan tidak dihitung sebagai konfirmasi.\n"
      "- **Daya P7e dan P7f.** Keduanya mewarisi keterbatasan daya enam minggu dan ekor berat yang sama; hasil TIDAK TERBUKTI atau TIDAK TERKONFIRMASI tidak boleh dibaca sebagai kesetaraan.")
secs = {int(m.group(1)): m for m in re.finditer(r"^## (\d+)\. .*$", s, re.M)}
if not all(k in secs for k in (1, 2, 6, 7)): print("ABORT: bagian 1, 2, 6, atau 7 tidak ditemukan; tidak ada yang ditulis"); sys.exit(2)
def end_of(n, nxt): return secs[n].end() + len(s[secs[n].end():secs[nxt].start()].rstrip())
edits = [(end_of(6, 7), "\n" + S6), (end_of(1, 2), "\n\n" + S1)]
for pos, text in sorted(edits, key=lambda t: -t[0]): s = s[:pos] + text + s[pos:]
shutil.copy(P, str(P) + ".pre-sec16.bak"); P.write_text(s, encoding="utf-8"); print(f"OK: bagian 1 dan 6 diperbarui di {P}")

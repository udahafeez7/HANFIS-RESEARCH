#!/usr/bin/env python3
r"""Mencatat A-62 (pemeriksaan pra-D2 14 Okt: T1 sampai T4, image cosign, tiga revisi runbook) di HANFIS_RESEARCH_MEMORY.md dan menaikkan versi 2.35 -> 2.36.
Gagal-tertutup: baris A-61 dan kepala 'Versi: 2.35 · Tanggal: 2026-10-14' harus ada tepat sekali; baris A-62 harus berisi tepat 5 pipa. Idempoten (baris A-62 yang ada diganti). Cadangan .pre-a62.bak.
   python scripts/apply_memory_a62.py [--today 2026-10-14]"""
import argparse, re, shutil, sys
from pathlib import Path
ap = argparse.ArgumentParser(); ap.add_argument("--today", default="2026-10-14"); a = ap.parse_args()
M = Path("HANFIS_RESEARCH_MEMORY.md"); m = M.read_text(encoding="utf-8")
ROW = ("| A-62 | " + a.today + " | Testbed, runbook D2 | Pemeriksaan pra-D2 (hanya membaca, kecuali satu `docker pull`; tidak ada tahap D2 dijalankan, tidak ada artefak beku diubah). "
 "(T1) `configs/assets_v3.csv` belum ada karena dibuat oleh tahap `rescan` D2 (protokol langkah D2, docstring `e7_rescan.py`), bukan berkas beku; `configs/assets.csv` 121 baris; empat `configs/assets_*` tak terlacak (e14_tmp, v3_cold3, v3_rehearsal, v3_rehearsal10) adalah keluaran gladi dan tidak dikomit. "
 "(T2) tiga berkas berubah sejak tag e7-prereg-2026-10-12, semuanya di luar 23 berkas beku (verifikasi lolos, pohon kerja bersih): `scripts/e7_freeze_check.py` (komit 63348e4, pemeriksa pembekuan v4; menambah jalur keluar STATUS=E7_FREEZE_READY_TO_FILL bila hanya placeholder tersisa; tidak ada di catatan pembekuan dan tidak dipanggil D2), `scripts/e14_common_weeks.py` (9 baris; skrip post hoc E14c) dan `protocols/E7_osf_registration_DRAFT.md` (4 baris; salinan kerja teks OSF); protokol yang berlaku tidak berubah. "
 "(T3) angka disk di runbook dikoreksi (631 GB bebas dari 930 GB; semula tertulis 300 GB). "
 "(T4) pembacaan kode: state resmi rescan `data/evidence/e7_rescan_2026-11-02.json` (tag = tanggal D2; state gladi cold3, rehearsal, rehearsal10 tidak bentrok); `e7_d2.py --redo` hanya menghapus catatan tahap dan tidak meneruskan --resume; tahap gagal tidak tercatat selesai di d2_state.json (belum ada), jadi ulangan rescan = hapus state lalu `--stage rescan` dari awal dengan unduhan DB baru (belum diuji); runner memakai tanggal UTC, mulai paling cepat 07.00 WIB; `e7_rescan.py --dry-run` kembali sebelum menyentuh state, DB, atau Docker: 120 aset menjadi 119 target. "
 "(cosign) dari 119 image unik hanya `gcr.io/projectsigstore/cosign@sha256:dc905e43...` yang tidak ada di Docker lokal; menurut pesan galat `scan_image_evidence.sh` pemeriksaan ID lokal hanya untuk image tanpa digest, dan `docker pull` berhasil dengan digest yang sama (registri masih menyajikannya), sehingga kini ada lokal. "
 "Runbook direvisi tiga kali (komit 16a1733, 6c7d82b, 0b28877; rev 3 memuat kamus status runner, `scripts/apply_runbook_v3.py` sha256 d8237a65b6619c4c) |")
if ROW.count("|") != 5: sys.exit(f"ABORT: baris A-62 harus berisi tepat 5 pipa (ada {ROW.count('|')})")
if re.search(r"^\| A-62 \|", m, re.M): new = re.sub(r"^\| A-62 \|.*$", lambda x: ROW, m, count=1, flags=re.M)
else:
    r61 = list(re.finditer(r"^\| A-61 \|.*$", m, re.M)); h = list(re.finditer(r"Versi: 2\.35 \u00b7 Tanggal: 2026-10-14", m))
    if len(r61) != 1 or len(h) != 1: sys.exit(f"ABORT, tidak ada yang ditulis: baris A-61 {len(r61)}x, kepala {len(h)}x (harus 1 dan 1)")
    new = m[:r61[0].end()] + "\n" + ROW + m[r61[0].end():]; new = new.replace("Versi: 2.35 \u00b7 Tanggal: 2026-10-14", f"Versi: 2.36 \u00b7 Tanggal: {a.today}", 1)
if new == m: print("Tidak ada perubahan (sudah sama)."); sys.exit(0)
shutil.copy(M, str(M) + ".pre-a62.bak"); M.write_text(new, encoding="utf-8"); print("OK: A-62 ditambahkan; versi 2.36")

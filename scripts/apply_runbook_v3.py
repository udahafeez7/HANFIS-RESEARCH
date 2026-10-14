#!/usr/bin/env python3
r"""Runbook D2, revisi 3 (dokumen kerja, bukan artefak beku). Memasukkan temuan pembacaan kode 14 Okt:
 - jalur state resmi rescan = data/evidence/e7_rescan_2026-11-02.json (tag = tanggal D2);
 - tahap yang gagal tidak tercatat selesai di d2_state.json, jadi ulangan rescan cukup `--stage rescan` setelah state dihapus;
 - e7_d2.py memakai tanggal UTC: mulai paling cepat 07.00 WIB;
 - d2_state.json tidak boleh ada sebelum D2; kamus status runner.
Gagal-tertutup: setiap penggantian harus cocok tepat sekali; tidak ada yang ditulis bila satu gagal. Idempoten.
   python scripts/apply_runbook_v3.py [--md protocols/E7_D2_runbook.md]"""
import argparse, shutil, sys
from pathlib import Path
ap = argparse.ArgumentParser(); ap.add_argument("--md", default="protocols/E7_D2_runbook.md"); a = ap.parse_args()
P = Path(a.md); s = P.read_text(encoding="utf-8")
MARK = "## 6. Kamus status runner"
if MARK in s: print("Tidak ada perubahan (sudah diterapkan)."); sys.exit(0)
def rep(txt, old, new):
    if txt.count(old) != 1: sys.exit(f"ABORT, tidak ada yang ditulis: '{old[:70]}...' ditemukan {txt.count(old)}x (harus 1)")
    return txt.replace(old, new, 1)
s = rep(s, "data/evidence/e7_rescan_<tag>.json", "data/evidence/e7_rescan_2026-11-02.json")
s = rep(s, "(3) jalankan `--stage rescan --redo rescan`, yang mulai dari awal dan mengunduh DB Trivy lagi;",
        "(3) jalankan ulang `--stage rescan` (tahap yang gagal tidak tercatat selesai di `d2_state.json`, jadi `--redo` tidak perlu), yang mulai dari awal dan mengunduh DB Trivy lagi;")
s = rep(s, "atau `e7_formula_results_*.json` sebelum D2.",
        "`e7_formula_results_*.json`, atau `d2_state.json` (catatan tahap milik runner; bila ada, tahap yang tercatat dilewati) sebelum D2.")
timenote = ("Catatan waktu: `e7_d2.py` membandingkan tanggal **UTC** dengan D2. Mulai paling cepat **07.00 WIB** pada 2 November (00.00 UTC); sebelum itu `fetch` dan `rescan` ditolak dengan `HOLD_E7_D2_NOT_YET`. "
            "Jangan memakai `--today` untuk menyiasatinya.\n\n")
s = rep(s, "Contoh lengkap satu tahap:", timenote + "Contoh lengkap satu tahap:")
s = s.rstrip("\n") + "\n\n" + MARK + """

Dibaca dari `scripts/e7_d2.py` (14 Okt). Runner berhenti pada kegagalan pertama dan tidak mencatat tahap yang gagal.

| STATUS | Arti | Tindakan |
|---|---|---|
| `HOLD_E7_D2_NOT_YET` | Tanggal UTC hari ini lebih awal dari D2 (hanya `fetch` dan `rescan`) | Tunggu sampai 07.00 WIB |
| `HOLD_E7_PREREG_NOT_VERIFIED` | Verifikasi tag gagal | Berhenti; baca berkas mana yang berbeda; jangan lanjut |
| `HOLD_E7_D2_ORDER` | Tahap menunggu tahap sebelumnya di `d2_state.json` | Jalankan tahap sebelumnya dahulu |
| `HOLD_E7_D2_STAGE_FAILED` | Salah satu perintah tahap gagal | Baca log di `d2_logs/`; perbaiki penyebab teknis; ulangi tahap itu (untuk `rescan`, hapus state dahulu) |
| `HOLD_E7_D2_INSUFFICIENT` | Aturan penjatuhan 2% dilanggar | Berhenti; tidak ada pelonggaran |
| `HOLD_E7_D2_BUILD_GATE` | `build` tidak mencetak `STATUS=TRAINING_AUTHORIZED` | Berhenti; baca keluaran build |
| `HOLD_E7_TOO_FEW_WEEKS` | Kurang dari 6 minggu uji matang pada tabel v3 | Berhenti; D2 cadangan hanya dipilih sebelum model dijalankan |
| `HOLD_E7_ALREADY_RUN`, `HOLD_E7_FORMULA_ALREADY_RUN` | Hasil resmi sudah ada | Tidak diulang |
| `E7_D2_STAGES_DONE` | Tahap yang diminta selesai | Lanjut ke tahap berikutnya |
"""
shutil.copy(P, str(P) + ".pre-v3.bak"); P.write_text(s, encoding="utf-8"); print("OK: runbook revisi 3")

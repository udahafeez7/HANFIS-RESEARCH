#!/usr/bin/env python3
"""Tambah amendemen A-39 (sensitivitas post hoc pra-pergantian EPSS) setelah baris A-38 di
HANFIS_RESEARCH_MEMORY.md, plus peta nomor patch -> hash komit 2026-10-06. Gagal-tertutup:
tepat satu baris '| A-38 |', dan tidak ada '| A-39 |'. Idempoten. Tidak menimpa baris lain."""
import sys, shutil, pathlib
P = pathlib.Path("HANFIS_RESEARCH_MEMORY.md")
lines = P.read_text(encoding="utf-8").split("\n")
text = "\n".join(lines)
if any(l.startswith("| A-39 |") for l in lines):
    print("A-39 sudah ada; tidak ada perubahan."); sys.exit(0)
idx = [i for i, l in enumerate(lines) if l.startswith("| A-38 |")]
if len(idx) != 1: sys.exit(f"ABORT: baris A-38 ditemukan {len(idx)}x (harus 1)")
i = idx[0]
if i + 1 < len(lines) and lines[i + 1].startswith("| A-"): sys.exit("ABORT: ada amendemen setelah A-38")
A39 = ("| A-39 | 2026-10-06 | Eksperimen E4 (sensitivitas) + Naskah §4.5, Limitations | Sensitivitas POST HOC (tidak ada di "
       "praregistrasi E4) terhadap pergantian model EPSS 2026-06-15 (`v2025.03.14` -> `v2026.06.15`): fold 3 (blok uji melintasi) dan "
       "fold 4 (uji pasca-pergantian) pada run penuh terpengaruh. E4bis dijalankan ulang dengan kode, seed, dan konfigurasi beku pada "
       "4.560 aset-minggu berlabel pra-pergantian (<= 2026-05-11; 720 baris uji; `scripts/make_pre_epss_change_table.py`). H1a/H1c/H2 tetap "
       "terkonfirmasi, H1b tetap belum; SS tidak sebanding langsung antar-kolom. Tidak mengubah status konfirmasi. Satu-satunya perubahan "
       "kode sejak tag gerbang E4bis: `--save-models`/meta aditif (komit 6aaec37); grup image 119/119 identik. Hasil: "
       "`results_python/e4bis_120_preEPSS` |")
lines.insert(i + 1, A39)
out = "\n".join(lines)
TAG = "## Peta nomor patch ke komit (2026-10-06)"
if TAG not in out:
    out = out.rstrip("\n") + f"""

{TAG}

Penomoran patch hari ini dapat bentrok dengan nomor lama (mis. komit 6aaec37, 2026-10-02, berlabel patch 0067). Rujukan yang pasti adalah hash komit:

| Label | Komit | Isi |
|---|---|---|
| 0066 | f487116 | naskah: protokol external-v3.0 (Opsi A) |
| 0067 | 01ff91c | testbed: P0-IF 1.2, restore_candidates_csv, first_seen_cache |
| 0068 | 16136fd | naskah: Tabel 1 evidence, bootstrap 10.000 |
| 0069 | 88d6fdd | naskah: sec 3.2 gerbang sebagai prosedur |
| 0070 | 358a6c6 | naskah: pelunakan satu kalimat |
| 0071 | f463caf | uji: sys.path Telemetry (ext4) |
| 0072 | 6a4f29f | naskah: inventaris 120 aset; cek fold vs EPSS |
| 0073 | 6307778 | naskah: buang sisa template backmatter |
| 0074 | 07dc7eb | naskah: sensitivitas pra-pergantian, kalimat basi, hypertexnames |
"""
shutil.copy(P, str(P) + ".pre-a39.bak")
P.write_text(out, encoding="utf-8"); print("OK: A-39 ditambahkan setelah A-38")

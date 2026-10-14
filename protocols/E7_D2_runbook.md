# E7 — Runbook D2 (Senin 2 November 2026)

Dokumen kerja; **bukan** artefak beku dan tidak mengubah protokol. Sumber: `protocols/E7_preregistration_2026-10-12.md`, serta keluaran `e7_d2.py --help` dan `--dry-run` tanggal 2026-10-14. Bila dokumen ini bertentangan dengan protokol, protokol yang berlaku.

Tag: `e7-prereg-2026-10-12` (komit dbed812). D2 = 2026-11-02. Minggu uji: 2026-08-31 sampai 2026-10-05 (6 minggu, minimum 6).

## 0. Prinsip

1. Runner hanya menjalankan skrip beku, berurutan, dan berhenti pada kegagalan pertama. Jangan menghitung apa pun sendiri.
2. Jalankan tahap satu per satu, bukan `--stage all`, agar setiap titik berhenti bisa diperiksa.
3. **Jangan pernah memakai `--today`.** Opsi itu memalsukan tanggal dan melewati penjaga "sebelum D2".
4. `evaluate` dan `formula` hanya jalan **sekali**. Tidak ada `--redo` untuk keduanya.
5. Tidak ada penyetelan, pemilihan ulang, atau analisis tambahan setelah hasil terlihat.
6. Kegagalan teknis (jaringan, disk, daya) boleh diulang dengan `--redo <tahap>` untuk `fetch`, `rescan`, `build`, `predict`; catat setiap pengulangan beserta alasannya.

## 1. Persiapan (jangan menunggu sampai 2 November)

- Jeda Windows Update dari 30 Oktober sampai 3 November (restart paksa dapat mematikan WSL di tengah pemindaian). Atur daya agar tidak tidur; sambungkan listrik.
- Docker Desktop berjalan; `docker info` berhasil; ruang disk lega (terakhir 300 GB bebas).
- Minggu 1 November (sehari sebelumnya): `git status` bersih, `verify_prereg_tag.py` lolos, `python -m pytest -q test tests` lulus (baseline 126 + 11 subtes), `e7_d2.py ... --dry-run` tanpa galat.
- Folder keluaran: tidak boleh ada `forward_predictions_*.csv`, `e7_results_*.json`, atau `e7_formula_results_*.json` sebelum D2.

## 2. Hari-H: urutan

Variabel (selalu ketik, jangan tempel placeholder):

```bash
cd /mnt/c/Research/ANFIS
source /home/hafiz/.venvs/anfis/bin/activate
set +H
D=2026-11-02
T=e7-prereg-2026-10-12
LOG=results_python/e7_d2_logs; mkdir -p $LOG
date          # harus Senin, 2026-11-02
git status --short | grep -v '^??'      # harus kosong
```

Setiap tahap: jalankan, lalu baca `STATUS=` yang tercetak dan `exit=`.

| # | Perintah | Perkiraan | Periksa | Berhenti bila |
|---|---|---|---|---|
| 1 | `python scripts/e7_d2.py --d2 $D --tag $T --stage fetch 2>&1 \| tee $LOG/1_fetch.txt; echo "exit=${PIPESTATUS[0]}"` | menit | `verify` snapshot OK; total 63 minggu tersegel (2025-08-25 sampai 2026-11-02) | STATUS bukan sukses; jumlah minggu tidak 63 |
| 1b | Cek manual versi model EPSS (kolom `epss_model_version` pada keluaran `status` atau manifest snapshot) | 10 mnt | tetap `v2026.06.15` sejak 2026-08-03 | Versi berganti: **berhenti**, baca aturan rezim patah di protokol sebelum melanjutkan |
| 2 | `... --stage rescan` (memakai `--download-db`) | 0,5 sampai 2 jam | selesai tanpa target gagal; komputer tidak tidur | Kegagalan teknis: `--redo rescan`; jangan ganti DB di tengah jalan |
| 3 | `... --stage build` (berjalan dua kali: tabel tanpa penjatuhan, lalu resmi dengan `--drop-insufficient`) | menit | baris dijatuhkan ≤ 2% baris minggu uji (14 dari 720); aset yang kehilangan semua minggu uji keluar dan dilaporkan; cockroachdb diperkirakan keluar | `HOLD_E7_TOO_FEW_WEEKS` atau penjatuhan > 2%: **berhenti**; jangan melonggarkan aturan |
| 4 | `... --stage predict` | menit | lima model (seed 20260928, 20261005, 20261012, 20261019, 20261026); jumlah baris sekitar 720 (sekitar 714 bila cockroachdb keluar) | Galat teknis: `--redo predict` |
| 5 | `... --stage evaluate` | menit | **sekali saja** | Tidak ada pengulangan |
| 6 | `... --stage formula` | menit | **sekali saja** | Tidak ada pengulangan |

Contoh lengkap satu tahap:

```bash
python scripts/e7_d2.py --d2 $D --tag $T --stage rescan 2>&1 | tee $LOG/2_rescan.txt; echo "exit=${PIPESTATUS[0]}"
```

Bila minggu matang kurang dari enam (`HOLD_E7_TOO_FEW_WEEKS`), D2 cadangan Senin 2026-11-09 hanya boleh dipilih **sebelum** model dijalankan, dan tidak untuk mengulang kegagalan.

## 3. Segera setelah `evaluate` dan `formula`

1. Salin keluaran (CSV prediksi, kedua JSON hasil, seluruh log) ke cadangan kedua di luar repositori; catat sha256.
2. Jalankan `fill_e7_results.py` untuk tabel LaTeX (ia memberi tanda jelas bila hasil bukan latihan).
3. Komit hasil dan log; buat tag `e7-results-2026-11-02`; dorong ke GitHub.
4. Amendemen baru di memori repositori (ringkasan status tiap hipotesis, jumlah baris, daftar aset yang keluar, setiap `--redo`).
5. Versi baru Zenodo (v2.0) memuat hasil; sitasi DOI versi yang baru.

## 4. Aturan pelaporan (sudah terdaftar)

- Keluarga 1 {P7a, P7b} dan keluarga 2 {P7e, P7f}, masing-masing dengan Holm pada alfa satu sisi 0,025 (ambang 0,0125 dan 0,025), SESOI 0,05, bootstrap per image 2.000 resampel, seed 20261102.
- P7e dan P7f berasal dari analisis post hoc: nyatakan demikian.
- Bila P7e tidak terkonfirmasi, tulis "tidak dibuktikan", bukan "tidak berbeda".
- Laporkan sensitivitas bootstrap per minggu (aturan "rapuh").

## 5. Dilarang sebelum dan sesudah D2

- Menjalankan tahap apa pun sebelum 2 November (kecuali `--dry-run`).
- `--today`; mengubah salah satu dari 23 artefak beku; mengunduh snapshot EPSS/KEV lewat jalur lain.
- Mengulang `evaluate` atau `formula`; memilih ulang tanggal D2 setelah model berjalan.
- Mengubah ambang, SESOI, atau daftar hipotesis setelah melihat hasil.

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
- Docker Desktop berjalan; `docker info` berhasil; ruang disk lega (14 Okt: 631 GB bebas dari 930 GB).
- Minggu 1 November (sehari sebelumnya): `git status` bersih, `verify_prereg_tag.py` lolos, `python -m pytest -q test tests` lulus (baseline 126 + 11 subtes), `e7_d2.py ... --dry-run` tanpa galat.
- Folder keluaran: tidak boleh ada `forward_predictions_*.csv`, `e7_results_*.json`, `e7_formula_results_*.json`, atau `d2_state.json` (catatan tahap milik runner; bila ada, tahap yang tercatat dilewati) sebelum D2.

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
| 2 | `... --stage rescan` (memakai `--download-db`) | 0,5 sampai 2 jam | selesai tanpa target gagal; komputer tidak tidur | Kegagalan teknis: lihat catatan ulangan di bawah tabel (state dihapus dulu) |
| 3 | `... --stage build` (berjalan dua kali: tabel tanpa penjatuhan, lalu resmi dengan `--drop-insufficient`) | menit | baris dijatuhkan ≤ 2% baris minggu uji (14 dari 720); aset yang kehilangan semua minggu uji keluar dan dilaporkan; cockroachdb diperkirakan keluar | `HOLD_E7_TOO_FEW_WEEKS` atau penjatuhan > 2%: **berhenti**; jangan melonggarkan aturan |
| 4 | `... --stage predict` | menit | lima model (seed 20260928, 20261005, 20261012, 20261019, 20261026); jumlah baris sekitar 720 (sekitar 714 bila cockroachdb keluar) | Galat teknis: `--redo predict` |
| 5 | `... --stage evaluate` | menit | **sekali saja** | Tidak ada pengulangan |
| 6 | `... --stage formula` | menit | **sekali saja** | Tidak ada pengulangan |

Catatan tahap 2: `rescan` **menulis** `configs/assets_v3.csv` dan manifesnya (berkas ini sengaja belum ada sebelum D2, sesuai protokol). Sesudahnya berkas harus ada dan jumlah barisnya (sekitar 121 dengan header, sama dengan `configs/assets.csv`) dicocokkan; selisih dijelaskan sebelum menjalankan `build`.

Catatan ulangan `rescan` (dibaca dari kode pada 14 Okt; belum diuji): `e7_d2.py --redo` hanya menghapus catatan tahap di runner dan tidak meneruskan `--resume` ke `e7_rescan.py`. Bila rescan berhenti di tengah dan `data/evidence/e7_rescan_2026-11-02.json` sudah ada, ulangan langsung ditolak ("sudah ada"). Prosedur: (1) baca pesan dan perbaiki penyebabnya (disk, Docker, jaringan); (2) hapus berkas state itu dengan sengaja; (3) jalankan ulang `--stage rescan` (tahap yang gagal tidak tercatat selesai di `d2_state.json`, jadi `--redo` tidak perlu), yang mulai dari awal dan mengunduh DB Trivy lagi; (4) catat ulangan dan kedua tanggal DB di log D2 dan di amendemen. Jangan menjalankan `e7_rescan.py --resume` langsung: runner tidak akan menganggap tahap itu selesai. Selama rescan berjalan, jangan menjalankan Trivy lain atau `docker system prune`: skrip berhenti bila DB berubah di tengah pemindaian atau ID image tidak cocok.

Catatan waktu: `e7_d2.py` membandingkan tanggal **UTC** dengan D2. Mulai paling cepat **07.00 WIB** pada 2 November (00.00 UTC); sebelum itu `fetch` dan `rescan` ditolak dengan `HOLD_E7_D2_NOT_YET`. Jangan memakai `--today` untuk menyiasatinya.

**Rev 4 (A-71): mulai tahap 1 sekitar 20.00 WIB (13.00 UTC), bukan 07.00 WIB.** Alasan: berkas EPSS bertanggal 2026-11-02 dibuat sekitar 12.00 UTC (stempel `score_date` pada delapan berkas tersegel 2026-08-03 sampai 2026-09-21 berkisar 12:00:16Z sampai 12:03:47Z), jadi pada 00.00 UTC kemungkinan besar belum ada dan `fetch` gagal. Penjaga hanya memeriksa batas bawah tanggal UTC (`scripts/e7_d2.py` baris 85; tidak ada batas atas), sehingga tahap yang melewati 07.00 WIB 3 November tidak terhenti; kesegaran DB Trivy dihitung terhadap D2 plus minus satu hari (`scripts/e7_rescan.py` baris 107 sampai 110), bukan terhadap jam. Sebelum tahap 1, ketersediaan berkas boleh diperiksa dengan permintaan header saja (`curl -sI https://epss.cyentia.com/epss_scores-2026-11-02.csv.gz | head -1`; hanya kode HTTP, tanpa mengunduh isi): 200 berarti ada, 404 berarti tunggu lalu cek lagi. Bila server tidak menjawab permintaan header, langsung jalankan tahap 1: berkas yang belum ada menggagalkan tahap tanpa mencatatnya, dan `--redo fetch` (butir 6 prinsip) hanya mengambil berkas yang belum tersegel; catat pengulangan itu beserta alasannya. Perkiraan jadwal: tahap 1 dan 1b sekitar setengah jam, rescan 0,5 sampai 2 jam, tahap 3 sampai 6 sekitar satu jam; selesai sekitar tengah malam WIB; cadangan keluaran (bagian 3) malam itu juga ke C:, WSL, dan D:. Bukti waktu terbit bersifat tidak langsung (stempel dalam berkas, bukan pengamatan server); jam 20.00 dipilih sebagai margin.

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

## 6. Kamus status runner

Dibaca dari `scripts/e7_d2.py` (14 Okt). Runner berhenti pada kegagalan pertama dan tidak mencatat tahap yang gagal.

| STATUS | Arti | Tindakan |
|---|---|---|
| `HOLD_E7_D2_NOT_YET` | Tanggal UTC hari ini lebih awal dari D2 (hanya `fetch` dan `rescan`) | Tunggu sampai 07.00 WIB (batas terendah; mulai praktis sekitar 20.00 WIB, lihat catatan waktu rev 4) |
| `HOLD_E7_PREREG_NOT_VERIFIED` | Verifikasi tag gagal | Berhenti; baca berkas mana yang berbeda; jangan lanjut |
| `HOLD_E7_D2_ORDER` | Tahap menunggu tahap sebelumnya di `d2_state.json` | Jalankan tahap sebelumnya dahulu |
| `HOLD_E7_D2_STAGE_FAILED` | Salah satu perintah tahap gagal | Baca log di `d2_logs/`; perbaiki penyebab teknis; ulangi tahap itu (untuk `rescan`, hapus state dahulu) |
| `HOLD_E7_D2_INSUFFICIENT` | Aturan penjatuhan 2% dilanggar | Berhenti; tidak ada pelonggaran |
| `HOLD_E7_D2_BUILD_GATE` | `build` tidak mencetak `STATUS=TRAINING_AUTHORIZED` | Berhenti; baca keluaran build |
| `HOLD_E7_TOO_FEW_WEEKS` | Kurang dari 6 minggu uji matang pada tabel v3 | Berhenti; D2 cadangan hanya dipilih sebelum model dijalankan |
| `HOLD_E7_ALREADY_RUN`, `HOLD_E7_FORMULA_ALREADY_RUN` | Hasil resmi sudah ada | Tidak diulang |
| `E7_D2_STAGES_DONE` | Tahap yang diminta selesai | Lanjut ke tahap berikutnya |

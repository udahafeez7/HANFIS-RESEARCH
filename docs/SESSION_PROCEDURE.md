# Prosedur Sesi Kerja HANFIS

> Dibaca dan dijalankan pada awal **setiap** sesi. Semua perintah siap tempel.
> Semua jalur ditulis lengkap. Versi 1.0 · 22 September 2026.

## 0. Peta direktori (hafalkan ini)

| Isi | Jalur lengkap (WSL) | Jalur Windows |
|---|---|---|
| Repositori penelitian | `/mnt/c/Research/ANFIS` | `C:\Research\ANFIS` |
| Virtual environment | `~/venv/anfis` (atau lihat langkah 1) | — |
| Kode model | `/mnt/c/Research/ANFIS/python_hanfis/` | `C:\Research\ANFIS\python_hanfis\` |
| Skrip data | `/mnt/c/Research/ANFIS/scripts/` | `C:\Research\ANFIS\scripts\` |
| Skrip telemetri | `/mnt/c/Research/ANFIS/telemetry/` | `C:\Research\ANFIS\telemetry\` |
| Runner eksperimen | `/mnt/c/Research/ANFIS/experiments/` | `C:\Research\ANFIS\experiments\` |
| Pengujian | `/mnt/c/Research/ANFIS/test/` dan `/mnt/c/Research/ANFIS/tests/` | — |
| **Hasil eksperimen** | `/mnt/c/Research/ANFIS/results_python/<nama>/` | `C:\Research\ANFIS\results_python\<nama>\` |
| Bukti telemetri v3 | `/mnt/c/Research/ANFIS/Jetson Orin/Telemetry/RunsV3/` | — |
| Bukti telemetri v4 | `/mnt/c/Research/ANFIS/Jetson Orin/Telemetry/RunsV4/` | — |
| Protokol telemetri | `/mnt/c/Research/ANFIS/Jetson Orin/Telemetry/hanfis_protocol_v3/` | — |
| Referensi dan arsip hasil | `/mnt/c/Research/ANFIS/reference/eint_results/` | — |
| Potongan naskah | `/mnt/c/Research/ANFIS/manuscript/` | — |
| Memori proyek | `/mnt/c/Research/ANFIS/HANFIS_RESEARCH_MEMORY.md` | — |
| **Folder patch (unduhan dari chat)** | `/mnt/c/Research/ANFIS/Patch/` | `C:\Research\ANFIS\Patch\` |
| Patch terbuka (sementara) | `/tmp/pNNNN/` | — |

## 1. Buka sesi (selalu empat langkah ini)

```bash
# 1a. Masuk repositori (perhatikan garis miring di depan: /mnt, bukan mnt)
cd /mnt/c/Research/ANFIS

# 1b. Aktifkan virtual environment
source ~/venv/anfis/bin/activate
#     Jika gagal, cari lokasinya lebih dulu:
#     ls -d ~/venv/anfis ~/.venvs/anfis /mnt/c/Research/ANFIS/venv /mnt/c/Research/ANFIS/.venv 2>/dev/null

# 1c. Periksa keadaan awal
pwd && which python && python -c "import torch, pandas, numpy; print('torch', torch.__version__)"
git status -sb && git log --oneline -3

# 1d. Baca keputusan yang sudah dibekukan
sed -n '1,60p' /mnt/c/Research/ANFIS/HANFIS_RESEARCH_MEMORY.md
```

Diharapkan: prompt `(anfis) ... :/mnt/c/Research/ANFIS$`, cabang `research/amend-a02-a06`, pohon kerja bersih.

## 2. Menerapkan patch dari chat

Simpan zip dari chat langsung ke `C:\Research\ANFIS\Patch\` (tidak perlu disalin lagi), lalu:

```bash
cd /mnt/c/Research/ANFIS
ls -la /mnt/c/Research/ANFIS/Patch/
sha256sum /mnt/c/Research/ANFIS/Patch/HANFIS_patch_NNNN_*.zip
grep NNNN /mnt/c/Research/ANFIS/HANFIS_patches_SHA256SUMS.txt
unzip -o /mnt/c/Research/ANFIS/Patch/HANFIS_patch_NNNN_*.zip -d /tmp/pNNNN
git am -3 /tmp/pNNNN/*.patch
python -m pytest -q test tests
```

Atau cukup satu perintah (mencari zip terbaru di folder Patch, memverifikasi checksum bila
tercantum, membuka, dan menerapkannya):

```bash
cd /mnt/c/Research/ANFIS && ./scripts/apply_latest_patch.sh
```

Bila `git am` berhenti: `git am --abort` mengembalikan keadaan semula, lalu laporkan pesannya.

## 3. Menjalankan eksperimen (semua hasil ke results_python/)

```bash
cd /mnt/c/Research/ANFIS

# E-INT: jumlah MF panel Integrasi
python experiments/exp_integration_mf.py --output results_python/eint_p3 --seeds 5

# E1: ablasi keluarga MF x konstrain monotonik
python experiments/exp_e1_ablation.py --output results_python/e1_v2 --seeds 5

# Telemetri: konsolidasi dan analisis berpasangan
python telemetry/tidy_pairs.py \
  --root "/mnt/c/Research/ANFIS/Jetson Orin/Telemetry/RunsV3" \
  --root "/mnt/c/Research/ANFIS/Jetson Orin/Telemetry/RunsV4" \
  --output results_python/telemetry/tidy_all_v3.csv
python telemetry/analyze_pairs.py \
  --tidy results_python/telemetry/tidy_all_v3.csv \
  --output results_python/telemetry/paired_effects_v3.csv
```

## 4. Mengirim hasil kembali ke chat

Berkas yang diminta selalu berada di `/mnt/c/Research/ANFIS/results_python/...`.
Di Windows, buka `C:\Research\ANFIS\results_python\` lalu seret berkas CSV ke jendela chat.
Untuk melihat daftarnya lebih dulu:

```bash
ls -la /mnt/c/Research/ANFIS/results_python/*/
```

## 5. Menutup sesi

```bash
cd /mnt/c/Research/ANFIS
python -m pytest -q test tests
git status -sb
git add -A && git commit -m "<pesan>"        # bila ada perubahan milik Anda sendiri
git push origin research/amend-a02-a06 --tags
git bundle create /mnt/c/Research/ANFIS/hanfis-$(date +%Y%m%d).bundle --all
sha256sum /mnt/c/Research/ANFIS/hanfis-$(date +%Y%m%d).bundle
```

Perbarui `HANFIS_RESEARCH_MEMORY.md` bila ada amendemen (A-xx) atau blocker yang ditutup (F-xx),
lalu commit dengan pesan `memory: A-xx ...` atau `memory: close F-x ...`.

## 6. Tiga angka wajib di setiap laporan harian

1. jumlah baris `event_id` (aset-minggu)
2. proporsi label non-NA / positif
3. status `TRAINING_AUTHORIZED`

## 7. Kesalahan yang paling sering terjadi

| Gejala | Sebab | Perbaikan |
|---|---|---|
| `cd: mnt/c/...: No such file or directory` | garis miring depan hilang | `cd /mnt/c/Research/ANFIS` |
| `No module named python_hanfis` | `pytest` dipanggil langsung | `python -m pytest -q test tests` |
| `sha256sum: FAILED open or read` | dijalankan dari direktori lain | `cd` ke folder tempat berkas berada lebih dulu |
| `already exists in working directory` saat `git am` | penggantian nama huruf besar-kecil di NTFS | `git mv A a_tmp && git mv a_tmp a` |
| `fatal: a branch named ... already exists` | cabang sudah dibuat | `git checkout research/amend-a02-a06` (tanpa `-b`) |
| `python: can't open file 'experiments/...'` | patch belum diterapkan | ulangi langkah 2 |

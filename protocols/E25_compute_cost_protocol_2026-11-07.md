# Protokol E25: pengukuran biaya komputasi (deskriptif, tidak terdaftar)

Ditulis dan dikomit 7 November 2026, SEBELUM pengukuran nyata. Lapisan (pagar P1): pipeline data dan prosedur mutu. Dokumen: berkas ini, `scripts/e25_compute_cost.py`. Tidak ada berkas beku E4 atau E7 yang diubah.

## 1. Status dan alasan

- Eksperimen ini TIDAK terdaftar di OSF dan TIDAK berstatus konfirmatori. Hasilnya deskriptif dan tidak mengubah satu pun keputusan terdaftar (H1a, H1b, H1c, H2/H3, P7a sampai P7f).
- Dilakukan setelah hasil E7 diketahui (2 November 2026). Pengukuran ini tidak memakai label, prediksi, atau hasil E7, dan tidak dapat memengaruhinya.
- Alasan: C2 di naskah dan definisi H2 menjanjikan pengukuran waktu latih, memori puncak, latensi inferensi, dan throughput. Pengukuran itu tidak pernah dilakukan; yang ada hanya jumlah aturan dan parameter (Tabel 1) dan waktu dinding per fold untuk semua model sekaligus. Celah ini ditemukan pada 7 November 2026 lewat pembacaan paper pembanding, bukan dari hasil apa pun.
- Bila hasilnya tidak menguntungkan HANFIS, hasil itu dilaporkan apa adanya.

## 2. Subjek

Tiga prosedur pelatihan beku dari E4-bis, tanpa perubahan kode (`python_hanfis/hanfis_end2end.py`, `flat_anfis_matched.py`, `hanfis_models.py`, `scripts/e4_run.py`):

| Kode | Model | Prosedur (seperti `scripts/e4_run.py`) |
|---|---|---|
| `hanfis` | HANFIS (34 aturan, 176 parameter) | terbaik dari 3 restart, `fit_hybrid_lower_alternating`, Gaussian, monotonik, `m_raw=2`, `m_intermediate=3`, 600 epoch, patience 100, minimum 200 epoch |
| `matched` | FlatANFISMatched (parameter sama, selisih paling banyak 5%) | `build_matched` (pencarian radius klaster pada data latih fold) lalu `fit_hybrid`, 600 epoch, patience 100, minimum 200 epoch |
| `flat_full` | Flat ANFIS penuh (128 aturan, 1.052 parameter) | `SugenoANFIS(n_inputs=7, n_mfs=2)`, `fit_anfis`, 600 epoch, patience 60 |

Data: `data/processed/asset_weeks_v2_120assets_e4bis.csv` (inventaris 120 aset), 5 fold GroupTimeSplit (embargo 30 hari), pembagian validasi 15% dengan `rng(20260928 + indeks fold)` seperti E4. Seed: hanya seed beku pertama, 20260928 (bukan kelima seed), karena yang diukur adalah biaya satu prosedur latih, bukan galat prediksi.

## 3. Metrik dan cara ukur

Satu unit = satu (model, fold, ulangan). Tiap unit dijalankan di subproses baru, torch dibatasi 1 thread, hanya CPU. Setiap subproses lebih dulu menjalankan satu lintasan pemanasan dengan kode yang sama (3 epoch, hasilnya dibuang) agar pemuatan pustaka dan halaman kode sudah ada di memori.

1. Waktu latih: `perf_counter` seputar seluruh prosedur pelatihan model (termasuk 3 restart HANFIS dan pencarian radius matched), detik.
2. Kenaikan memori puncak: setelah pemanasan, penanda puncak resident set proses direset (`/proc/self/clear_refs`, nilai 5), lalu selisih VmHWM sesudah pelatihan terhadap VmHWM sebelum pelatihan, MiB. Resolusi sekitar 1 MiB dan bersifat tingkat proses.
3. Latensi inferensi: `predict` yang sama dengan pipeline, satu baris per panggilan, 200 panggilan pemanasan lalu 2.000 panggilan; median dan persentil ke-95, mikrodetik. Termasuk biaya konversi numpy ke torch di dalam `predict`.
4. Throughput: `predict` pada seluruh baris uji fold, 20 panggilan, median, baris per detik.
5. Jumlah aturan dan parameter dari model terlatih.

Ulangan: 3 per (model, fold), jadi 5 fold x 3 model x 3 ulangan = 45 unit. Urutan: ulangan, lalu fold, lalu model (`hanfis`, `matched`, `flat_full`).

## 4. Pelaporan

- Untuk tiap model dan metrik: median, minimum, maksimum atas 15 pengukuran (5 fold x 3 ulangan), dan median per fold.
- Rasio median HANFIS terhadap flat penuh dan terhadap FlatANFISMatched.
- Tanpa uji hipotesis, tanpa selang kepercayaan, tanpa nilai p.
- Pembacaan deskriptif, ditetapkan sebelum pengukuran: untuk setiap metrik, "didukung secara deskriptif" bila median HANFIS lebih rendah daripada median flat penuh pada kelima fold (median atas ulangan per fold); "tidak didukung" bila lebih tinggi pada sekurang-kurangnya tiga fold; selain itu "campuran". Untuk throughput arah dibalik (lebih tinggi = lebih baik). Terhadap FlatANFISMatched hasil hanya dilaporkan, karena parameternya dipasangkan secara desain.

## 5. Larangan dan penanganan kegagalan

- Kode beku, epoch, patience, seed, dan jumlah restart tidak diubah. Tidak ada penyetelan.
- Pengukuran nyata dijalankan sekali (`--run`). Hanya kegagalan teknis (galat proses, disk, daya) yang boleh diulang, dan setiap pengulangan dicatat beserta alasannya. Pengulangan karena hasil tidak diinginkan dilarang.
- Satu uji fungsi (`--smoke`: 1 fold, 1 ulangan, 3 epoch) boleh dijalankan sebelum pengukuran nyata; keluarannya dibuang dan tidak dipakai. Uji fungsi pada 7 November memperbaiki dua cacat alat ukur memori (pemuatan pustaka tercatat sebagai memori model); perbaikan itu sudah ada di skrip yang dikomit bersama protokol ini.

## 6. Batas klaim

- Mini PC (AMD Ryzen 7 255, 16 inti logis) di WSL 2; Docker, Kubernetes, dan Prometheus dapat berjalan bersamaan. Nilai mutlak tidak berlaku untuk mesin lain.
- Bukan pengukuran edge dan bukan pengukuran produksi; tidak ada klaim tentang Jetson atau perangkat edge (pagar P11).
- Latensi satu model kecil di tingkat mikrodetik tidak otomatis bermakna praktis.
- Di naskah hasil ini ditulis sebagai pengukuran tidak terdaftar dan deskriptif.

## 7. Keluaran

`results_python/e25/raw_<stempel>.csv`, `summary_<stempel>.json`, `env_<stempel>.json` (versi Python dan torch, CPU, komit git). Berkas diabaikan git; yang dikomit hanya hash dan ringkasan di amendemen memori.

---
Dokumen ini disusun dengan bantuan asisten AI (Claude, Anthropic) atas permintaan peneliti pada 7 November 2026.

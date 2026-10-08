# Praregistrasi E7 — Evaluasi prospektif dan metrik utilitas (DRAFT dengan keputusan desain; belum dibekukan)

> **STATUS: DRAFT.** Keputusan desain di bawah ditetapkan 2026-10-08 **atas delegasi peneliti** ("lanjutkan sampai selesai untuk keputusan E7") dan dapat diubah **sebelum**
> pembekuan, tidak sesudahnya. Nomor amendemen: A-44. Isi E7 diinferensikan dari memori (§3 "metrik utilitas"), Parthiban-Krishna, dan analisis eksploratori A-41;
> peneliti harus memastikan ini memang E7. Pembekuan = komit + tag + `scripts/verify_prereg_tag.py` LOLOS (pelajaran E6: tag yang dibuat sebelum komit tidak membekukan apa pun).

## Mengapa desainnya prospektif

A-41 menghasilkan hipotesis pada data yang **sudah terlihat**, sehingga menguji ulang di data yang sama tidak konfirmatori. Jalan yang jujur: menguji pada minggu yang labelnya belum
pernah dihitung. Data berakhir pada snapshot 2026-09-21, sehingga label minggu 2026-08-31 dan setelahnya belum ada.

## Keputusan desain (2026-10-08, atas delegasi)

| Butir | Keputusan | Alasan singkat |
|---|---|---|
| D2 (tanggal tarik data dan pembekuan DB Trivy) | **2026-11-09** | memberi **7** minggu forward matang (t = 2026-08-31, 09-07, 09-14, 09-21, 09-28, 10-05, 10-12; syarat t + 28 hari <= D2); 2026-11-02 hanya 6 (tanpa cadangan bila satu minggu dikecualikan); 2026-11-16 menabrak M6 |
| Minimum minggu analisis | **6**; kurang dari itu E7 ditunda, tidak dilonggarkan | D2 memberi 7, cadangan satu minggu |
| Bentuk hibrida | **satu parameter lambda**: `y_hat = lambda * y_hat_HANFIS + (1 - lambda) * y_lag4`, skala 0-100 | gerbang berbasis perubahan masukan adalah desain yang dipilih setelah melihat A-41 (derajat kebebasan peneliti); lambda tunggal murah, dapat dilaporkan, dan sulit disalahgunakan |
| Sumber lambda | kuadrat terkecil **pada prediksi out-of-fold E4** (label <= 2026-08-24), dijepit ke [0,1], lewat `scripts/e7_fit_lambda.py`; dibekukan sekali di `protocols/E7_lambda_<tanggal>.json` | prediksi dalam sampel model akhir terlalu optimis dan membiaskan lambda ke HANFIS |
| Model akhir | dilatih ulang pada **semua** minggu berlabel <= 2026-08-24, konfigurasi A-09 + A-10, lima seed yang sama; hash berkas dicatat sebelum tag | cek gerbang >= 10 observasi per parameter (sekitar 39) |
| P7c primer | **non-inferioritas** hibrida terhadap persistence pada presisi@20%: batas bawah CI95 selisih > **-0,05** | peringkat persistence sudah sangat kuat; yang diuji adalah bahwa hibrida tidak merusaknya |

## Hipotesis yang dinyatakan sebelum data (dari A-41)

| ID | Pernyataan | Kriteria |
|---|---|---|
| P7a | **Prediksi rezim.** Pada minggu forward tanpa pergantian versi model EPSS, HANFIS **tidak** lebih baik dari persistence. | SS terhadap persistence: batas atas CI95 < 0,05 (SESOI E4). Hasil sebaliknya (SS >= 0,05 dengan batas bawah > 0) membantah hipotesis rezim. |
| P7b | **Hibrida.** Campuran persistence dan HANFIS mengalahkan persistence. | SS_hibrida terhadap persistence >= 0,05 dan batas bawah CI95 > 0, dengan lambda dari `E7_lambda_<tanggal>.json`. |
| P7c | **Utilitas (peringkat).** Presisi@20% per minggu (irisan 20% teratas menurut label dan menurut prediksi) dan Spearman. | primer: lihat tabel keputusan; Spearman dan pembanding ridge-7 dilaporkan dengan CI tanpa koreksi (sekunder). |

Analisis: MSE terkumpul pada skala mentah, bootstrap berkelompok per image (2.000), koreksi Holm pada keluarga {P7a, P7b}.

**Dilaporkan tanpa kriteria (tidak masuk keputusan):** SS terhadap persistence per strata perubahan masukan yang **tersedia pada waktu t** (selisih x2 atau status KEV
selama 4 minggu = 0 vs > 0), untuk menguji mekanisme "HANFIS reaktif" secara prospektif; lambda per fold dan pada skala log1p; hasil dengan dan tanpa wordpress.

## Urutan kerja (setiap langkah sebelum tag TIDAK menyentuh label forward)

| Jendela | Langkah |
|---|---|
| sekarang - 2026-10-11 | jalankan `e7_fit_lambda.py` pada prediksi E4 (lambda, CI, per fold); keputusan ini tercatat di A-44 |
| 2026-10-12 - 10-25 (M3) | tulis `scripts/e7_train_final.py` dan perluasan pipeline untuk minggu > 2026-09-21; latih model akhir lima seed; hash model |
| paling lambat 2026-10-31 (gerbang 1 November) | komit protokol bertanggal, skrip, `E7_lambda_*.json`, hash model; **tag `e7-prereg-<tanggal>`**; `python scripts/verify_prereg_tag.py <tag> <berkas...>` harus **LOLOS** |
| setelah tag | tarik dan segel snapshot EPSS/KEV 2026-09-28 .. 2026-11-09 dengan manifest; catat versi model EPSS tiap minggu |
| 2026-11-09 (D2) | unduh DB Trivy sekali, bekukan (`--skip-db-update`), pindai ulang 120 image, bangun dataset versi 3 (checksum), hitung label minggu 2026-08-31 .. 2026-10-12 |
| 2026-11-10 .. 11-15 (M5) | jalankan E7 **satu kali**; `--run` menolak berjalan bila `verify_prereg_tag.py` gagal; laporan |

## Prasyarat yang HARUS ada sebelum pembekuan

1. **Pindai ulang** pada D2 dengan DB dibekukan (A-15: satu pindaian hanya memuat CVE yang diketahui saat itu). Dataset versi 3 dengan checksum.
2. **Minggu uji** hanya `t` dengan `t + 28 hari <= D2`; minggu tanpa snapshot lengkap dikecualikan dan dihitung.
3. **Model dibekukan** (hash) sebelum label forward dihitung.
4. **Persistence** memakai label versi 3 untuk minggu `t - 4` agar konsisten.
5. **Versi model EPSS** pada minggu forward dicatat; bila ada pergantian baru, minggu itu dipisah sebagai rezim patahan.
6. **Pemeriksa tag**: `scripts/verify_prereg_tag.py` lolos untuk protokol, skrip, lambda, dan hash model.

## Risiko yang dinyatakan

Snapshot yang tidak terkumpul sejak 2026-09-21 diambil dari arsip publik dan disegel sebelum label dihitung; celah = minggu dikecualikan. Daya terbatas: 7 minggu x 120 image,
deret tiap image berkorelasi, sehingga CI lebar; hasil tidak signifikan dilaporkan sebagai tidak terbukti, bukan sebagai kesetaraan. Lambda dipasang pada model validasi silang
dan diterapkan pada model akhir yang dilatih pada data lebih banyak: ketidakcocokan ini dinyatakan, bukan disetel.

## Tidak akan dilakukan

Menghitung label atau menarik snapshot minggu >= 2026-08-31 sebelum tag; melatih ulang setelah melihat label forward; menyesuaikan lambda, D2, atau ambang setelah hasil terlihat;
memilih minggu; menambah pembanding; mengubah definisi hibrida.

## Sumber

`HANFIS_RESEARCH_MEMORY.md` (A-09, A-10, A-13, A-15, A-34, A-41, A-43); `results_python/e4_regime*`, `e4_influence*`, `e6`.

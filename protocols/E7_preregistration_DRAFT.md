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

## Nilai lambda (dihitung 2026-10-08)

- lambda = 0,5109; CI95 bootstrap berkelompok [0,260; 0,778] (119 kelompok image, 1.080 baris); sensitivitas log1p 0,5053. Berkas: `protocols/E7_lambda_2026-10-08.json` (hash masukan di dalamnya). Tidak akan disetel ulang.
- Per fold: 0,013 / 0,266 / 0,454 / 1,0 / 0,614 (heterogen); satu lambda adalah kompromi antar rezim.
- MSE out-of-fold dalam sampel: HANFIS 0,4087; persistence 0,4147; hibrida 0,3425 (SS dalam sampel 0,174; optimis karena lambda dipasang pada baris yang sama; bukan hasil E7).
- P7a dan P7b dapat sama-sama benar bila galat HANFIS dan persistence tidak sepenuhnya berkorelasi; P7b tidak otomatis gugur bila P7a terbukti.

## Keputusan D2 (2026-10-08, menggantikan baris D2 pada tabel keputusan di atas)

- **D2 primer = 2026-11-02**: 6 minggu forward matang (t = 2026-08-31, 09-07, 09-14, 09-21, 09-28, 10-05), tepat di minimum.
- **Cadangan = 2026-11-09 (7 minggu)**, hanya bila saat dataset versi 3 dibangun jumlah minggu matang < 6 (snapshot hilang, pergantian versi model EPSS), diputuskan **sebelum model apa pun dijalankan pada data forward**. Tidak ada pilihan D2 setelah melihat hasil.
- Alasan: percepatan satu minggu; risiko ketiadaan cadangan dibatasi oleh aturan cadangan ini.

## Amendemen A-46 (2026-10-08): metrik utilitas dan keterbatasan daya, setelah latihan kode

Latihan kode `e7_evaluate.py --rehearsal` pada 1.080 baris out-of-fold E4 (**bukan data E7**; lambda dipasang pada baris yang sama) memberi tiga pelajaran, dicatat sebelum pembekuan:

1. **Efek langit-langit pada P7c (level).** Persistence mencapai presisi@20% = 0,969 karena perbedaan antar-asset yang stabil mendominasi label; hibrida 0,889 (selisih -0,080, CI95 [-0,299; -0,020]).
   Margin non-inferioritas -0,05 hampir pasti gagal di E7 bukan karena kualitas hibrida, tetapi karena metrik level tidak mengukur kontribusi dinamis. **P7c (level) diturunkan menjadi deskriptif.**
2. **P7d (utilitas, menggantikan P7c sebagai kriteria utilitas): informasi tambahan di atas persistence.** Rerata mingguan korelasi Spearman antara perubahan prediksi (`y_hanfis - y_lag4`)
   dan perubahan nyata (`y_true - y_lag4`), minggu dengan >= 5 asset. Kriteria: batas bawah CI95 bootstrap berkelompok per image > 0. Sekunder, tanpa koreksi multiplisitas. Hibrida memiliki Spearman perubahan
   identik dengan HANFIS (lambda > 0), sehingga tidak dilaporkan terpisah; ridge-7 dilaporkan sebagai pembanding.
3. **Daya terbatas.** Pada OOF, SS_hibrida = 0,174 dengan CI95 [0,011; 0,236] dan p Holm 0,021 (> ambang 0,0125): P7b gagal pada ambang Holm walaupun batas bawah CI > 0; P7a CI95 [-0,642; 0,241].
   Data forward lebih sedikit (6 minggu x sekitar 120 image). **Aturan keputusan P7a dan P7b tidak diubah karena rehearsal** (Holm dipertahankan). E7 dilaporkan sebagai estimasi prospektif dengan CI;
   hasil "tidak terbukti" bukan bukti kesetaraan.

Perubahan nomor 1 dan 2 didasarkan pada data E4, bukan data forward; data forward belum disentuh.

## Amendemen A-47 (2026-10-08): batas data latih model akhir (koreksi kebocoran temporal)

Draf dan A-44 menyatakan model akhir dilatih pada semua minggu berlabel <= 2026-08-24. **Itu salah.** Label minggu 2026-08-24 memakai EPSS/KEV sampai 2026-09-21, sehingga jendela label baris latih
menumpuk dengan waktu fitur minggu forward 2026-08-31 .. 2026-09-21 dan dengan jendela label forward. Prosedur E4 (`GroupTimeSplit`, `python_hanfis/splits.py`) menerapkan embargo 30 hari:
latih hanya baris dengan `week_start_utc <= minggu uji pertama - 30 hari`.

Untuk E7: minggu forward pertama 2026-08-31, sehingga cutoff = 2026-08-01 dan **model akhir dilatih pada minggu berlabel <= 2026-07-27** (jendela label terakhirnya berakhir 2026-08-24, sebelum
2026-08-31). `scripts/e7_pipeline.py train` menegakkan aturan ini dan menolak embargo < 28 hari; `predict` menolak minggu sebelum minggu forward pertama model dan memverifikasi hash model terhadap manifest.
Gerbang kecukupan data (>= 10 observasi per parameter, 176 parameter) dihitung ulang oleh skrip. Validasi: 15% baris latih acak dengan seed tetap 20260933; konfigurasi pelatihan identik dengan E4.
Koreksi dibuat **sebelum** pembekuan dan tanpa menyentuh label forward. Lambda (dari prediksi out-of-fold E4, yang sudah memakai embargo) tidak terpengaruh. Semua teks lain yang menyebut 2026-08-24
sebagai batas latih (A-44, draf pendaftaran OSF) digantikan oleh amendemen ini.

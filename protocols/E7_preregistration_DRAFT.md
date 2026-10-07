# Praregistrasi E7 — Evaluasi prospektif dan metrik utilitas (KERANGKA, belum lengkap)

> **STATUS: KERANGKA untuk ditinjau peneliti. BELUM dibekukan, dan belum layak dibekukan** sampai prasyarat di bawah
> terpenuhi. Butir **[PUTUSKAN]** adalah usulan. Nomor amendemen usulan: A-44. Isi E7 diinferensikan dari memori (§3 "metrik
> utilitas", Parthiban-Krishna) dan dari analisis eksploratori A-41; **peneliti harus memastikan ini memang E7**.

## Mengapa desainnya prospektif

Analisis eksploratori A-41 menghasilkan hipotesis baru pada data yang **sudah terlihat**, sehingga menguji ulang di data yang
sama tidak konfirmatori. Jalan yang jujur adalah menguji pada minggu yang labelnya belum pernah dihitung. Data berakhir pada
snapshot 2026-09-21, jadi label minggu 2026-08-31 dan setelahnya belum dapat dihitung hari ini.

## Hipotesis yang dinyatakan sebelum data (dari A-41)

| ID | Pernyataan | Kriteria |
|---|---|---|
| P7a | **Prediksi rezim.** Pada minggu forward tanpa pergantian versi model EPSS, HANFIS **tidak** lebih baik dari persistence. | SS terhadap persistence: batas atas CI95 < 0,05 (SESOI E4). Hasil sebaliknya (SS >= 0,05 dengan batas bawah > 0) membantah hipotesis rezim. |
| P7b | **Hibrida.** Campuran persistence dan HANFIS mengalahkan persistence. | SS_hibrida terhadap persistence >= 0,05, batas bawah CI95 > 0. Hibrida dibekukan sebelum data: `y_hat = lambda * y_hat_HANFIS + (1 - lambda) * y_lag4`, **satu** parameter lambda di [0,1] dari kuadrat terkecil pada minggu latih [PUTUSKAN]. |
| P7c | **Utilitas (peringkat).** Peringkat per minggu: Spearman dan presisi@20%. | Dilaporkan untuk HANFIS, persistence, hibrida, ridge-7; kriteria utama P7c: hibrida >= persistence pada presisi@20% [PUTUSKAN]. |

Analisis: MSE terkumpul, bootstrap berkelompok per image (2.000), koreksi Holm pada keluarga {P7a, P7b}. P7c dilaporkan
dengan CI tanpa koreksi karena sekunder.

## Prasyarat yang HARUS ada sebelum pembekuan

1. **Pindai ulang 120 image** dengan DB Trivy yang dibekukan pada tanggal D2 (A-15: satu pindaian hanya memuat CVE yang
   diketahui saat itu; tanpa ini CVE baru tidak ada di data forward). Hasilnya dataset versi 3 dengan checksum.
2. **Minggu uji** hanya `t` dengan `t + 28 hari <= D2`. Bila D2 = awal November, minggu yang matang kira-kira sampai
   pertengahan Oktober. Jumlah minggu minimum untuk analisis: 6 [PUTUSKAN]; kurang dari itu E7 ditunda, bukan dilonggarkan.
3. **Model dibekukan** (hash berkas) sebelum label forward dihitung: dilatih pada **semua** minggu berlabel <= 2026-08-24,
   konfigurasi A-09 + A-10, lima seed yang sama. Cek gerbang >= 10 observasi per parameter (di sini sekitar 39).
4. **Persistence memakai label versi 3** untuk minggu `t - 4`, supaya perbandingan konsisten.
5. **Versi model EPSS** pada minggu forward dicatat; bila ada pergantian baru, minggu itu dipisah sebagai rezim patahan.

## Risiko yang dinyatakan

Bila snapshot EPSS/KEV mingguan tidak dikumpulkan sejak 2026-09-21, snapshot yang hilang harus diambil dari arsip publik
dan disegel dengan manifest sebelum label dihitung. Bila ada celah, minggu itu dikecualikan dan dihitung.

## Tidak akan dilakukan

Melatih ulang setelah melihat label forward; menyesuaikan lambda atau ambang setelah hasil terlihat; memilih minggu;
menambah pembanding; mengubah definisi hibrida.

## Sumber

`HANFIS_RESEARCH_MEMORY.md` (A-09, A-10, A-13, A-15, A-34, A-41); `results_python/e4_regime*` dan `e4_influence*`.

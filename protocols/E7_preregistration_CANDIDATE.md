# Protokol E7 — Evaluasi prospektif HANFIS (KANDIDAT PEMBEKUAN, satu dokumen konsisten)

> **Status: KANDIDAT.** Menggabungkan draf dan amendemen A-44 sampai A-48 menjadi satu teks tanpa butir yang saling bertentangan. Dibekukan hanya lewat urutan di bagian 11
> (komit, `make_prereg_tag.py`, `verify_prereg_tag.py` LOLOS). Setelah beku, perubahan hanya lewat amendemen bernomor. Isi [KURUNG SIKU] diisi saat pembekuan.
> Tanggal pembekuan: [TANGGAL]. Komit: [HASH KOMIT]. Tag: [TAG].

## 1. Tujuan dan dasar

Analisis post hoc E4 (A-41) menunjukkan bahwa HANFIS **reaktif**: ia unggul atas persistence ketika label bergerak (SS +0,483 di dalam jendela perubahan model EPSS) dan tidak ketika stabil (SS −0,420).
Hipotesis itu lahir dari data yang sudah terlihat, sehingga uji ulang pada data yang sama tidak konfirmatori. E7 mengujinya **prospektif** pada minggu yang labelnya belum pernah dihitung (snapshot EPSS tersegel berakhir 2026-09-21; label minggu >= 2026-08-31 belum dihitung).
Kode analisis diuji (latihan) hanya pada data lama, termasuk latihan pseudo-forward; angka latihan bukan bukti E7.

**Peran rumus bentuk-maks.** Analisis post hoc E11 dan E12 (out-of-fold, bukan konfirmatori) menunjukkan bahwa rumus empat parameter dari x2 dan x7 memiliki kesalahan lebih kecil daripada HANFIS dan daripada persistence, dan bahwa campuran lintas-fold antara rumus dan persistence atau HANFIS tidak memperbaikinya. E7 karena itu juga menguji rumus itu secara prospektif (P7e dan P7f, bagian 5), di samping hipotesis reaktivitas HANFIS di atas.

## 2. Unit, data, dan minggu uji

- **Aset:** 120 aset pada `configs/assets.csv` (117 image resmi berpatok digest, `p0-baseline`, `p0if-on`, `p0if-off`); unit analisis: asset-minggu; kelompok bootstrap: image (`p0if-on` dan `p0if-off` satu kelompok).
- **Label:** definisi §3.3 (A-13): `y(a,t) = 100 x rerata atas snapshot mingguan tau di {t+7, ..., t+28 hari} dari maksimum atas CVE aktif v dari X_v(tau) x rho_v`, dengan `X_v = max(EPSS, 1[KEV])`, skala 0–100, `y` kosong bila jendela melewati snapshot terakhir.
- **Minggu uji:** minggu `t` (Senin) dengan `t >= 2026-08-31` dan `t + 28 hari <= D2`.
- **D2 primer = 2026-11-02:** enam minggu, t = 2026-08-31, 09-07, 09-14, 09-21, 09-28, 10-05.
- **Cadangan D2 = 2026-11-09 (tujuh minggu, tambah t = 10-12):** hanya bila saat dataset versi 3 dibangun jumlah minggu matang < 6, diputuskan **sebelum model apa pun dijalankan pada data forward**. Kurang dari 6 minggu: E7 ditunda, kriteria tidak dilonggarkan. Tidak ada pilihan D2 setelah melihat hasil.
- **Bukti tidak cukup:** `--drop-insufficient` pada `build_asset_weeks.py` hanya dipakai bila baris yang dibuang pada minggu uji <= 2% dari baris minggu uji; aset yang kehilangan seluruh minggu ujinya otomatis keluar dari analisis forward (ia tidak memiliki baris uji) dan dilaporkan; tiap baris yang dibuang dilaporkan per `asset_id`. Pada inventaris saat ini `cockroachdb` memiliki bukti rentang versi tidak cukup pada tujuh minggu berurutan, 2026-08-10 sampai 2026-09-21, dan diperkirakan keluar; pada 720 baris uji (120 aset x 6 minggu) batas 2% berarti paling banyak 14 baris, yaitu dua aset penuh. Lebih dari itu: HOLD, E7 tidak dijalankan sampai dikaji (keputusan diambil sebelum model dijalankan pada data forward).
- **Eksklusi:** minggu tanpa rangkaian snapshot lengkap (dicatat); baris tanpa `y_lag4`; baris dengan masukan tidak diketahui tetap dipakai model (nilai hilang = 0 seperti E4) tetapi dikecualikan dari strata perubahan masukan.

## 3. Model dan pembanding (dibekukan sebelum label forward dihitung)

- **HANFIS:** lima model (seed 20260928, 20261005, 20261012, 20261019, 20261026) dilatih pada **minggu berlabel <= 2026-07-27** (minggu forward pertama 2026-08-31 dikurangi embargo 30 hari; jendela label latih terakhir berakhir 2026-08-24, sebelum 2026-08-31).
  Konfigurasi identik dengan E4 (A-09, A-10): `HANFIS(m_raw=2, m_intermediate=3, gauss, monotone)`, `fit_hybrid_lower_alternating`, 3 restart terbaik, patience 100, min_epochs 200, ridge=None, validasi acak 15% (seed 20260933).
  5.880 baris latih, 33,4 observasi per parameter (176 parameter). Prediksi = rerata lima seed x 100. Manifes dan hash: `results_python/e7_final/final_models_manifest.json` [SHA256 MANIFES].
- **Persistence:** `y_lag4` = label versi 3 pada minggu `t - 28 hari` untuk aset yang sama (pencocokan kalender).
- **Hibrida:** `y_hibrida = lambda * y_HANFIS + (1 - lambda) * y_lag4`, **lambda = 0,5109** (CI95 bootstrap berkelompok [0,260; 0,778]) dari `protocols/E7_lambda_2026-10-08.json` [SHA256], dipasang pada prediksi out-of-fold E4 (label <= 2026-08-24; sudah ber-embargo). Tidak disetel ulang.
- **Ridge-7** (7 masukan, lambda ridge 1e-3, dilatih pada baris latih yang sama): pembanding deskriptif.
- **Rumus bentuk-maks:** `y_rumus = a + b * max(x2, c * x7)`, x2 = `exploitability` dan x7 = `threat_intelligence` pada waktu t (nilai hilang = 0). `c` dipilih dari grid {0, 0,05, ..., 1,5}, `a` dan `b` dengan kuadrat terkecil biasa, pada baris latih yang SAMA dengan model akhir (berlabel, minggu <= 2026-07-27; 5.880 baris), oleh `scripts/e7_formula.py fit`. Koefisien dibekukan di `protocols/E7_formula_2026-10-12.json` [SHA256]. Tidak disetel ulang.

## 4. Prosedur data (urutan wajib; semua skrip ikut dibekukan)

1. Pembekuan (bagian 11). **Sebelum itu tidak ada label minggu >= 2026-08-31 yang dihitung dan tidak ada snapshot EPSS setelah 2026-09-21 yang diunduh.** Keadaan data saat pembekuan: snapshot EPSS tersegel sampai 2026-09-21 (rentang diverifikasi dengan `fetch_snapshots.py status`); satu snapshot KEV bertanggal 2026-09-28 (1.728 entri, sha256 `164f2f10…`) sudah ada sebelum E7 dirancang (diambil untuk E4-bis) dan tidak dipakai menghitung label forward; `data/real/snapshots/manifest.json` [SHA256] dibekukan bersama protokol.
2. Setelah tag: `python scripts/fetch_snapshots.py fetch --start 2026-09-28 --end <D2>`, lalu `status` dan `verify` (kegagalan integritas = berhenti).
3. Pada D2: `python scripts/e7_rescan.py --d2 <D2> --download-db` (DB Trivy diunduh satu kali dan dibekukan untuk seluruh run; DB harus segar; setiap bundel mencatat tanggal DB yang sama) menghasilkan `configs/assets_v3.csv` dan manifes.
4. `python scripts/build_asset_weeks.py --assets configs/assets_v3.csv --snapshots data/real/snapshots --out-prefix data/processed/asset_weeks_v3 --start 2025-08-25 --end <minggu uji terakhir>` membangun tabel versi 3 (mencetak tiga angka wajib dan `STATUS=TRAINING_AUTHORIZED|HOLD`; `HOLD` menghentikan prosedur); checksum dicatat.
5. `python scripts/e7_pipeline.py predict --table <v3> --models-dir results_python/e7_final --first-week 2026-08-31 --last-week <minggu terakhir>` (menolak minggu sebelum minggu forward pertama model dan memverifikasi hash model).
6. `python scripts/e7_evaluate.py --run --tag <TAG> --files <berkas beku>` (menolak berjalan bila `verify_prereg_tag.py` gagal). **Dijalankan satu kali.**
7. `python scripts/e7_formula.py evaluate --run --pred <prediksi forward> --table <v3> --formula-json protocols/E7_formula_2026-10-12.json --tag <TAG> --files <berkas beku>` (dijalankan otomatis oleh `scripts/e7_d2.py` sebagai tahap terakhir; **dijalankan satu kali**).

## 5. Hipotesis dan kriteria

`SS_m = 1 - MSE_m / MSE_persistence`, MSE terkumpul pada skala mentah 0–100. CI: bootstrap berkelompok per image (2.000 resampel, seed 20261102, persentil 2,5 dan 97,5). SESOI = 0,05.

| ID | Pernyataan | Kriteria |
|---|---|---|
| P7a | Pada minggu forward dengan versi model EPSS yang sama dengan minggu forward pertama, HANFIS **tidak** lebih baik dari persistence. | DIDUKUNG bila batas atas CI95 `SS_HANFIS` < 0,05 dan lolos Holm; DIBANTAH bila `SS >= 0,05` dan batas bawah > 0; selain itu TIDAK TERBUKTI. |
| P7b | Hibrida mengalahkan persistence (semua minggu forward). | TERKONFIRMASI bila `SS_hibrida >= 0,05`, batas bawah CI95 > 0, dan lolos Holm; LEBIH BURUK bila batas atas < 0; selain itu TIDAK TERKONFIRMASI. |
| P7d | HANFIS membawa informasi arah perubahan di atas persistence (sekunder, tanpa koreksi). | Rerata mingguan korelasi Spearman antara `y_HANFIS - y_lag4` dan `y_true - y_lag4` (minggu dengan >= 5 aset); INFORMATIF bila batas bawah CI95 (1.000 resampel) > 0. Hibrida identik dengan HANFIS pada metrik ini (lambda > 0). |

**Holm** pada keluarga {P7a, P7b}: p-value satu sisi dari bootstrap (+1), alpha satu sisi 0,025, sehingga ambang 0,0125 untuk p terkecil dan 0,025 untuk berikutnya; P7a menguji H0 `SS >= 0,05`, P7b menguji H0 `SS <= 0`.
**Deskriptif (tanpa kriteria):** P7c (presisi@20% dan Spearman pada level; persistence sudah mencapai 0,969 pada data lama, efek langit-langit); SS per strata perubahan masukan yang tersedia pada waktu t (selisih x2 atau status KEV selama 4 minggu = 0 vs > 0); lambda per fold; skala log1p; hasil tanpa image `wordpress`; ridge-7.

**Keluarga kedua (rumus bentuk-maks; asal post hoc; didaftarkan sebelum data forward).** {P7e, P7f} dikoreksi dengan Holm di dalam keluarganya sendiri (alpha satu sisi 0,025; ambang 0,0125 untuk p terkecil dan 0,025 untuk berikutnya; p satu sisi dari bootstrap dengan +1), terpisah dari keluarga pertama {P7a, P7b}. Kedua keluarga menjawab pertanyaan yang berbeda (HANFIS terhadap persistence; rumus sederhana terhadap persistence dan terhadap HANFIS), sehingga kesalahan tipe I dikendalikan per keluarga; gabungan satu sisi paling banyak 0,05 (Bonferroni atas dua keluarga). Metrik, bootstrap (berkelompok per image, 2.000 resampel, seed 20261102), populasi baris, dan SESOI 0,05 identik dengan keluarga pertama. P7d tetap sekunder tanpa koreksi. Sebagai analisis sensitivitas tanpa kriteria, P7e dan P7f juga dilaporkan dengan bootstrap per minggu.

| ID | Pernyataan | Kriteria |
|---|---|---|
| P7e | Rumus bentuk-maks mengalahkan persistence (semua minggu forward). | TERKONFIRMASI bila `SS(rumus terhadap persistence) >= 0,05`, batas bawah CI95 > 0, dan lolos Holm (keluarga kedua); LEBIH BURUK bila batas atas < 0; selain itu TIDAK TERKONFIRMASI. |
| P7f | HANFIS tidak lebih baik daripada rumus bentuk-maks. | DIDUKUNG bila batas atas CI95 dari `SS(HANFIS terhadap rumus)` < 0,05 dan lolos Holm (keluarga kedua); DIBANTAH bila `SS >= 0,05` dan batas bawah > 0; selain itu TIDAK TERBUKTI. |

## 6. Keterbatasan yang dinyatakan sebelum data

- **Daya terbatas.** Pada latihan out-of-fold E4, `SS_hibrida` 0,174 dengan CI95 [0,011; 0,236] dan p Holm 0,021 (di atas ambang 0,0125); pada latihan pseudo-forward enam minggu CI95 `SS_hibrida` lebar ([−0,934; +0,031]) karena ekor berat. "Tidak terbukti" **bukan** bukti kesetaraan; E7 dilaporkan sebagai estimasi prospektif dengan CI.
- **Pergeseran versi EPSS.** Dari 49 minggu latih, 38 berlabel model EPSS lama, 3 campuran, 8 model baru; semua minggu forward berlabel model baru. Tidak ada pelatihan ulang; pergantian versi lagi pada minggu forward memisahkan minggu itu sebagai rezim patahan.
- **Apa yang diukur model (E8, deskriptif).** Atribusi Shapley eksak pada 25 model E4-bis menempatkan **78,9%** dampak pada x2 (EPSS x rho) dan x7 (KEV), yaitu bahan label yang juga masukan, dan hanya **3,3%** pada masukan lingkungan (x4–x6); pada baris dengan label 20% teratas, x7 saja menyumbang 63,0%. Hasil E7 karena itu terutama mencerminkan kemampuan meramal sinyal exploitability yang sudah terlihat, bukan nilai konteks lingkungan; label tidak memuat komponen lingkungan.
- **Pandangan ke belakang (backfill) DB.** Pindai ulang pada D2 memuat CVE yang terbit sebelum `t` tetapi baru tercatat di DB setelah `t`; E4 memiliki batasan yang sama (DB beku 2026-09-14). Latihan pindai ulang menunjukkan inventaris CVE tumbuh cepat: P0 109 -> 157 CVE (+44%) dan `nginx-1-27-alpine` 137 -> 159 antara bundel lama dan DB 2026-10-02.
- **Lambda** dipasang pada model validasi silang dan diterapkan pada model akhir yang dilatih dengan data lebih banyak; ketidakcocokan ini dinyatakan, bukan disetel.
- Hipotesis P7a, P7b, dan P7d berasal dari analisis post hoc E4 dan latihan kode pada prediksi out-of-fold dan data pseudo-forward (bukan data forward).
- **Rumus ditemukan post hoc.** Bentuk rumus dan hipotesis P7e dan P7f lahir dari analisis out-of-fold E11, setelah hasil E4 dan E8 sampai E10 terlihat. Dukungan out-of-fold (SS HANFIS terhadap rumus -0,534, CI95 [-1,438; -0,208]; SS rumus terhadap persistence +0,357, CI95 [+0,279; +0,407]) **tidak** dihitung sebagai konfirmasi; hanya data forward yang dihitung.
- **Target tidak bergantung pada masukan lingkungan** (x4 sampai x6 konstan per aset dan tidak masuk label), sehingga E7 tidak dapat menguji manfaat masukan lingkungan. Analisis E8 sampai E10 menunjukkan bahwa kemampuan HANFIS bertumpu pada x2 dan x7.
- Dalam E11 `c` terpilih 0,10 pada kelima fold; bila minggu forward menunjukkan nilai yang sangat berbeda, itu dilaporkan sebagai temuan, bukan disetel.
- **E12 (post hoc, deskriptif).** Campuran rumus dengan persistence (bobot rumus 1,0 pada kelima fold) dan dengan HANFIS (bobot rumus 0,91 sampai 0,98), dengan bobot dipasang pada fold lain, tidak menurunkan kesalahan rumus (SS campuran rumus+HANFIS terhadap rumus -0,001, CI95 [-0,010; +0,003]); pada data out-of-fold persistence dan HANFIS tidak menambah informasi di luar rumus. Ini bukan hipotesis E7 dan tidak dihitung sebagai konfirmasi.
- **Daya P7e dan P7f.** Keduanya mewarisi keterbatasan daya enam minggu dan ekor berat yang sama; hasil TIDAK TERBUKTI atau TIDAK TERKONFIRMASI tidak boleh dibaca sebagai kesetaraan. Pada 40 jendela enam minggu historis dari prediksi out-of-fold (E13, post hoc; jendela saling tumpang tindih), P7e memenuhi kriterianya di sekitar 35% jendela dan P7f di sekitar 72% sampai 78%, P7a di sekitar 38% dan P7b di sekitar 28% sampai 30%; hasil TIDAK TERKONFIRMASI pada P7e karena itu sering diperkirakan dan tidak boleh dibaca sebagai penolakan rumus.
- **Ketergantungan antar minggu.** Bootstrap berkelompok per image memperlakukan guncangan mingguan yang dialami semua image (misalnya perubahan skor EPSS) sebagai tetap; dengan enam minggu, jumlah titik waktu efektif adalah enam dan CI dapat terlalu sempit. Perbandingan kemampuan prediksi pada deret waktu biasanya memperhitungkan ketergantungan ini; bootstrap per minggu dilaporkan sebagai sensitivitas, tanpa kriteria. Pada prediksi out-of-fold (45 minggu), CI95 keunggulan rumus terhadap persistence dengan bootstrap per minggu, [+0,127; +0,672], sekitar tiga kali lebih lebar daripada dengan bootstrap per image, [+0,263; +0,425]. Keputusan konfirmatori mengikuti prosedur per image yang didaftarkan; bila kriteria terpenuhi menurut prosedur per image tetapi tidak menurut sensitivitas per minggu, hasilnya dilaporkan sebagai terkonfirmasi menurut inferensi per image dan rapuh menurut inferensi per minggu.

## 7. Yang tidak akan dilakukan

Menghitung label atau menarik snapshot minggu >= 2026-08-31 sebelum tag; melatih ulang setelah melihat label forward; menyetel lambda, D2, SESOI, ambang Holm, atau definisi hibrida setelah hasil terlihat; memilih minggu atau aset; menambah pembanding ke keluarga keputusan; menjalankan `e7_evaluate.py --run` lebih dari satu kali.

Juga tidak akan dilakukan: mengubah grid `c`, koefisien rumus, atau bentuk rumus setelah label forward terlihat; menambahkan varian rumus lain ke keluarga keputusan.

## 8. Artefak yang dibekukan (semuanya harus dikomit tanpa perubahan saat tag dibuat)

`protocols/E7_preregistration_[TANGGAL].md` · `protocols/E7_lambda_2026-10-08.json` · `results_python/e7_final/final_models_manifest.json` dan `results_python/e7_final/models/final_seed*_hanfis.pt` ·
`scripts/e7_pipeline.py` · `scripts/e7_evaluate.py` · `scripts/e7_rescan.py` · `scripts/verify_prereg_tag.py` · `scripts/make_prereg_tag.py` · `scripts/fetch_snapshots.py` · `scripts/build_asset_weeks.py` · `scripts/e4_run.py` · `scripts/scan_image_evidence.sh` ·
`python_hanfis/hanfis_end2end.py` · `python_hanfis/splits.py` · `configs/assets.csv`. [Skrip pelaksana D2 satu-langkah, bila ditambahkan, masuk daftar ini sebelum tag.]

Tambahan artefak beku (rumus dan pelaksana): `scripts/e7_formula.py` · `protocols/E7_formula_2026-10-12.json` · `scripts/e7_d2.py`.

## 9. Riwayat amendemen yang tergabung

A-44 (desain awal, D2, hibrida satu lambda) · A-45 (D2 primer 2026-11-02 dengan cadangan) · A-46 (P7c menjadi deskriptif, P7d ditambahkan setelah latihan kode) · A-47 (batas latih diperbaiki dari 2026-08-24 menjadi 2026-07-27: kebocoran temporal) · A-48 (koreksi 6.833 total vs 6.357 berlabel).

## 10. Transparansi

E6 dijalankan dengan protokol yang tag pembekuannya mendahului komit yang memuat teks akhirnya (deviasi prosedural, A-43). Untuk E7, `make_prereg_tag.py` menolak membuat tag bila ada berkas belum dikomit, dan `e7_evaluate.py --run` menolak berjalan bila `verify_prereg_tag.py` gagal.

## 11. Urutan pembekuan

0. `python scripts/e7_formula.py fit` (harus mencetak `STATUS=E7_FORMULA_FIT_DONE` dengan 5.880 baris), lalu `git add -f protocols/E7_formula_2026-10-12.json`; berkas itu masuk komit pembekuan.
1. Ganti nama berkas ini menjadi `protocols/E7_preregistration_[TANGGAL].md`, isi tanda kurung siku, `git add` seluruh artefak bagian 8 (`git add -f` untuk `results_python/e7_final`), `git commit`.
2. `python scripts/make_prereg_tag.py e7-prereg-[TANGGAL] <seluruh artefak bagian 8>` harus mencetak LOLOS.
3. (Opsional, disarankan) daftarkan di OSF Registries dengan teks `E7_osf_registration_DRAFT.md`, **sebelum** langkah 2 bagian 4.
4. `git push` dan `git push origin --tags`.

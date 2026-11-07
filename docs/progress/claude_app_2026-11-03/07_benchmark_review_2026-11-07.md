# Pembacaan pembanding dan penilaian ulang naskah HANFIS (7 November 2026)

Sumber: empat paper pembanding yang diunggah (Juston dkk. 2024, IEEE TFS; Parthiban dan Krishna 2026, IEEE Access; Wu dan Zaman 2025, Robotics and Autonomous Systems; Jabeen dkk. 2023, Applied Soft Computing), naskah `sn-article_2026-11-03.pdf` (48 halaman), `additional_file_1_2026-11-03.pdf`, berkas 00 sampai 06, dan memori repositori v2.62. Skill yang dipasang dan dibaca sebagai kerangka: `academic-paper` dan `academic-paper-reviewer` (imbad0202/academic-research-skills), `manuscript-writing`, `manuscript-formatting`, `paper-review` (neuromechanist/research-skills), dan `academic-research-writer` (endigo/claude-skills). Semua skor di bawah adalah pertimbangan, bukan pengukuran. Hal yang belum dicek terhadap repositori ditandai "belum diperiksa".

Aturan keras tetap berlaku: tidak ada analisis tambahan atas hasil E7, tidak ada penyetelan, post hoc tetap ditandai post hoc, sitasi tidak ditulis dari ingatan (nama penulis di bawah hanya penunjuk untuk dicari di doi.org, bukan entri siap pakai).

> Catatan penyimpanan (7 November, sesi repositori): dokumen ini disimpan apa adanya dari aplikasi Claude. Pencocokannya terhadap repositori ada di `08_pencocokan_benchmark_dengan_progres_2026-11-07.md`. Dua klaim di bawah ternyata tidak sesuai repositori: butir 4 di bagian 1 dan baris "Permukaan respons / PDP" di tabel bagian 1 menyebut gambar PDP belum ada, padahal sudah ada; lihat berkas 08.

---

## 1. /analyze: pola penulisan di empat paper pembanding

| Pola | Juston 2024 (TFS) | Parthiban 2026 (Access) | Wu dan Zaman 2025 (RAS) | Jabeen 2023 (ASOC) | Naskah HANFIS |
|---|---|---|---|---|---|
| Jumlah referensi | 68 | 29 | 48 | 41 | 20 |
| Related work sebagai bagian tersendiri | Ya (FIS, HRBR, ANFIS) | Ya (di Introduction, padat) | Ya (tiga paradigma formasi + FIS hierarkis) | Ya (derivatif vs heuristik) | Hanya 2.1 ANFIS, sekitar setengah halaman |
| Kontribusi bernomor yang dikontraskan dengan rujukan spesifik | Tiga "innovations" | Empat kontribusi | Empat kontribusi, masing-masing "unlike [13 sampai 15]..." | Dua keterbatasan prior yang ditangani | C1 sampai C4 tanpa rujukan pembanding |
| Paragraf peta isi ("Section II ... Section VIII") | Ya | Ya | Ya | Ya | Tidak ada |
| Eksposisi ANFIS lapis demi lapis dengan persamaan bernomor | Ya, 81 persamaan, notasi matriks | Ringkas | Ya, 39 persamaan | Ya | Ringkas (Pers. 3 sampai 4); cukup untuk JoCC |
| Diagram arsitektur dengan alur sinyal | Ya | Ya (Fig. 3 dan 4) | Ya (Fig. 5 dan 6) | Ya | Ya (Fig. 1 TikZ, baru) |
| Basis aturan ditampilkan | Ya (matriks A, Q, P) | Ya (screenshot rule viewer, praktik lemah) | Ya (Tabel 2 sampai 5, semua konsekuen) | Tidak | Tidak ada satu pun aturan terlatih yang ditampilkan |
| Permukaan respons / PDP | Tidak | Ya (Fig. 8, 13, 14) | Fig. 9 (vector field) | Tidak | Tidak ada; hanya Tabel 6 (sapuan monotonisitas) |
| Tabel hiperparameter | Sebagian (Tabel II, III) | Tidak | Tabel 1 | Tabel 5 | Dalam prosa 4.2 (lr, ridge, patience, restart) |
| Uji statistik bernama dan dikutip | Tidak (satu run simulasi) | Tidak (70/30 split, RMSE) | Tidak | 5x2cv paired t-test (Dietterich 1998), 10-fold CV | Bootstrap berkluster, Holm, SESOI, praregistrasi, OSF |
| Hasil negatif dilaporkan | Tidak | Tidak | Sebagian (ANFIS berosilasi) | Tidak | Ya, menyeluruh |
| Ablasi | Tidak | Tidak | Ya (dengan/tanpa F_cd) | Perbandingan 4 algoritma | Ya (E1, E5, E9, E16 sampai E19) |
| Reproducibility | Tidak | Tidak | "Data confidential" | Code Ocean capsule | Zenodo DOI, OSF, tag git, SHA-256 |
| Limitations | Dalam Conclusion, satu kalimat | Satu paragraf di Conclusion | Tidak eksplisit | Dalam Conclusion (Gaussian saja) | Subbagian tersendiri, panjang |
| Panjang badan | 13 halaman dua kolom | 11 halaman | 18 halaman | 12 halaman | 48 halaman referee (sekitar 10.950 kata) |

### Pola yang layak diadopsi

1. Related work berlapis tiga. Keempat paper memetakan (a) keluarga metode, (b) upaya reduksi kompleksitas, (c) domain aplikasi, lalu menempatkan kontribusi di persilangan ketiganya. Naskah HANFIS hanya punya (a) dalam bentuk minimal. Untuk JoCC yang pembacanya praktisi cloud, lapisan (c) yang hilang paling terasa: tidak ada tinjauan atas vulnerability prioritization berbasis EPSS/KEV, SSVC, atau risk scoring untuk Kubernetes, padahal itulah yang membuat persistence dan rumus max-form masuk akal sebagai pembanding.

2. Kontribusi dikontraskan dengan rujukan. Wu dan Zaman menulis setiap kontribusi sebagai "berbeda dari [x] yang melakukan y". C1 sampai C4 HANFIS berdiri sendiri; satu klausa kontras per kontribusi (misalnya C1 terhadap Soozanchi 2010 dan hierarchical fuzzy control klasik; C3 terhadap CVSS v4 Threat metric dan EPSS) akan memperjelas kebaruan tanpa menambah klaim.

3. Basis aturan ditampilkan. Tiga dari empat paper menampilkan aturan hasil akhir. Naskah HANFIS menyatakan nilai HANFIS "lies in structure and interpretability" dan "a readable rule base" (Discussion, Conclusion) tetapi tidak menampilkan satu aturan pun, baik di badan maupun di Additional file 1. Ini celah antara klaim dan bukti yang paling mudah ditanyakan penelaah. Menampilkan 34 aturan satu seed (pusat dan lebar MF, konsekuen) dari 25 model tersimpan adalah dokumentasi, bukan analisis baru, dan tidak menyentuh E7.

4. Permukaan respons. Parthiban menampilkan surface view untuk setiap ANFIS. Untuk HANFIS, satu gambar r terhadap (x2, x7) dari ensemble lima seed akan memberi bukti visual bagi kalimat "documented response surface" (Conclusion) dan bagi hasil E8 (Tabel 6). Memori repositori A-34 mencatat flag `--save-models`/PDP (patch 0068) ada tetapi gambar belum dibuat; dengan 25 model tersimpan ini bisa dilakukan tanpa pelatihan ulang. Ini pilihan presentasi, bukan keharusan, dan harus diberi label deskriptif.

5. Paragraf peta isi di akhir Introduction. Semua pembanding memilikinya; biayanya tiga kalimat.

6. Tabel hiperparameter dan konfigurasi beku. Pindahkan isi prosa 4.2 (lr 1e-2, ridge 1e-3, 3 restart, patience 100, minimum 200 epoch, Gaussian + monotonik, GroupTimeSplit 5 fold, embargo 30 hari) ke satu tabel kecil di Additional file 1, dengan rujukan ke amendemen A-09 dan A-16.

### Pola yang tidak perlu ditiru

Screenshot MATLAB sebagai gambar (Parthiban), satu run simulasi tanpa interval (Juston, Parthiban), data "confidential" (Wu dan Zaman), dan kalimat penutup "the results demonstrate the effectiveness" tanpa ukuran (ketiganya). Dalam hal ketelitian statistik, praregistrasi, dan pelaporan hasil negatif, naskah HANFIS sudah di atas keempat pembanding.

---

## 2. Temuan konsistensi internal dari pembacaan utuh (prioritas tinggi)

Ini bukan masukan gaya, melainkan hal yang penelaah metodologi akan tangkap pada bacaan pertama.

### 2.1 Label hipotesis H2 dan H3 tidak sejalan antara Section 1 dan Results

Section 1 mendefinisikan H2 sebagai efisiensi komputasi (lebih sedikit aturan dan parameter, waktu latih, memori puncak, latensi inferensi lebih rendah daripada flat ANFIS) dan H3 sebagai performance preservation (non-inferior terhadap FlatANFISMatched). Tabel 4, Section 4.3, 4.5, dan Conclusion melaporkan perbandingan skill terhadap FlatANFISMatched sebagai "H2 ... Confirmed". H3 tidak pernah diputuskan di mana pun (hanya disebut empat kali: definisi, "falsification of H2/H3", dan dua kalimat "H1a–H1c and H2–H3 are pre-registered"). Memori repositori (A-20, A-34) memang menyebut perbandingan matched sebagai H2 sejak awal, jadi kemungkinan daftar hipotesis di naskah yang tertinggal dari protokol E4. Berkas 02 menyatakan H1a sampai H5 tidak boleh diubah kata per kata; bila itu dipertahankan, maka Tabel 4 dan setiap "H2" yang merujuk perbandingan matched harus menjadi "H3", dan H2 harus dilaporkan terpisah (lihat 2.2). Perlu dicek dulu (belum diperiksa): penamaan hipotesis di `protocols/E4_preregistration_2026-09-29*.md` dan tag `e4-prereg-2026-09-29`. Yang mana pun yang menang, naskah harus konsisten dengan protokol beku, bukan sebaliknya.

### 2.2 Pengukuran komputasi yang dijanjikan C2, H2, dan Introduction tidak ada di naskah

Introduction (baris 190 sampai 193) menyatakan biaya komputasi "is measured (rule count, trainable parameters, training duration, peak memory, throughput, and median and tail inference latency)". C2 menjanjikan "empirical measurements of parameter count, training cost, memory consumption, throughput, and inference latency". H2 menjanjikan pengurangan training time, peak memory, inference latency relatif terhadap flat ANFIS. Yang ada di badan dan Additional file 1 hanya jumlah aturan dan parameter (Tabel 1). Tidak ada tabel waktu latih, memori, throughput, atau latensi untuk HANFIS versus flat ANFIS; `results_efficiency.tex` di repositori adalah overhead observabilitas (Tabel 2), bukan efisiensi model. Dua jalan keluar yang sesuai aturan proyek:

- A. Bila angka waktu latih dan latensi sudah ada di log E4/E4-bis (belum diperiksa; pelatihan 5 fold x 5 seed x 3 restart hampir pasti mencatat durasi), tambahkan satu tabel kecil (HANFIS vs FlatANFISMatched vs Flat ANFIS penuh: durasi latih per fold, parameter, latensi inferensi per baris) dan beri label deskriptif tanpa uji. Ini pembacaan log, bukan eksperimen baru.
- B. Bila tidak ada, persempit klaim: C2 dan kalimat Introduction menjadi "rule and parameter counts (Table 1)", dan H2 dilaporkan "confirmed for rule and parameter counts by construction; training time, memory and latency were not measured and are left to future work". Ini konsisten dengan praktik A-63 (claim-boundary pass).

Tanpa salah satunya, C2 adalah kontribusi yang tidak dibuktikan.

### 2.3 H4 tidak diuji sebagaimana dirumuskan

H4 menjanjikan perbandingan dengan "an otherwise identical HANFIS without this input" (x7 saja). E9 menghapus x2 dan x7 bersamaan. Tidak ada kalimat yang menyatakan H4 tidak diuji. Satu kalimat di 4.8 atau Limitations cukup: "H4 was not tested as stated; E9 removes x2 and x7 together, and a single-input ablation of x7 was not run."

### 2.4 Angka baris uji 981 di Section 4.4 berasal dari inventaris 109 aset

Kalimat "identical fold assignment for all 981 held-out rows ... Pearson r = 0.9984" berasal dari pemeriksaan paritas A-26 pada inventaris 109 aset (n_test 981). Tabel 5 dan kalimat sekitarnya memakai inventaris 120 aset (1.080 baris uji). Paragraf itu mencampur dua inventaris tanpa menyebutnya. Perlu dicek (belum diperiksa): apakah paritas per baris diulang pada 120 aset (A-36). Bila tidak, tulis "on the 109-asset inventory" atau hapus angka itu.

### 2.5 Hal kecil yang terlihat pada bacaan utuh

- Abstrak: "6,357 asset-weeks" sebaiknya "6,357 labelled asset-weeks" (Section 3.5 menyebut 6.833 baris). Memori A-76 sudah mencatat ketidaksesuaian ini sebagai belum diperiksa.
- Keyword "Nonlinear Risk Mitigation" tidak menggambarkan isi; naskah tidak melakukan mitigasi. Kandidat pengganti: "Hierarchical fuzzy systems", "Exploit prediction", "Vulnerability prioritization".
- Section 4.3 merujuk ke dirinya sendiri: "The E3 pilot showed the same pattern (Section 4.3's baseline table above)". Ganti dengan "(Table 3)".
- Section 2.1 memberi contoh dua aturan Sugeno generik tanpa rujukan ke Jang (1993) di kalimat itu; sitasi Jang ada di Introduction. Tambahkan `\cite` di 2.1 atau hapus contoh generiknya.
- Section 4.5 "Where HANFIS and persistence differ" menyebut "exploratory, post hoc, outside the Holm-corrected family": sudah benar, pertahankan.
- Sitasi metode yang dipakai tetapi tidak dikutip (belum diperiksa di .bib, hanya tidak terlihat di daftar referensi PDF): subtractive clustering untuk FlatANFISMatched (Chiu 1994), Adam (Kingma dan Ba), gradient boosting (Friedman 2001), Kendall W, Spearman. JoCC tidak mewajibkan semuanya, tetapi subtractive clustering adalah inisialisasi pembanding utama H2/H3 dan sebaiknya dikutip. Metadata diambil dari doi.org, bukan dari sini.

---

## 3. /mindmap: peta masukan

```
NASKAH HANFIS (48 hlm, 20 ref, E0..E24 selesai, E7 terkunci)
|
+-- KUAT (pertahankan)
|   +-- praregistrasi + OSF + tag beku + SHA-256 + Zenodo
|   +-- bootstrap berkluster, Holm, SESOI, dua keluarga hipotesis
|   +-- hasil negatif ditulis apa adanya (H1b, E9, E11, H6c, E7)
|   +-- pembanding yang keras: persistence, rumus 4 parameter
|   +-- Limitations tersendiri, telemetri dipisah dari masukan model
|
+-- KONSISTENSI (perbaiki dulu, sebelum gaya)
|   +-- H2 vs H3: label Tabel 4 vs definisi Section 1
|   +-- C2/H2: ukuran komputasi dijanjikan, tidak ada tabelnya
|   +-- H4: tidak diuji, tidak dinyatakan
|   +-- 981 baris (109 aset) di paragraf 120 aset
|   +-- 6.357 vs 6.833; keyword; rujukan diri 4.3
|
+-- CELAH vs PEMBANDING
|   +-- Related work: hierarchical fuzzy, reduksi aturan ANFIS,
|   |   EPSS/KEV/SSVC, Kubernetes risk (20 ref vs 29..68)
|   +-- Basis aturan terlatih tidak ditampilkan
|   +-- Permukaan respons r(x2,x7) tidak ada
|   +-- Kontribusi tanpa kontras rujukan
|   +-- Tidak ada paragraf peta isi
|   +-- Hiperparameter dalam prosa, bukan tabel
|
+-- PELUANG (tanpa analisis baru)
    +-- Posisikan sebagai protocol + benchmark + negative-result paper
    +-- Paragraf "what a practitioner should use" di Discussion
    +-- Tabel aturan + PDP dari 25 model tersimpan (deskriptif)
    +-- Perluas Literature Review (menjawab 2 risiko penelaah di berkas 06)
    +-- Cover letter yang menjual kejujuran metodologis, bukan akurasi
```

---

## 4. /eli5: ringkasan tanpa istilah

Bayangkan empat orang lain menulis laporan tentang mesin penilai yang mirip. Mereka semua menggambar mesinnya, menunjukkan beberapa roda giginya (aturan), dan menceritakan siapa saja yang pernah membuat mesin serupa. Laporan kita lebih jujur dan lebih teliti dalam mengukur, tetapi kita tidak menunjukkan satu roda gigi pun, kita hanya menyebut tiga nama orang yang pernah membuat mesin serupa, dan di halaman depan kita berjanji akan menimbang berat dan kecepatan mesin padahal di dalam tidak ada timbangannya. Penelaah akan percaya pada ukuran kita, lalu bertanya: mana roda giginya, mana timbangannya, dan siapa lagi yang sudah mencoba?

---

## 5. /argue: penelaah versus penulis

Penelaah: "Model yang Anda usulkan kalah dari rumus empat parameter dan tidak lebih baik dari persistence, termasuk pada evaluasi maju. Mengapa paper ini layak terbit?"
Penulis: Karena pertanyaannya dijawab dengan protokol beku dan registrasi publik sebelum data terlihat, dengan pembanding yang paling keras yang bisa dibangun dari data yang sama, dan karena temuan bahwa target exploitability-exposure hampir sepenuhnya ditentukan oleh dua sinyal masukan adalah hasil yang berguna bagi siapa pun yang membangun risk scorer di atas EPSS dan KEV. Paper ini adalah paper protokol dan benchmark; arsitekturnya adalah objek yang diuji, bukan pahlawan ceritanya.
Penilaian saya: argumen penulis kuat, tetapi naskah belum memposisikan dirinya begitu. Judul, C1, dan paragraf pembuka Conclusion masih berbicara sebagai paper sistem. Peneliti sudah memutuskan judul tetap (3 November); keputusan itu dihormati. Yang masih bisa dilakukan tanpa mengubah judul: satu paragraf di awal Discussion yang menyatakan apa yang sebaiknya dipakai praktisi sekarang (rumus max-form, dengan persistence sebagai pembanding wajib), dan untuk apa HANFIS tetap relevan (ketika struktur aturan yang bisa diaudit dibutuhkan dan luaran yang bergantung pada lingkungan tersedia).

Penelaah: "Anda mengklaim nilai HANFIS ada pada interpretabilitas, tetapi E6 gagal kriterianya dan tidak ada aturan yang ditunjukkan."
Penulis: E6 menunjukkan atribusi per aturan benar rata-rata, tidak merata, dan kami menarik klaim penjelasan berlapis. Klaim yang tersisa adalah struktur: 34 aturan yang bisa dibaca dan dicetak.
Penilaian saya: klaim yang tersisa itu sah hanya bila aturannya benar-benar dicetak. Tabel aturan satu seed di Additional file 1 menutup celah ini dengan biaya satu halaman.

Penelaah: "Dua puluh referensi untuk paper 48 halaman di jurnal Q1."
Penulis: Referensi dipilih yang diverifikasi lewat doi.org saja.
Penilaian saya: disiplin verifikasinya benar, jumlahnya tetap akan dibaca sebagai literatur yang tipis. Perluasan 15 sampai 25 referensi terverifikasi di tiga lapisan (Section 1 di atas) adalah kerja menulis, bukan eksperimen, dan masuk dalam 32 hari.

---

## 6. Penilaian ulang (skala 0 sampai 100; pertimbangan, bukan pengukuran)

Arah skala dinyatakan per baris agar tidak ambigu.

| Dimensi | Skor | Arah | Dasar |
|---|---|---|---|
| Strength | 82 | tinggi = kuat | Praregistrasi E4 dan E7, OSF, tag beku, data bersegel, bootstrap berkluster + Holm + SESOI, evaluasi maju sekali jalan, hasil negatif dilaporkan, Zenodo. Di atas keempat pembanding pada semua butir ini. Dipotong karena bukti untuk klaim yang tersisa (struktur, keterbacaan aturan) belum ditampilkan. |
| Weakness | 58 | tinggi = lebih parah | H2/H3/H4 tidak konsisten dengan Results; C2 tanpa bukti; aturan tidak ditampilkan; angka 981 dari inventaris lama; literatur tipis. Sebagian besar dapat diperbaiki dengan teks dan dokumentasi, tanpa eksperimen. |
| Gap | 62 | tinggi = celah lebih besar | Related work tiga lapis; pengukuran komputasi; H4; permukaan respons; kontras kontribusi; paragraf praktisi. Tidak ada celah yang membutuhkan analisis baru atas E7. |
| Opportunity | 74 | tinggi = peluang lebih besar | Reposisi sebagai protocol dan benchmark paper, tabel aturan dan PDP dari model tersimpan, perluasan literatur, cover letter yang tepat. Semua dalam aturan proyek dan dalam tenggat 5 Desember. |
| Kesiapan submit saat ini | 64 | tinggi = siap | Ditahan oleh butir 2.1 sampai 2.4. |
| Kesiapan yang dapat dicapai dalam aturan proyek | 80 sampai 84 | | Bila 2.1 sampai 2.4, Literature Review, tabel aturan, dan paragraf praktisi selesai; sisanya adalah keputusan editor, bukan naskah. |

---

## 7. Urutan kerja yang disarankan (menggantikan urutan 1 sampai 7 di berkas 05 hanya pada butir yang bersinggungan)

1. Putuskan 2.1 (cek protokol E4 beku untuk penamaan H2/H3) dan 2.2 (A atau B). Keduanya menentukan teks di Section 1, Tabel 4, 4.3, 4.5, Conclusion.
2. Tambahkan kalimat H4 tidak diuji (2.3) dan perbaiki 981 (2.4), 6.357 (2.5).
3. Literature Review: tambah 2.2 Hierarchical fuzzy systems and rule-base reduction, 2.3 Exploit prediction and vulnerability prioritization, 2.4 Risk assessment for cloud-native and Kubernetes workloads. Setiap referensi lewat doi.org.
4. Kontras rujukan pada C1 sampai C4 (satu klausa per kontribusi) dan paragraf peta isi.
5. Additional file 1: tabel hiperparameter beku; tabel 34 aturan satu seed; opsional PDP r(x2, x7) dari ensemble, berlabel deskriptif.
6. Paragraf praktisi di Discussion.
7. Baru kemudian: baca ulang manusia utuh (tugas 1 berkas 05), kebijakan AI Springer, Zenodo versi baru, Overfull baris 407, Holm 1979, paket submit dan cover letter.

Setiap perubahan tetap lewat pasangan LAMA/BARU dan skrip teks-persis gagal-tertutup sesuai berkas 06.

---
Dokumen ini disusun dengan bantuan asisten AI (Claude, Anthropic) dari berkas yang diunggah ke sesi 7 November 2026. Angka naskah dikutip dari PDF; pertimbangan ditandai sebagai pertimbangan; hal yang belum dicek terhadap repositori ditandai "belum diperiksa".

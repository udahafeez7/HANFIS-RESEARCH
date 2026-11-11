# Pemeriksaan ulang gerbang, koreksi untuk Overleaf, dan penilaian naskah (11 November 2026)

Sumber: PDF Overleaf `2026_11_07_HIBAH_KEPAKARAN_HAFIZ___ANFIS-2.pdf` (60 halaman, dengan Literature Review 2.2 sampai 2.4, C5, abstrak baru), repositori (HEAD setelah komit perbaikan hari ini), berkas hasil, dan doi.org. Skor adalah pertimbangan, bukan pengukuran.

## 1. Peringatan: dua sumber naskah yang berbeda

Sumber di Overleaf sudah lebih maju daripada `manuscript/sn-article.tex` di repositori (Literature Review tiga bagian dengan 20 referensi baru, kontribusi C5, abstrak dan beberapa kalimat lain). Tidak ada salinan `.tex` baru di mesin ini. Risiko: perbaikan di repositori tidak otomatis sampai ke Overleaf dan sebaliknya. Yang dibutuhkan: unduh proyek Overleaf sebagai zip (Menu, Download, Source) ke `C:\Users\moham\Downloads`, lalu kirim namanya; saya akan membandingkannya dengan repositori dan menjadikan satu sumber kebenaran lewat skrip teks-persis.

## 2. Hasil pemeriksaan ulang gerbang (semua dijalankan 11 November)

| Gerbang | Hasil |
|---|---|
| `pytest -q test tests` | 126 passed, 11 subtests passed |
| Tag beku E7 (`verify_prereg_tag.py`) | LOLOS, 23 berkas identik |
| `e7_d2.py --dry-run` | `STATUS=E7_D2_DRY_RUN` |
| Hash hasil E7, E25, E26 (7 berkas) terhadap memori | semua cocok |
| Cadangan D2 di tiga tempat | `PASS_D2_BACKUP_VERIFY_ONLY` |
| E27 dijalankan ulang | tabel aturan identik bit demi bit (sha256 3aa14d434925420f) |
| Angka di PDF terhadap berkas hasil (E7, E25, E26, Tabel 3, Tabel 4) | semua angka yang dilaporkan ditemukan; yang tidak ditemukan hanya baris skala log1p (tidak dipakai naskah) dan satu CI acuan E26 yang memang tidak dilaporkan |
| 36 DOI di daftar referensi PDF | semua terselesaikan di doi.org; judul dan penulis pertama cocok dengan entri |
| Holm (1979), tanpa DOI | volume 6(2) dan halaman 65 sampai 70 BELUM terverifikasi: JSTOR memblokir, Crossref tidak mengindeksnya |
| Tag E4 (`e4-prereg-2026-09-29`) | memuat protokol, seed, kode split dan model HANFIS; TIDAK memuat `flat_anfis_matched.py` (dikomit 2026-09-30 11:58 WIB, 23 menit setelah tag) dan `scripts/e4_run.py` (dikomit 2026-10-01 11:00 WIB, 16 detik sebelum run pertama). Kalimat naskah sudah dibuat persis (koreksi 3 di bawah) |

Tidak ada eksperimen yang perlu dijalankan ulang: semua hasil terkunci, hash cocok, dan tidak ada perbedaan antara kode kerja dan kode yang dipakai hasil terdaftar yang mengubah prediksi (perubahan `e4_run.py` setelah run hanya menambah penyimpanan model dan pencatatan normalisasi).

## 3. Koreksi yang harus diterapkan di Overleaf (pasangan LAMA dan BARU)

Sudah diterapkan di repositori (komit hari ini). Terapkan di Overleaf dengan cari-ganti persis.

### 3.1 Tanda tanya terbalik di halaman 29 (Section 4.3)

LAMA: `(ratio >$1{,}000\times$ in the most extreme case)`
BARU: `(ratio $>1{,}000\times$ in the most extreme case)`

### 3.2 Label hipotesis di Section 4.3

LAMA: `claimed in C1/H2, not as a methodological artefact`
BARU: `claimed in C1 and H2/H3, not as a methodological artefact`

### 3.3 Apa yang dibekukan tag E4 (Section 4.2)

LAMA: `The confirmatory protocol was committed on 30 September 2026 and tagged the same day (tag \texttt{e4-prereg-2026-09-29}, whose name carries the nominal date of the protocol file), and the first confirmatory training run took place on 2 October 2026.`

BARU: `The confirmatory protocol was committed on 30 September 2026 and tagged the same day (tag \texttt{e4-prereg-2026-09-29}, whose name carries the nominal date of the protocol file). The tag covers the protocol, the seed list, the split code and the HANFIS model code. The parameter-matched flat comparator and the training script were committed on 30 September and 1 October 2026, after the tag but before the first confirmatory run on 1 October 2026 (109-asset inventory); the 120-asset run reported here took place on 2 October 2026. Later additions to the training script (saving models, recording the normalisation) do not change its predictions.`

### 3.4 Abstrak melebihi batas

Abstrak PDF sekitar 300 kata (versi repositori 247). Batas yang kita pakai 250. Kalimat yang bisa dipadatkan tanpa menghilangkan angka: "We built ... and we tested whether it earns that complexity against simple baselines" dan kalimat terakhir "On this target HANFIS adds a printable rule base but no accuracy, and the data cannot show whether environmental context helps." Usulan: gabungkan menjadi satu kalimat penutup, hapus "(73.4% and 83.3% fewer)" karena 34 dan 176 lawan 128 dan 1.052 sudah ada.

### 3.5 Pernyataan AI (Methods "Use of AI tools" dan Declarations) masih tidak akurat

Kalimat "All experiments were run by the authors" tidak benar: asisten menjalankan perintah atas arahan dan izin penulis (D2, E25, E26, E27). Peran AI juga lebih luas daripada yang ditulis (menyusun protokol E25 dan E26, menjalankan skrip, ikut menafsirkan hasil, menyusun Results dan Discussion). Kebijakan Springer Nature meminta alat, versi, cakupan, dan tanggung jawab manusia. Naskah draf pengganti ada di memori A-79 dan balasan 7 November; yang masih dibutuhkan dari penulis: versi model yang dipakai dan rentang tanggal. Model yang tercatat di sesi ini: Claude Sonnet 5.5 (sampai 7 November) dan Claude Fable 5.1 (sejak 11 November); sesi sebelum 20 Oktober belum saya periksa.

### 3.6 Gambar 2 (pertumbuhan aturan) memuat teks `2{,}000` mentah

Label "refused (>2{,}000-param budget)" di dalam gambar menampilkan kode LaTeX mentah. Skrip pembuatnya tidak ada di repositori (hanya PDF-nya yang terlacak); perlu dibuat ulang dengan label "2,000".

### 3.7 Referensi baru harus masuk repositori lewat jalur yang sama

Ke-20 referensi baru benar ada (DOI terselesaikan). Tetapi `sn-bibliography.bib` di repositori belum memuatnya. Setelah zip Overleaf diterima, entri bib diambil ulang lewat `scripts/bib_from_doi.py` dan diaudit dengan `audit_bib_dois.py` dan `bib_deep_audit.py` agar metadata (judul, volume, halaman) berasal dari doi.org, bukan dari ingatan.

## 4. Penilaian kematangan untuk Journal of Cloud Computing (0 sampai 100; pertimbangan)

| Aspek | Skor | Arah | Dasar |
|---|---|---|---|
| Strength | 76 | tinggi = kuat | Semua gerbang lolos hari ini; angka naskah terlacak ke berkas hasil; 36 DOI terverifikasi; praregistrasi, OSF, hasil negatif, E25 sampai E27; Literature Review kini tiga lapis dengan 41 referensi; posisi naskah sudah jujur (C5, abstrak, Conclusion). |
| Weakness | 60 | tinggi = lebih parah | Hasil utama negatif dan klaim yang tersisa sempit; pernyataan AI tidak akurat (risiko kepatuhan nyata); abstrak 300 kata; naskah 60 halaman referee (sekitar 12.400 kata badan); dua sumber naskah berbeda; Holm belum terverifikasi; tanda tanya terbalik dan label gambar mentah (sudah diperbaiki di repo, belum di Overleaf). |
| Gap | 48 | tinggi = celah lebih besar | Celah literatur sudah ditutup; yang tersisa: pengujian panel lingkungan butuh luaran yang bergantung pada lingkungan (di luar jangkauan naskah ini), label linguistik variabel antara tidak stabil, dan tidak ada perbandingan maju dengan flat ANFIS. |
| Opportunity | 62 | tinggi = peluang lebih besar | Dengan C5 dan Discussion praktisi, naskah sudah berdiri sebagai protokol dan benchmark; kebijakan jurnal tentang hasil negatif belum dibaca (halaman memblokir pengambilan otomatis), jadi peluang bergantung pada itu. |
| Kesiapan submit | 70 | tinggi = siap | Naik dari 58 (7 November). Ditahan oleh: pernyataan AI, abstrak, sinkronisasi Overleaf dengan repositori, bib baru lewat doi.org, Holm, gambar 2, dan pembacaan utuh oleh penulis. |

Urutan yang saya sarankan: (1) unduh zip Overleaf dan satukan dengan repositori; (2) terapkan 3.1 sampai 3.3; (3) perbaiki pernyataan AI setelah versi dan tanggal diberikan; (4) padatkan abstrak; (5) bib baru lewat `bib_from_doi.py` dan audit; (6) gambar 2; (7) Holm lewat JSTOR di browser; (8) baca ulang utuh; (9) Zenodo versi baru dengan Additional file 1 dan hasil E25 sampai E27.

## 5. Status sore 11 November (setelah zip Overleaf diterima)

- Zip `2026_11_07_HIBAH_KEPAKARAN_HAFIZ___ANFIS.zip` disatukan ke repositori (`Patch/apply_overleaf_merge_2026-11-11.py`). Mulai sekarang `manuscript/sn-article.tex` dan `sn-bibliography.bib` di repositori adalah satu-satunya sumber; Overleaf diperbarui dengan mengunggah kedua berkas itu dari repositori.
- Koreksi 3.1 sampai 3.3 sudah ada di repositori di atas teks Overleaf. 3.4 (abstrak 248 kata), 3.5 (pernyataan AI dengan versi model), dan kalimat H3 tentang plateau sudah diterapkan (`Patch/apply_abstract_conclusion_ai_2026-11-11.py`). 3.7 selesai: 42 entri diaudit, 35 OK, 6 tanpa DOI, 1 PERIKSA hanya karena tanggal rekaman IEEE Xplore. Holm (1979) 6(2):65-70 diverifikasi dari JSTOR.
- Masih terbuka: 3.6 (Figure 2, skrip pembuat tidak ada), periode penggunaan AI ("during 2026") perlu dikonfirmasi penulis, pembacaan utuh oleh penulis.
- PDF hasil: `docs/progress/sn-article_2026-11-11.pdf` (61 halaman). Audit bib: `docs/progress/bib_audit_overleaf_2026-11-11.csv`.

---
Dokumen ini disusun dengan bantuan asisten AI (Claude, Anthropic) dari pemeriksaan repositori dan PDF pada 11 November 2026.

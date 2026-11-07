# Pencocokan dokumen pembanding (berkas 07) dengan progres eksperimen dan repositori

Disusun 7 November 2026 di sesi repositori (akses ke berkas, log, dan protokol beku). Berkas 07 ditulis di aplikasi Claude tanpa akses ke repositori, jadi sebagian klaimnya belum dicek di sana. Di sini tiap butir dicek ke berkas aslinya. Skor dan "kesiapan" adalah pertimbangan, bukan pengukuran. Empat paper pembanding tidak ada di repositori, jadi tabel pola penulisan di bagian 1 berkas 07 tidak saya verifikasi.

## 1. Hasil verifikasi per butir

| Butir berkas 07 | Terverifikasi di repositori? | Bukti | Penyesuaian |
|---|---|---|---|
| 2.1 H2 dan H3 | Sebagian. Naskah tidak bertentangan dengan protokol beku, tetapi ambigu | `protocols/E4_preregistration_2026-09-29.md` baris 22 menamai perbandingan terhadap FlatANFISMatched "H2/H3" (non-inferioritas, batas bawah CI 95% di atas -0,05), dan keluarga Holm adalah {H1a, H1b, H1c, H2}. Tabel 4 dan teks naskah menulis "H2". Section 1 mendefinisikan H2 (efisiensi komputasi) dan H3 (preservasi performa) terpisah | Tulis "H2/H3" untuk perbandingan matched di Tabel 4, subbagian 4.3, 4.5, dan Conclusion, sama persis dengan protokol. Tambahkan satu kalimat di Section 1: protokol beku menguji H2 dan H3 bersama lewat skill terhadap FlatANFISMatched, dan bagian komputasi H2 dibahas terpisah. Kata hipotesis H1a sampai H5 tidak berubah |
| 2.2 C2 dan H2: pengukuran komputasi | Ya, klaimnya tidak punya bukti | Introduction (kalimat edge), C2, dan definisi H2 menjanjikan durasi latih, memori puncak, throughput, latensi. Naskah hanya punya jumlah aturan dan parameter (Tabel 1). Di repo hanya ada waktu dinding per fold untuk semua model sekaligus (`results_python/e4bis_120/meta_20261002T103905Z.json`, `fold_times_sec`: 40,1; 58,8; 119,0; 116,7; 140,2 detik) dan `time_sec` per run E5. Tidak ada waktu per model, memori, latensi, atau throughput | Opsi A di berkas 07 (cukup baca log) tidak cukup. Dua jalan: B (persempit klaim, tanpa eksperimen) atau C (pengukuran kecil, lihat bagian 3) |
| 2.3 H4 | Ya | `H4` hanya muncul sekali di naskah (definisi, `sn-article.tex` baris 191), tidak ada di protokol E4 dan E7, dan tidak ada di memori proyek | Satu kalimat "H4 was not tested as stated; E9 removes x2 and x7 together" di 4.8 atau Limitations, dan boleh diturunkan ke pekerjaan lanjutan seperti H5. Tidak perlu eksperimen |
| 2.4 angka 981 baris | Ya | Kalimat ada di `sn-article.tex` baris 554. Satu-satunya berkas paritas adalah `results_python/e5_e4_parity_20261001T061220Z.csv` dari inventaris 109 aset (A-26: 0 dari 981 baris tidak cocok, r = 0,9984). Tidak ada berkas paritas untuk 120 aset (1.080 baris uji) | Tulis "on the 109-asset inventory" atau hapus angkanya. Mengulang paritas pada 120 aset opsional dan murah |
| 2.5 hal kecil | Ya, semuanya | Abstrak "6,357 asset-weeks" adalah baris berlabel dari 6.833 (rasio 0,930); keyword "Nonlinear Risk Mitigation"; rujukan diri "Section 4.3's baseline table above"; subbagian 2.1 tanpa `\cite`; `manuscript/sn-bibliography.bib` tidak berisi Chiu (subtractive clustering), Adam, gradient boosting, maupun Kendall | Perbaikan teks. Sitasi baru diambil lewat `scripts/bib_from_doi.py`, tidak dari ingatan |
| Butir 3 dan 4 (basis aturan dan permukaan respons "belum dibuat") | Tidak sepenuhnya. Ada kekeliruan di berkas 07 | `scripts/e4_pdp.py` dan gambar jadi sudah ada di `manuscript/figures/e4bis_pdp` (fold 0) dan `e4bis_pdp_fold1`: PDP satu masukan 7 panel dan permukaan respons, dari 5 seed model asli (forward pass, bukan rekonstruksi). Permukaannya untuk pasangan `kubernetes_exposure` dan `asset_criticality`, bukan (x2, x7). Folder itu tidak terlacak git dan tidak dipakai naskah. 25 model tersimpan ada (`results_python/e4bis_120_models/models`) | Permukaan (x2, x7) bisa dibuat tanpa pelatihan ulang karena skrip menerima `--pair`. Tabel 34 aturan belum ada alatnya: `SugenoANFIS` hanya punya `rule_count`, dan skrip PDP sengaja tidak merekonstruksi aritmetika dari state_dict karena hasilnya bisa tampak benar tetapi salah |

## 2. Yang benar di berkas 07 dan sudah sejalan dengan progres

- Kekuatan metodologi (praregistrasi, OSF, tag beku, bootstrap berkluster, Holm, hasil negatif, SHA-256) sesuai dengan bukti di repositori.
- Posisi "paper protokol dan benchmark" sejalan dengan keputusan 3 November: judul tetap, nilai HANFIS pada struktur, bukan akurasi (skenario A).
- Literature Review memang tipis: `sn-bibliography.bib` berisi 20 entri, dan enam di antaranya web atau perangkat lunak tanpa DOI (audit 4 November).
- Limitations dan pemisahan telemetri dari masukan model sudah selesai (A-80).

## 3. Eksperimen: apa yang berubah dari jawaban saya kemarin

Kemarin saya menyatakan tidak ada eksperimen yang tersisa. Itu masih benar untuk E7 dan semua hipotesis terdaftar. Berkas 07 menemukan celah lain: C2 dan H2 menjanjikan pengukuran komputasi yang tidak pernah dilakukan. Pilihannya adalah keputusan Anda:

| Opsi | Isi | Biaya | Risiko dan aturan |
|---|---|---|---|
| B. Persempit klaim | C2, kalimat Introduction, dan H2 menyatakan "jumlah aturan dan parameter (Tabel 1)"; waktu latih, memori, latensi tidak diukur dan menjadi pekerjaan lanjutan | Hanya teks | Paling aman dan jujur; C2 menjadi kontribusi yang lebih kecil. Konsisten dengan A-63 |
| C. Pengukuran kecil, deskriptif | Waktu latih per model, memori puncak, latensi dan throughput inferensi untuk HANFIS, FlatANFISMatched, dan flat penuh pada data dan seed yang sama; tanpa uji, tanpa keputusan. Dijalankan dari kode beku; protokolnya ditulis dan dikomit lebih dulu | Sekitar setengah hari kerja; lapisan pipeline data dan dokumen baru `protocols/` | Tidak menyentuh label atau hasil E7, tetapi tetap harus dinyatakan tidak terdaftar dan deskriptif. Bila flat ANFIS ternyata lebih cepat, hasilnya tetap dilaporkan. Tidak boleh dipakai untuk menyetel apa pun |

Eksperimen opsional lain, semuanya tanpa pelatihan ulang dan deskriptif:
- Permukaan respons r terhadap (x2, x7) dari lima seed dengan `scripts/e4_pdp.py --pair exploitability threat_intelligence`, memakai model tersimpan.
- Paritas k=1 pada 120 aset, bila ingin mempertahankan angka kesepadanan di 4.4.

## 4. Penyesuaian yang perlu dilakukan, per lapisan dan dokumen (pagar P1)

| Penyesuaian | Lapisan | Dokumen yang berubah | Eksperimen? |
|---|---|---|---|
| Label H2/H3 + satu kalimat Section 1 | Naskah (pelaporan) | `manuscript/sn-article.tex` | Tidak |
| H4 tidak diuji | Naskah | `sn-article.tex` | Tidak |
| 981 menjadi "109-asset inventory" | Naskah | `sn-article.tex` | Tidak (paritas 120 aset opsional) |
| Abstrak "labelled asset-weeks", keyword, rujukan diri 4.3, `\cite` di 2.1 | Naskah | `sn-article.tex` | Tidak |
| Klaim komputasi (B) atau tabel komputasi (C) | Naskah, bila C: pipeline data dan prosedur mutu | `sn-article.tex`; bila C: `protocols/E25_...md` baru, skrip baru, `additional_file_1.tex` | Hanya pada C |
| Literature Review tiga lapis (15 sampai 25 referensi) | Naskah | `sn-article.tex`, `sn-bibliography.bib` | Tidak; setiap referensi lewat `scripts/bib_from_doi.py` dan diaudit |
| Kontras rujukan pada C1 sampai C4, paragraf peta isi | Naskah | `sn-article.tex` | Tidak |
| Tabel hiperparameter beku | Naskah | `additional_file_1.tex` | Tidak (isi dari 4.2, A-09, A-16) |
| Permukaan (x2, x7) dan pelacakan folder `manuscript/figures` | Naskah | `additional_file_1.tex`, git | Tidak, tetapi jalankan skrip PDP |
| Tabel 34 aturan | Naskah | `additional_file_1.tex` | Tidak, tetapi butuh kode ekstraksi yang diuji terhadap forward pass model |
| Paragraf "apa yang dipakai praktisi" di Discussion | Naskah | `sn-article.tex` | Tidak |

Klaim yang tidak boleh dimunculkan lewat Literature Review baru (pagar P11): HANFIS sebagai istilah baru, edge atau Jetson, policy enforcement, overhead kausal observabilitas, DMM, penjelasan berlapis. Tinjauan harus tetap menyatakan bahwa Soozanchi dkk. (2010) lebih dulu memakai nama HANFIS.

## 5. Urutan kerja yang disesuaikan

1. Putuskan klaim komputasi (B atau C). Ini menentukan teks di Section 1, C2, Tabel 4, 4.3, dan Conclusion.
2. Perbaikan konsistensi naskah dalam satu skrip teks-persis: H2/H3, H4, 981, abstrak, keyword, rujukan diri 4.3, `\cite` di 2.1.
3. Literature Review dan kontras kontribusi: kumpulkan DOI kandidat dulu, ambil metadata lewat `bib_from_doi.py`, baru tulis.
4. Additional file 1: tabel hiperparameter, permukaan (x2, x7), pelacakan `manuscript/figures`; tabel aturan hanya bila kode ekstraksinya teruji.
5. Paragraf praktisi di Discussion.
6. Baca ulang manusia, kebijakan AI Springer, volume dan halaman Holm, Overfull baris 407, Zenodo (ditunda).

Tenggat tetap 5 Desember (28 hari dari 7 November). Aturan yang berlaku: tidak ada analisis tambahan atas hasil E7, tidak ada penyetelan, analisis baru ditandai post hoc atau tidak terdaftar, perubahan naskah lewat skrip teks-persis yang gagal-tertutup dan diuji di salinan.

---
Dokumen ini disusun dengan bantuan asisten AI (Claude, Anthropic) dari pemeriksaan repositori pada 7 November 2026. Bukti diambil dari berkas dan keluaran terminal yang disebut; hal yang tidak diperiksa ditandai.

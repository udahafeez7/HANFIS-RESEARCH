# HANFIS: paket serah terima untuk aplikasi Claude (3 November 2026)

Paket ini berdiri sendiri. Aplikasi Claude tidak punya akses ke mesin atau repositori Anda, jadi ia hanya bisa membantu menafsirkan, menulis, dan memeriksa dari berkas yang Anda unggah atau tempel. Ia tidak bisa menjalankan skrip, mengomit, atau menyentuh data.

## Isi paket

| Berkas | Isi |
|---|---|
| `01_status_naskah.md` | Posisi naskah: ukuran, perubahan hari ini, hash, struktur bagian |
| `02_teks_inti_naskah.md` | Judul, abstrak, kontribusi C1 sampai C4, hipotesis, Discussion dan Conclusion (kutipan verbatim) |
| `03_hasil_E7_dan_aturan_klaim.md` | Hasil resmi evaluasi maju E7, istilah baku, klaim yang boleh dan tidak boleh |
| `04_additional_file_1_indeks.md` | Isi Additional file 1 (tabel, gambar, catatan suplemen) dan peta pemindahan |
| `05_tugas_terbuka_dan_jadwal.md` | Daftar kerja sampai kirim, urutan, tenggat |
| `06_aturan_menulis_dan_risiko_penelaah.md` | Aturan gaya, aturan perubahan naskah, pertanyaan yang mungkin diajukan penelaah |

Folder ini sudah memuat `sn-article_2026-11-03.pdf` dan `additional_file_1_2026-11-03.pdf` (salinan PDF naskah saat ini); unggah keduanya bila ingin Claude membaca naskah utuh. Berkas `.tex` boleh diunggah, tetapi jangan minta Claude menyunting `.tex` langsung: perubahan naskah di repositori memakai skrip teks-persis (lihat berkas 06).

## Prompt pembuka (tempel sebagai pesan pertama)

```text
Kamu membantu saya menyiapkan naskah Q1 untuk Springer Journal of Cloud Computing (kirim paling lambat 5 Desember 2026). Baca semua berkas markdown yang saya unggah, mulai dari 00 sampai 06. Kamu tidak punya akses ke mesin atau repositori saya; bantu hanya dari berkas dan teks yang saya tempel. Aturan keras: hasil negatif dilaporkan apa adanya; jangan menyarankan analisis tambahan atau penyetelan setelah hasil E7 terlihat; jangan melonggarkan ambang; analisis post hoc harus ditandai post hoc; jangan menulis sitasi dari ingatan (metadata referensi saya ambil dari doi.org). Jawab dalam bahasa Indonesia, istilah teknis tetap bahasa Inggris, teks naskah dalam bahasa Inggris. Kalimat pertama menjawab pertanyaan; tanpa pembuka dan penutup basa-basi.
```

## Posisi satu paragraf

Evaluasi maju E7 sudah dijalankan sekali pada 2 November 2026 dan hasilnya terkunci (tag `e7-results-2026-11-02`). Hasilnya: HANFIS tidak lebih baik daripada persistence (P7a didukung) maupun rumus empat parameter (P7f didukung); rumus mengalahkan persistence (P7e terkonfirmasi). Naskah sudah memuat hasil itu (skenario A dari templat 14 Oktober), diperpendek dari 58 ke 48 halaman format referee, dan memiliki satu berkas tambahan (Additional file 1).


---
Dokumen ini disusun dengan bantuan asisten AI (Claude, Anthropic) dari berkas repositori dan keluaran terminal sesi kerja 2 sampai 3 November 2026. Angka dan kutipan naskah diambil langsung dari berkas; pertimbangan ditandai sebagai pertimbangan.

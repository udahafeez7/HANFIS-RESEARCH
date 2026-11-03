# Tugas terbuka dan jadwal sampai kirim

Tenggat kerja: kirim paling lambat 5 Desember 2026 (32 hari dari 3 November). Pertimbangan penyusun: urutan di bawah mengurangi risiko, bukan aturan jurnal.

## Sebelum menulis ulang apa pun

1. **Baca ulang naskah utuh** (`sn-article.pdf`, 48 halaman). Suntingan hari ini otomatis; hanya angka dan sitasi yang diperiksa mesin. Catat kalimat yang janggal, lalu kirim sebagai pasangan teks lama dan baru.
2. Prometheus: pemeriksa kesehatan sudah terpasang sebagai timer systemd tingkat pengguna (tanpa sudo) dan melapor `PROM_OK targets=2`. Tidak memengaruhi naskah.

## Pekerjaan naskah

| Urutan | Tugas | Catatan |
|---|---|---|
| 1 | Baca ulang naskah, terutama ringkasan Results hasil pemangkasan | Pemindaian mesin sudah dilakukan; pembacaan manusia belum |
| 2 | Cocokkan kebijakan AI Springer Nature | Pernyataan ada di Methods ("Use of AI tools") dan Declarations |
| 3 | Zenodo versi baru (Additional file 1, keluaran D2, tabel v3, bundel Trivy) | DITUNDA atas keputusan peneliti (3 November). Setelah terbit, ganti kalimat Availability dan kalimat DOI di subbagian hasil E7 |
| 4 | Audit bibliografi | `scripts/audit_bib_dois.py` dan `scripts/bib_deep_audit.py`; jangan menulis sitasi dari ingatan |
| 5 | Periksa setiap angka abstrak terhadap tabel badan | Sembilan tabel sumber masih di badan; periksa ulang setelah suntingan akhir |
| 6 | Peringatan Overfull baris 407 | Belum diperiksa asalnya |
| 7 | Persetujuan ko-penulis tertulis | Saat ini hanya lisan; satu pesan singkat dari Dr. Derisma dan Dr. Budi cukup sebagai catatan |
| 8 | Siapkan paket submit: naskah `.tex` tunggal, gambar, Additional file 1 terpisah, cover letter | Cover letter ditulis setelah naskah final |

## Pekerjaan non-naskah yang masih terbuka

- Prometheus v4.1 sudah berjalan (2/2 target naik sejak 3 November 09.22 WIB). Celah rekaman 16 Oktober 17.00 sampai 3 November 09.22 tetap ada di data.
- Jeda Windows Update sudah diperpanjang oleh peneliti.
- Dugaan penyebab kegagalan transfer HANFIS (pergantian model EPSS) belum diuji. Pengujiannya akan post hoc dan tidak boleh mengubah keputusan terdaftar; bila dilakukan, tulis sebagai post hoc.

## Aturan perubahan sampai kirim

- Tidak ada analisis tambahan atau penyetelan atas hasil E7. Tidak ada `--today`, tidak ada `--redo` untuk `evaluate` dan `formula`.
- Berkas beku E7 (23 berkas, tag `e7-prereg-2026-10-12`) tidak boleh diubah; cacat berarti amendemen bernomor.
- Setiap perubahan naskah yang dikomit lewat skrip teks-persis gagal-tertutup, diuji di salinan, dengan pemeriksaan `\cite`, `\ref`, `\label`, rumus, dan angka.


---
Dokumen ini disusun dengan bantuan asisten AI (Claude, Anthropic) dari berkas repositori dan keluaran terminal sesi kerja 2 sampai 3 November 2026. Angka dan kutipan naskah diambil langsung dari berkas; pertimbangan ditandai sebagai pertimbangan.

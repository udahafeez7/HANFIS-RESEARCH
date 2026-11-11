# Zenodo versi 2: apa yang perlu dilakukan (11 November 2026)

## Mengapa perlu versi 2

Isi versi 1 (`10.5281/zenodo.23357118`, terbit 14 Oktober) diperiksa lewat API Zenodo dan `git ls-tree 534de7d`:

| Ada di v1 | Tidak ada di v1 |
|---|---|
| Kode dan protokol (komit `534de7d`) | 25 model tersimpan E4-bis (dasar E6, E8, E9, E26, E27) |
| 116 berkas bukti Trivy | Keluaran evaluasi maju E7 (D2, 2 November) |
| Manifes snapshot EPSS/KEV | Berkas snapshot EPSS/KEV bersegel itu sendiri |
| Lima model akhir E7 (`.pt`) | Hasil E25, E26, E27 dan Additional file 1 |

Kalimat Availability di naskah ("frozen model files ... are archived at Zenodo") karena itu hanya benar sebagian.

## Paket yang sudah disiapkan (lokal, belum diunggah)

Folder: `C:\Users\moham\Downloads\zenodo_v2_2026-11-11\`

| Berkas | Ukuran | Isi |
|---|---|---|
| `HANFIS-RESEARCH_4d82bea_code.zip` | 15 MB | Kode, protokol, naskah, Patch, memori pada komit `4d82bea` |
| `HANFIS_results_models_2026-11-11.tar.gz` | 132 KB | 25 model E4-bis, meta dan prediksi E4-bis, keluaran E7 dan log D2, model akhir E7, hasil E25, E26, E27 (77 berkas, 30 `.pt`) |
| `HANFIS_sealed_epss_kev_snapshots.tar.gz` | 136 MB | 57 snapshot EPSS mingguan, katalog KEV, manifes SHA-256 |
| `Additional_file_1.pdf` | 528 KB | Additional file 1 versi 11 November |
| `SHA256SUMS.txt` | | Hash keempat berkas |

Tidak ikut: `data/evidence/` (4,0 GB, termasuk pindaian ulang D2). Bisa ditambahkan sebagai berkas terpisah bila Anda mau; unggahan akan lama.

Satu hal yang perlu Anda cek sebelum unggah: ketentuan redistribusi data EPSS dari FIRST. KEV dari CISA adalah data publik pemerintah AS. Bila EPSS tidak boleh didistribusikan ulang, hapus berkas snapshot dari unggahan dan biarkan manifes hash (sudah ada di zip kode) sebagai bukti.

## Langkah di Zenodo

1. Masuk ke https://zenodo.org, buka rekaman `10.5281/zenodo.23357118`.
2. Klik **New version**. Zenodo menyalin metadata v1.
3. Di bagian Files: hapus `HANFIS-RESEARCH_534de7d.zip` dari draf versi baru (berkas v1 tetap ada di v1), lalu unggah keempat berkas dari folder di atas beserta `SHA256SUMS.txt`.
4. **Reserve DOI**: klik tombol "Get a DOI now!" atau "Reserve DOI". Salin DOI-nya dan kirim ke saya; DOI itu masuk ke naskah sebelum Anda menekan Publish.
5. Metadata:
   - Version: `v2.0`
   - Publication date: tanggal publish
   - Description: tambahkan satu paragraf: "Version 2 adds the 25 saved E4-bis models, the outputs of the pre-registered forward evaluation run on 2 November 2026 (tag e7-results-2026-11-02), the sealed weekly EPSS and KEV snapshots, the results of the unregistered computational-cost measurement and the post hoc threat-intelligence ablation and rule documentation (E25 to E27), and Additional file 1 of the manuscript."
   - Related identifiers: biarkan OSF `10.17605/OSF.IO/AHCVS` (references); tambahkan `10.5281/zenodo.23357118` dengan relasi "is new version of" bila Zenodo tidak menambahkannya otomatis.
6. Jangan tekan **Publish** dulu. Berkas Zenodo tidak bisa diubah setelah publish.
7. Kirim DOI hasil reservasi. Saya perbarui pernyataan Availability dan Code availability lewat skrip, Anda baca, lalu Anda tekan Publish.

## Keputusan yang masih Anda pegang

Repositori GitHub: telaah jurnal ini satu arah (penelaah anonim, penulis diketahui), jadi tidak ada alasan menutup kode. Pilihan:
- buka publik saat kirim dan hapus "(private during review)", atau
- tetap privat dan tulis "public on acceptance".

Dengan Zenodo v2 berisi kode dan model, penelaah sudah bisa memeriksa semuanya meski repo tetap privat.

---
Disusun dengan bantuan asisten AI (Claude, Anthropic) dari pemeriksaan API Zenodo dan repositori pada 11 November 2026.

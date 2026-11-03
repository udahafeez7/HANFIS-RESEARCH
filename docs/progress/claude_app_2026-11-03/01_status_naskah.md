# Status naskah (3 November 2026)

HEAD repositori `2886cb1`, cabang `research/amend-a02-a06`, memori proyek v2.57 (amendemen A-77). Tag penting: `e7-prereg-2026-10-12` (komit `dbed812`, 23 berkas beku), `e7-results-2026-11-02`, `progress-seal-2026-11-03`, `progress-seal-2026-11-03b`.

## Ukuran

| Ukuran | Sebelum pemangkasan | Sekarang |
|---|---|---|
| Kata badan (penghitung kasar, tanpa tabel, gambar, referensi) | 13.100 | sekitar 10.950 |
| Abstrak | 246 | sekitar 248 kata (batas 250) |
| Tabel di badan | 18 | 10 |
| Gambar di badan | 5 | 3 (dua lama, satu diagram struktur HANFIS baru) |
| Halaman naskah (format `referee`, spasi ganda, nomor baris) | 58 | 48 |
| Additional file 1 | tidak ada | 13 halaman |

Kata badan dihitung dengan penghitung kasar yang sama sebelum dan sesudah; bukan hitungan resmi jurnal.

## Perubahan 2 sampai 3 November (urut waktu)

1. 35 suntingan keterbacaan (`apply_prose_edits_4.py`): kalimat terpanjang dipecah, tanpa mengubah angka, `\cite`, `\ref`, rumus.
2. `manuscript/sn-basic.bst` kini terlacak git.
3. Subbagian hasil E7 baru ("Prospective evaluation (E7): forward results", Tabel 18 pada versi sebelum pemangkasan) dari templat skenario A; kalimat "results will be added to a later version" diganti.
4. Bingkai: judul tetap; abstrak, Discussion, Conclusion memuat kalimat skenario A apa adanya; C1 sampai C3 tetap; C4 diperluas ke evaluasi maju; H2 tetap.
5. Suntingan gaya tahap 2 (18): tanda pisah, judul subbagian huruf kecil kalimat, empat kata, satu klausa kontras.
6. Pemangkasan: 8 tabel dan 3 gambar dipindah ke Additional file 1; tujuh bagian diringkas dengan teks asli di Supplementary note S1 sampai S7; Introduction, integrasi telemetri, dan Conclusion dipadatkan.
7. Diagram struktur HANFIS (Figure 1, TikZ) disisipkan di subbagian arsitektur.

Setiap perubahan lewat skrip teks-persis gagal-tertutup yang diuji di salinan; invarian angka dan sitasi diperiksa. Dari gabungan naskah dan Additional file 1 tidak ada angka data asli yang hilang. Satu `\cite` dan satu `\ref` hilang bersama narasi yang sengaja dihapus (rinciannya di A-77).

## Hash berkas (sha256)

| Berkas | sha256 |
|---|---|
| `manuscript/sn-article.tex` | `3a1da3e1244cdc284d065a5c1b5bb5b6bb326f9ae523492806aa17b287da2b1b` |
| `manuscript/sn-article.pdf` | `54561f463c881fe0eb49a03e750b92d0466eefc978903ecadca8552cee24f329` |
| `manuscript/additional_file_1.tex` | `b6cb31c14cece62742e8e02d5f69e77d30dd1292ca156147fd48d96f03297f89` |
| `manuscript/additional_file_1.pdf` | `85580c3bebee9c743b279a3db9391f72b35f3a217d7d8108fa9f94163376ae24` |

## Struktur bagian naskah (badan)

- Introduction
- Literature Review
    - ANFIS
- Methodology
    - HANFIS architecture and risk formulation
    - HANFIS architecture, rule count, and parameter complexity
    - Experimental platform and telemetry validation
    - Observability-Overhead Protocol (external-v3.0)
    - Realised exploitability-exposure target and real-world asset-week dataset
    - Integration of validated telemetry with HANFIS
    - Validity safeguards and methodological boundary
    - Prospective evaluation (E7): pre-registered design
    - Use of AI tools
- Results
    - Observability overhead
    - Training configuration
    - Predictive performance
    - Accuracy-complexity curve
    - Ablation and robustness analysis
    - Explanation fidelity (E6)
    - Attribution and monotonicity checks (E8)
    - Label-ingredient ablation and information-minimal baselines (E9--E11)
    - Horizon sweep and feature impact by horizon (E14)
    - Prioritisation utility (E15)
    - Error anatomy and the EPSS model change (E16--E19)
    - Calibration (E21)
    - Prospective evaluation (E7): forward results
- Discussion
    - Limitations
- Conclusion and Future Work

## Yang belum dilakukan atau belum diperiksa

- Naskah belum dibaca ulang utuh oleh peneliti setelah pemangkasan. Ringkasan di Results dibuat otomatis dari teks asli dan hanya diperiksa lewat invarian angka.
- Satu peringatan Overfull 6,05 pt di baris 407; belum diperiksa apakah ada sebelum suntingan.
- Kebijakan AI Springer Nature belum dicocokkan dengan pernyataan di Methods dan Declarations.
- Zenodo versi baru belum terbit; kalimat Availability dan kalimat tentang DOI di subbagian hasil E7 masih menunggu DOI.
- Additional file 1 memakai `xr-hyper`: untuk dikompilasi, naskah harus dikompilasi dulu agar `sn-article.aux` ada. Nomor kutipan di Additional file 1 berbeda dari naskah.


---
Dokumen ini disusun dengan bantuan asisten AI (Claude, Anthropic) dari berkas repositori dan keluaran terminal sesi kerja 2 sampai 3 November 2026. Angka dan kutipan naskah diambil langsung dari berkas; pertimbangan ditandai sebagai pertimbangan.

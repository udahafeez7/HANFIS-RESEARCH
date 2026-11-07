# Status naskah (3 November 2026)

HEAD repositori `d1f6ea1`, cabang `research/amend-a02-a06`, memori proyek v2.62 (amendemen A-82). Tag penting: `e7-prereg-2026-10-12` (komit `dbed812`, 23 berkas beku), `e7-results-2026-11-02`, `progress-seal-2026-11-03` sampai `progress-seal-2026-11-03e` (lima segel hari itu).

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
8. Baca ulang dengan aturan humanizer dan avoid-ai-writing (3 November siang): pemindaian mekanis tidak menemukan kata Tier 1A atau Tier 2, transisi klise, atau tanda pisah. Delapan suntingan diterapkan: "not yet" pada H1b menjadi "not" (tiga tempat, karena P7a juga tidak mendukung H1b), dua penegas "real," dihapus, kalimat E14 tentang evaluasi maju yang "planned" diperbarui ke hasil E7, "cockroachdb is expected to" diperbarui (tidak ada aset yang gugur), dan "evidence for the mechanism" di 4.3 dilunakkan menjadi "suggestive of" agar sejalan dengan Conclusion.
9. Narasi telemetri disesuaikan dengan bukti (3 November sore, 8 suntingan di naskah dan Additional file 1): "telemetry-aware" menjadi "evidence-based", tujuan kedua Methods menjadi "establish which validated runtime measurements ... in future work", kalimat 3.5 dan 3.6 menyatakan bahwa telemetri bukan masukan model dan x5 mengikuti rubrik atas konfigurasi klaster, kalimat 4.1 dan Discussion disesuaikan, simpul akar Figure S1 menjadi "Evidence-based HANFIS methodology".

Setiap perubahan lewat skrip teks-persis gagal-tertutup yang diuji di salinan; invarian angka dan sitasi diperiksa. Dari gabungan naskah dan Additional file 1 tidak ada angka data asli yang hilang. Satu `\cite` dan satu `\ref` hilang bersama narasi yang sengaja dihapus (rinciannya di A-77).

## Hash berkas (sha256)

| Berkas | sha256 |
|---|---|
| `manuscript/sn-article.tex` | `3f7e3fcb3a90be8e81bacd8cea59685830f8e688b436ba2e017ed847452c464f` |
| `manuscript/sn-article.pdf` | `e82db3213b1af0ac43b2ed756beb61912166e1c5453ab7646b73442ceb0c765d` |
| `manuscript/additional_file_1.tex` | `64a7279b83af14f2f748ae72605ba33e371c7d60e2ce6c10461ce8af1850f0b8` |
| `manuscript/additional_file_1.pdf` | `d4eb182c9a0690b160bcdd0335dd9e2708520f49defdb0583ea1a58081b54925` |

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
    - Relation of validated telemetry to HANFIS
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
- Pertentangan telemetri sudah diselesaikan (keputusan peneliti 3 November, opsi A): telemetri runtime bukan masukan model; x4 sampai x6 adalah nilai statis per aset (x5 dan x6 lewat rubrik tertulis, A-30); HANFIS dinarasikan "evidence-based", dan telemetri sebagai sumber x5 adalah hipotesis lanjutan. Dasar: `python_hanfis/asset_weeks.py` baris 361 sampai 363, tabel E7 (x5 konstan per image), README `comparison_20260914_v3`, dan dokumen arsip percakapan 3 November yang menyatakan sendiri bahwa belum ada skrip yang mengubah telemetri Prometheus menjadi tujuh fitur.
- Kalimat di abstrak dan 4.3 yang memakai "significantly" pada hipotesis terdaftar tidak boleh diubah.
- Zenodo versi baru ditunda atas keputusan peneliti; kalimat Availability dan kalimat tentang DOI di subbagian hasil E7 masih menunggu DOI.
- Additional file 1 memakai `xr-hyper`: untuk dikompilasi, naskah harus dikompilasi dulu agar `sn-article.aux` ada. Nomor kutipan di Additional file 1 berbeda dari naskah.


---
Dokumen ini disusun dengan bantuan asisten AI (Claude, Anthropic) dari berkas repositori dan keluaran terminal sesi kerja 2 sampai 3 November 2026. Angka dan kutipan naskah diambil langsung dari berkas; pertimbangan ditandai sebagai pertimbangan.

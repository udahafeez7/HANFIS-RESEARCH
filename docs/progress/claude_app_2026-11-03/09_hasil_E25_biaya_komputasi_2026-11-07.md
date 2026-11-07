# Hasil E25: biaya komputasi HANFIS, FlatANFISMatched, dan flat ANFIS penuh (7 November 2026)

Protokol: `protocols/E25_compute_cost_protocol_2026-11-07.md` (tag `e25-protocol-2026-11-07`, komit `0e4a117`, dibekukan sebelum pengukuran). Pengukuran DESKRIPTIF dan TIDAK TERDAFTAR, dilakukan setelah hasil E7 diketahui, tanpa memakai data E7. Dijalankan satu kali (`--run`, mulai 11.05 WIB, selesai sekitar 11.13 WIB), 45 dari 45 unit, tanpa kegagalan teknis dan tanpa pengulangan.

## Keadaan pengukuran

Mini PC AMD Ryzen 7 255 w/ Radeon 780M Graphics (16 inti logis), WSL 2, Python 3.12.3, torch 2.13.0+cu130, 1 thread, hanya CPU. Komit kode `0e4a117`. Seed 20260928, 600 epoch, 5 fold x 3 ulangan per model. Docker, Kubernetes, dan Prometheus berjalan bersamaan. Berkas mentah: `results_python/e25/raw_20261107T040539Z.csv` (sha256 `cfeb70c9f1c5fe8e`), ringkasan `summary_20261107T040539Z.json` (sha256 `a0f20a7ae7777615`); keduanya diabaikan git.

## Hasil: median (minimum sampai maksimum) atas 15 pengukuran

| Metrik | HANFIS | FlatANFISMatched | Flat ANFIS penuh |
|---|---|---|---|
| Waktu latih (detik) | 8,51 (5,55 sampai 10,23) | 0,95 (0,21 sampai 6,56) | 7,30 (0,87 sampai 12,06) |
| Kenaikan memori puncak (MiB) | 0,40 (0,10 sampai 0,95) | 194,13 (5,53 sampai 663,48) | 3,83 (0,27 sampai 9,70) |
| Latensi satu baris, median (mikrodetik) | 398,2 (382,4 sampai 467,4) | 49,1 (46,7 sampai 62,4) | 95,6 (91,8 sampai 100,3) |
| Latensi satu baris, persentil 95 (mikrodetik) | 572,2 (524,5 sampai 681,7) | 98,1 (84,8 sampai 199,1) | 157,8 (143,7 sampai 187,9) |
| Throughput batch (baris per detik) | 388.665 (261.727 sampai 423.789) | 2.456.989 (1.208.422 sampai 2.678.173) | 264.865 (252.131 sampai 278.219) |
| Aturan dan parameter | 34 dan 176 | 8 dan 176 | 128 dan 1.052 |

## Pembacaan yang ditetapkan di protokol (HANFIS terhadap flat penuh, median per fold)

| Metrik | Fold tempat HANFIS lebih baik | Pembacaan | Rasio median HANFIS terhadap flat penuh |
|---|---|---|---|
| Waktu latih | 2 dari 5 | tidak didukung | 1,17x |
| Kenaikan memori puncak | 5 dari 5 | didukung secara deskriptif | 0,10x |
| Latensi satu baris (median) | 0 dari 5 | tidak didukung | 4,17x |
| Latensi satu baris (persentil 95) | 0 dari 5 | tidak didukung | 3,63x |
| Throughput batch | 5 dari 5 | didukung secara deskriptif | 1,47x |

Terhadap FlatANFISMatched hasil hanya dilaporkan (parameternya dipasangkan secara desain): HANFIS membutuhkan waktu latih sekitar 9 kali lebih lama (median 8,51 lawan 0,95 detik), latensi satu baris sekitar 8 kali lebih tinggi, dan throughput batch sekitar seperenam. Sebaliknya, kenaikan memori FlatANFISMatched jauh lebih besar dan tumbuh dengan jumlah baris latih (5,5 sampai 663 MiB dari fold 0 ke fold 4), kemungkinan besar karena pencarian radius klaster yang membangun matriks jarak antarbaris; HANFIS 0,1 sampai 0,9 MiB.

## Median per fold

Waktu latih (detik):

| Fold | HANFIS | FlatANFISMatched | Flat ANFIS penuh |
|---|---|---|---|
| 0 | 5,71 | 0,23 | 0,87 |
| 1 | 7,66 | 0,57 | 2,17 |
| 2 | 9,43 | 0,95 | 11,03 |
| 3 | 8,42 | 2,71 | 7,30 |
| 4 | 10,09 | 6,37 | 12,06 |

Kenaikan memori puncak (MiB):

| Fold | HANFIS | FlatANFISMatched | Flat ANFIS penuh |
|---|---|---|---|
| 0 | 0,11 | 5,56 | 0,27 |
| 1 | 0,25 | 66,75 | 2,48 |
| 2 | 0,46 | 194,13 | 4,99 |
| 3 | 0,85 | 390,17 | 8,20 |
| 4 | 0,72 | 663,46 | 6,72 |

Latensi satu baris, median (mikrodetik):

| Fold | HANFIS | FlatANFISMatched | Flat ANFIS penuh |
|---|---|---|---|
| 0 | 395,3 | 47,1 | 92,5 |
| 1 | 387,6 | 49,1 | 94,1 |
| 2 | 402,1 | 50,0 | 96,4 |
| 3 | 398,2 | 53,8 | 95,6 |
| 4 | 424,2 | 47,3 | 97,1 |

## Arti hasilnya (pertimbangan penyusun, bukan pengukuran)

- Yang didukung: HANFIS memakai 6 kali lebih sedikit parameter dan 3,8 kali lebih sedikit aturan daripada flat penuh, memori puncak pelatihan sekitar sepersepuluh, dan throughput batch 1,5 kali lebih tinggi.
- Yang TIDAK didukung: waktu latih HANFIS tidak lebih rendah (median 17% lebih lama daripada flat penuh, lebih rendah hanya pada 2 dari 5 fold), dan latensi satu baris sekitar 4 kali lebih tinggi daripada flat penuh. Klaim di H2 bahwa HANFIS "will reduce training time ... and inference latency" jadi tidak terpenuhi pada ukuran ini.
- Jadi C2 ("computational optimization strategy") terdukung untuk jumlah aturan dan parameter, memori, dan throughput batch, tetapi tidak untuk waktu latih dan latensi satu baris.

## Batas pembacaan

- Satu seed (20260928). Waktu latih mencakup 3 restart HANFIS, sedangkan flat penuh dilatih satu kali dengan patience 60; jumlah epoch yang sungguh berjalan berbeda karena penghentian dini, jadi selisih waktu latih tidak murni soal arsitektur.
- Latensi satu baris mengukur `predict` seperti yang dipakai pipeline, termasuk konversi numpy ke torch dan tiga lintasan panel HANFIS di PyTorch tanpa optimasi. Ini sifat implementasi, bukan batas teoretis.
- Kenaikan memori diukur sebagai selisih penanda puncak resident set proses setelah pemanasan; resolusi sekitar 1 MiB dan tingkat proses.
- Mesin satu kelas (mini PC WSL 2), bukan edge atau produksi; tidak ada klaim tentang Jetson. Tanpa uji statistik atau selang kepercayaan, sesuai protokol.

---
Dokumen ini disusun dengan bantuan asisten AI (Claude, Anthropic) dari berkas hasil E25; angka dihitung langsung dari `summary_20261107T040539Z.json` dan `raw_20261107T040539Z.csv`.

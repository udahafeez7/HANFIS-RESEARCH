# Hasil E26 dan E27, dan verifikasi audit klaim berlebih (7 November 2026)

Protokol: `protocols/E26_h4_and_documentation_protocol_2026-11-07.md` (tag `e26-protocol-2026-11-07`, komit `a632437`, dibekukan sebelum E26 nyata). Semua POST HOC, DESKRIPTIF, TIDAK TERDAFTAR, dilakukan setelah hasil E7 diketahui, tanpa data E7 (data E4-bis out-of-fold, 1.080 baris). Tidak ada keputusan terdaftar yang berubah. E26 dijalankan satu kali (mulai 11.20 WIB), tanpa kegagalan teknis dan tanpa pengulangan.

## 1. E26: HANFIS tanpa x7 (indikator KEV) saja

Prosedur sama dengan E9, hanya x7 yang diganti konstanta 0 (latih dan uji); lima seed beku, 3 restart, 600 epoch. Fold identik dengan prediksi E4-bis; CVSS-saja dan persistence yang dihitung ulang cocok dengan berkas itu (selisih 8,9e-16 dan 0). Skill score SS = 1 - MSE_a / MSE_b, CI 95% bootstrap berkelompok per image (2.000 resampel).

| Pasangan | SS | CI 95% | MSE |
|---|---|---|---|
| HANFIS tanpa x7 terhadap HANFIS penuh (pasangan utama) | -6,738 | [-13,958; -2,899] | 3,16 lawan 0,41 |
| HANFIS tanpa x7 terhadap persistence | -6,625 | [-19,375; -2,492] | 3,16 lawan 0,41 |
| HANFIS tanpa x7 terhadap CVSS-saja | +0,748 | [+0,605; +0,856] | 3,16 lawan 12,54 |
| Acuan: HANFIS penuh terhadap persistence | +0,015 | [-0,702; +0,250] | 0,41 lawan 0,41 |
| Acuan: HANFIS penuh terhadap CVSS-saja | +0,967 | [+0,952; +0,980] | 0,41 lawan 12,54 |

Metrik peringkat mingguan (definisi E15, 45 minggu dengan sekurang-kurangnya 15 aset). Rerata Spearman dan presisi pada 20% teratas: HANFIS tanpa x7 0,889 dan 0,716; HANFIS penuh 0,969 dan 0,973; persistence 0,992 dan 0,969. Selisih berpasangan (bootstrap minggu, 2.000 resampel):

| Selisih | Spearman | Presisi pada 20% teratas |
|---|---|---|
| Tanpa x7 dikurangi penuh | -0,080 [-0,089; -0,072] | -0,258 [-0,307; -0,204] |
| Tanpa x7 dikurangi persistence | -0,103 [-0,113; -0,093] | -0,253 [-0,302; -0,204] |
| Penuh dikurangi persistence (acuan) | -0,023 [-0,027; -0,018] | +0,004 [-0,009; +0,018] |

Per fold (SS tanpa x7 terhadap penuh, semuanya negatif):

| Fold | Baris | MSE tanpa x7 | MSE penuh | SS |
|---|---|---|---|---|
| 0 | 225 | 4,996 | 0,328 | -14,21 |
| 1 | 216 | 3,261 | 0,613 | -4,32 |
| 2 | 216 | 1,806 | 0,017 | -103,21 |
| 3 | 216 | 4,840 | 1,043 | -3,64 |
| 4 | 207 | 0,731 | 0,029 | -24,20 |

Pembacaan yang ditetapkan di protokol: "arah H4" terpenuhi bila SS negatif dengan batas atas CI di bawah 0 DAN kedua selisih peringkat negatif dengan batas atas CI di bawah 0. Pada ketiganya batas atas CI berada di bawah 0, jadi arah H4 terpenuhi secara deskriptif. Tanpa x7 MSE naik dari 0,41 menjadi 3,16 (sekitar 7,7 kali), dan semua fold bergerak ke arah yang sama.

Batas pembacaan: x7 adalah indikator KEV, yang juga bahan label. Hasil ini menunjukkan seberapa besar model bergantung pada bahan label, bukan bahwa x7 adalah sinyal ancaman independen. H4 sebagai hipotesis terdaftar tetap tidak diuji; ini hanya jawaban deskriptif dengan prosedur terdekat. Tanpa x7, HANFIS tetap lebih baik daripada CVSS-saja (SS +0,748) tetapi jauh di bawah persistence.

## 2. E27: dokumentasi satu model dan permukaan respons

Model yang ditentukan sebelum melihat apa pun: fold 0, seed 20260928. Tabel 34 aturannya ada di `docs/progress/E27_hanfis_rules_fold0_seed20260928.md` (pusat dan lebar fungsi keanggotaan, konsekuen). Rekonstruksi keluaran tiap panel dari aksesor model cocok dengan forward pass model (selisih maksimum 0 pada 1.000 baris tetap, ambang 1e-5).

Temuan yang harus dilaporkan: fungsi keanggotaan diberi nama menurut indeks (MF1, MF2, MF3), karena pusat Gaussian adalah parameter bebas dan tidak dipaksa mengikuti urutan indeksnya. Pada model yang ditentukan, pusat x2 tidak berurutan ([0,682; 0,282]), begitu pula variabel antara v ([0,352; 0,677; 0,659]) dan e ([0,317; 0,297; 0,484]). Tambahan di luar protokol (membaca parameter, tanpa pelatihan), atas ke-25 model tersimpan: pusat MF berurutan naik pada x1 25 dari 25 model, x2 24, x3 25, x4 25, x5 25, x6 25, x7 20, tetapi hanya pada 8 dari 25 model untuk v dan 17 dari 25 untuk e. Artinya nama "low, medium, high" untuk variabel antara tidak dapat dibaca langsung dari indeks pada sebagian besar model, padahal Section 3.2 membenarkan 3 fungsi keanggotaan pada v dan e justru agar tetap dapat ditafsirkan secara linguistik (A-02).

Permukaan respons r terhadap (x2, x7), lima seed, model asli (`manuscript/figures/e4bis_pdp_x2x7/fig_e4_pdp_surface.pdf`): prediksi naik halus pada kedua masukan, sekitar 1 di sudut (0, 0) dan sekitar 10,5 di sudut (0,1; 1) pada skala 0 sampai 100; kontur mendekati vertikal di tepi kanan rentang x2, jadi respons terhadap x2 menjenuh di dalam rentang teramati. Pembacaan ini dari gambar, bukan dari uji.

Catatan koreksi skrip: `scripts/e27_rules_and_surface.py` yang dibekukan bersama protokol semula memberi label "low, medium, high" menurut indeks. Itu menyesatkan, jadi label diganti menjadi MF1 sampai MF3 dan pemeriksaan keurutan ditambahkan SEBELUM keluaran dipakai. Perubahan itu hanya pada pelabelan dokumentasi, bukan pada eksperimen.

## 3. Verifikasi butir audit klaim berlebih (berkas 10) terhadap repositori

| # | Butir | Status verifikasi | Catatan |
|---|---|---|---|
| 1 | C2 dan H2 | Terverifikasi dan sudah diukur | E25 (A-84): memori dan throughput terdukung, waktu latih dan latensi satu baris tidak |
| 2 | C3 | Terverifikasi | Label di Section 3.5 hanya memakai EPSS, KEV, dan reachability; C3 menyebut MFA, eksposur, dan kekritisan aset |
| 3 | C1 | Terverifikasi | Shapley 3,3% untuk x4 sampai x6 (E8); E27 menambah bahwa MF panel E berurutan, tetapi perannya tetap tidak terbukti |
| 4 | H3 | Terverifikasi | Protokol beku E4 menamai perbandingan matched "H2/H3" (berkas 08) |
| 5 | H4 | Terverifikasi dan sudah dijawab deskriptif | E26: arah H4 terpenuhi secara deskriptif, H4 terdaftar tetap tidak diuji |
| 6 | Fold 0 dan pembanding matched | Angka terverifikasi di naskah (91%; rentang prediksi matched -6,679 sampai 11,059) | Uji sensitivitas jumlah pusat klaster tidak dijalankan: mengubah jumlah pusat mengubah jumlah parameter dan merusak pasangan parameter (protokol E26, bagian 4) |
| 7 | H1a | Terverifikasi | CVSS-saja memakai hanya x1 (`scripts/e4_run.py`) |
| 8 | H1c | Terverifikasi | Ridge-7 SS terhadap persistence -2,293; ridge interaksi x2, x7 mengalahkan HANFIS (E11, -0,529) |
| 9 | "Two further contributions are established" | Terverifikasi | Ablasi E1 pada dua skenario sintetis dan lima seed |
| 10 | "Readable rule base", "documented response surface" | Didukung sebagian setelah E27 | Aturan dan permukaan kini ada, tetapi pusat MF variabel antara tidak berurutan pada sebagian besar model, jadi label linguistik tidak dapat diasumsikan |
| 11 | P7a "supported" | Terverifikasi sebagai risiko pembacaan | Tulis "didukung (HANFIS tidak lebih baik)" |

Hal yang belum diperiksa: Section 1 sebagai kalimat sudah dibaca dari PDF oleh audit, bukan dari berkas `.tex`; penomoran tabel di audit mengikuti PDF 3 November.

## 4. Keluaran dan hash

`results_python/e26/e26_predictions_20261107T042449Z.csv` sha256 `48f118f9e83bd94d`; `e26_summary_20261107T042449Z.json` sha256 `66d95d53ec6c5a05` (keduanya diabaikan git). Tabel aturan: `docs/progress/E27_hanfis_rules_fold0_seed20260928.md`. Gambar permukaan: `manuscript/figures/e4bis_pdp_x2x7/`.

---
Dokumen ini disusun dengan bantuan asisten AI (Claude, Anthropic) dari berkas hasil E26 dan E27; angka dihitung langsung dari `e26_summary_20261107T042449Z.json` dan `e26_predictions_20261107T042449Z.csv`.

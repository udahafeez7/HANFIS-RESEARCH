# Protokol E26: ablasi x7 untuk H4 dan dokumentasi model (post hoc, deskriptif, tidak terdaftar)

Ditulis dan dikomit 7 November 2026, SEBELUM E26 dijalankan. Lapisan (pagar P1): prosedur mutu dan pipeline data. Dokumen: berkas ini, `scripts/e26_x7_ablation.py`, `scripts/e27_rules_and_surface.py`. Tidak ada berkas beku E4 atau E7 yang diubah dan tidak ada data atau hasil E7 yang dipakai; semua memakai data E4-bis (prediksi out-of-fold, 1.080 baris uji).

## 1. Status

- POST HOC, deskriptif, tidak terdaftar di OSF, dilakukan setelah hasil E7 diketahui. Tidak ada keputusan terdaftar (H1a, H1b, H1c, H2/H3, P7a sampai P7f) yang berubah.
- H4 tidak pernah diuji sebagaimana dirumuskan (H4 hanya ada sebagai definisi; tidak ada di protokol E4 maupun E7). E26 menjawabnya hanya secara deskriptif dengan prosedur terdekat. Hasilnya tidak dapat "mengonfirmasi H4" sebagai hipotesis terdaftar.
- Alasan: audit di sesi 7 November (berkas 08 dan audit klaim berlebih) menemukan bahwa H4 tidak diuji dan tidak dinyatakan demikian di naskah. Celah ini ditemukan lewat pembacaan, bukan dari hasil.
- Hasil apa pun dilaporkan apa adanya.

## 2. E26: ablasi x7 saja

Prosedur sama dengan E9 (`scripts/e9_ablation.py`): HANFIS dilatih ulang dengan HANYA masukan x7 (`threat_intelligence`, indikator KEV) diganti konstanta 0 pada data latih dan uji; fold, seed, embargo, pembagian validasi, dan semua hiperparameter identik dengan `scripts/e4_run.py` (diimpor dari sana). Seed beku semua (20260928, 20261005, 20261012, 20261019, 20261026), 3 restart, 600 epoch, patience 100, minimum 200 epoch. "HANFIS penuh" adalah kolom `y_hanfis` di `results_python/e4bis_120_models/predictions_20261005T083407Z.csv`. Skrip memeriksa bahwa fold identik dengan berkas itu dan bahwa CVSS dan persistence yang dihitung ulang cocok dengan kolomnya; bila tidak, ia berhenti.

Metrik:
1. Skill score terkumpul SS = 1 - MSE_a / MSE_b dengan bootstrap berkelompok per image (2.000 resampel, seed 20261107): HANFIS tanpa x7 terhadap HANFIS penuh (pasangan utama), terhadap persistence, dan terhadap CVSS-saja; acuan: HANFIS penuh terhadap persistence dan terhadap CVSS-saja.
2. Metrik peringkat mingguan seperti E15 (`scripts/e15_ranking.py`): korelasi Spearman dan presisi pada 20% teratas, minggu dengan sekurang-kurangnya 15 aset, rerata mingguan, dan selisih berpasangan (tanpa x7 dikurangi penuh) dengan bootstrap minggu (2.000 resampel, seed 20261107).

Pembacaan deskriptif, ditetapkan sebelum pengukuran:
- "Arah H4": SS (tanpa x7 terhadap penuh) bernilai negatif dengan batas atas CI di bawah 0, DAN pada kedua metrik peringkat selisih berpasangan negatif dengan batas atas CI di bawah 0. Bila hanya sebagian terpenuhi, "campuran".
- Bila CI melintasi 0 pada suatu metrik, ditulis "tidak terbukti", bukan "tidak berbeda".
- Bila tanpa x7 lebih baik dengan CI di atas 0, ditulis "arah berlawanan dengan H4".
- Tanpa koreksi multiplisitas; bukan keputusan terdaftar.

## 3. Dokumentasi model (E27), bukan eksperimen

Satu model yang ditentukan sekarang, sebelum melihat apa pun: lipatan 0, seed 20260928 (`results_python/e4bis_120_models/models/fold0_seed20260928_hanfis.pt`, model pertama dalam urutan beku). `scripts/e27_rules_and_surface.py` mencetak ke-34 aturan (pusat dan lebar fungsi keanggotaan, konsekuen) memakai aksesor model sendiri (`rule_indices`, `centers`, `log_sigmas`, `effective_consequents`). Sebelum menulis, skrip memeriksa bahwa rekonstruksi keluaran tiap panel dari aksesor itu sama dengan forward pass model pada 1.000 baris tetap (selisih maksimum harus di bawah 1e-5), dan berhenti bila tidak. Tanpa pelatihan dan tanpa pemilihan data.

Permukaan respons r terhadap (x2, x7): `scripts/e4_pdp.py --pair exploitability threat_intelligence`, lipatan 0, lima seed, model asli (forward pass), tanpa pelatihan. Deskriptif.

## 4. Yang sengaja tidak dikerjakan

Uji sensitivitas FlatANFISMatched dengan jumlah pusat klaster berbeda (usulan audit klaim berlebih, baris 6) tidak dijalankan: mengubah jumlah pusat mengubah jumlah parameter, sehingga model berhenti menjadi pembanding yang dipasangkan parameternya; varian apa pun adalah pembanding baru yang dipilih setelah hasil terlihat. Bila peneliti menginginkannya, protokol terpisah harus menetapkan varian sebelum menjalankan.

## 5. Larangan dan penanganan kegagalan

- Kode beku, hiperparameter, seed, dan jumlah restart tidak diubah. Tidak ada penyetelan.
- E26 nyata dijalankan sekali (`--run`). Hanya kegagalan teknis yang boleh diulang, dengan alasan tercatat; pengulangan karena hasil tidak diinginkan dilarang.
- Satu uji fungsi (`--smoke`: 1 seed, 1 restart, 40 epoch) sudah dijalankan pada 7 November sebelum pembekuan ini; keluarannya dibuang dan tidak dipakai untuk memilih apa pun. Uji itu memperlihatkan bahwa komparator CVSS dan persistence cocok dengan berkas E4-bis dan bahwa kedua skrip berfungsi.
- Bila E26 menunjukkan x7 tidak membantu, atau justru merugikan, hasilnya tetap dilaporkan.

## 6. Batas klaim

- Satu inventaris (120 aset), satu jendela waktu, satu pembagian fold. x7 adalah indikator KEV, yang juga bahan label; hasilnya menggambarkan ketergantungan model pada bahan label, bukan nilai x7 sebagai sinyal ancaman independen.
- Tidak ada klaim tentang H4 sebagai hipotesis terdaftar.
- Dokumentasi aturan menggambarkan satu model, bukan seluruh ensemble 25 model.

## 7. Keluaran

`results_python/e26/e26_predictions_<stempel>.csv`, `e26_summary_<stempel>.json` (diabaikan git; hash dicatat di amendemen memori). `results_python/e27/hanfis_rules_fold0_seed20260928.md`. Gambar permukaan di `manuscript/figures/`.

---
Dokumen ini disusun dengan bantuan asisten AI (Claude, Anthropic) atas permintaan peneliti pada 7 November 2026.

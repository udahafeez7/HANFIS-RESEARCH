# Praregistrasi E4 — HANFIS vs pembanding pada data nyata

Disahkan 2026-09-29. Dibekukan; perubahan berikutnya hanya lewat amendemen bernomor di
`HANFIS_RESEARCH_MEMORY.md`, tidak dengan menyunting berkas ini.

## Keputusan A-13 (final, disahkan setelah dicek terhadap `hanfis_sec33_target_definition.tex`)

1. **Agregasi label**: max_v X_v(τ)·S_{v,a}(τ) — definisi §3.3 itu sendiri, bukan pilihan bebas.
   Noisy-OR dilaporkan sebagai analisis sensitivitas, bukan pengganti.
2. **Skala y**: raw (0–100), sesuai formula `(100/Δ)·Σ...`. log1p dilaporkan penuh sebagai
   sensitivitas kedua.
3. **x₃ Patch Risk**: kontrak v2 `{0,1,2}` — sudah menjadi implementasi berjalan. Skema §2
   (rumus proporsi/usia) akan diamendemen mengikuti ini (tindak lanjut terbuka, tidak
   memblokir E4).
4. **Image 0 CVE tetap dimasukkan** sebagai aset nyata dengan y = 0.

## Hipotesis dan pembanding (terhadap MSE terkumpul, skala raw)

- H1a vs CVSS tunggal: SS_cvss > 0,10, batas bawah CI 95% > 0.
- H1b vs persistence (lag 4 minggu, kausal): SS_pers ≥ SESOI 0,05, batas bawah CI 95% > 0.
- H1c vs ridge 7-masukan: SS_ridge > 0, non-inferioritas batas bawah CI 95% > −0,02.
- H2/H3 vs FlatANFISMatched (±5% parameter): non-inferioritas batas bawah CI 95% > −0,05.
- H2′ vs flat ANFIS penuh: dilaporkan tanpa kriteria (referensi kapasitas).
- Fuzzyfortify: pembanding kualitatif eksternal pada 5 kasus acuan, tidak masuk uji statistik.

## Desain beku

- Data: `data/processed/asset_weeks_v2.csv`, gerbang §9 lolos 2026-09-29 (109 aset, 6.206 baris,
  `--drop-insufficient` mengeluarkan 7 baris `cockroachdb` berbukti tak tuntas).
- Pembagian: `GroupTimeSplit` (A-16), n_splits 5, embargo 30 hari, min_train_weeks 4, seed 20260928.
- Skema pelatihan (A-09, diperbarui menyusul A-19): **`fit_hybrid_lower_alternating`** (E2, ridge
  adaptif) — dikonfirmasi stabil dan unggul dari `fit_hybrid` pada pilot 100+ aset (RMSE
  terkumpul 0,77±0,52 vs 1,21±0,85). 3 restart pra-registrasi per fold, patience 100, min_epochs 200.
- Arsitektur: m=2 pada x1..x7, m_I=3 pada v,e, k=1, Gauss + monoton softplus; 34 aturan/176 parameter.
- Seed model: 20260928, 20261005, 20261012, 20261019, 20261026.
- Analisis: MSE terkumpul atas seluruh baris uji; bootstrap berkelompok per image (2.000 resampel);
  koreksi Holm pada keluarga {H1a, H1b, H1c, H2}.
- Tidak akan dilakukan: memilih agregasi/skala setelah melihat skill; menambah seed; mengeluarkan
  aset; mengubah SESOI setelah hasil terlihat.

Sumber: HANFIS_RESEARCH_MEMORY.md (A-09, A-13, A-16, A-19), hasil E3
`results_python/e3/baselines_20260928T065247Z`, hasil E2 `results_python/e2/e2_pilot_20260929T103340Z.csv`.

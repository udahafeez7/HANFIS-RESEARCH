# E7 — Templat teks hasil D2

Ditulis 2026-10-14, **sebelum** ada satu pun baris maju. Dikomit ke repositori sebelum 2 November supaya cap waktunya membuktikan bahwa kalimat ditulis tanpa melihat hasil. Bukan artefak beku; protokol yang berlaku tetap `protocols/E7_preregistration_2026-10-12.md`.

## Aturan pemakaian

1. Setelah D2 hanya **angka dalam kurung kurawal** yang diisi. Varian dipilih oleh string `keputusan` di JSON hasil, bukan oleh penulis.
2. Tidak ada varian baru yang ditulis setelah hasil terlihat. Bila hasil tidak cocok dengan varian mana pun, tulis amendemen bernomor dulu, baru teksnya.
3. Istilah baku: *supported*, *confirmed*, *not confirmed*, *not demonstrated*, *worse*, *refuted*. Jangan pakai "trend", "marginally significant", "almost confirmed". Hasil yang tidak terbukti **bukan** "tidak ada beda".
4. Angka diambil dari `e7_results_*.json` dan `e7_formula_results_*.json`. Kunci P7a sampai P7d pada hasil `e7_evaluate` belum pernah dicetak; periksa dulu sebelum mengisi.
5. Kecocokan istilah dengan string keputusan: DIDUKUNG = supported, TERKONFIRMASI = confirmed, TIDAK TERKONFIRMASI = not confirmed, TIDAK TERBUKTI = not demonstrated, LEBIH BURUK = worse, DIBANTAH = refuted.

## 0. Ringkasan data (selalu dipakai)

> The prospective evaluation covers {n_weeks} forward weeks ({first_week} to {last_week}) and {n_rows} asset-weeks from {n_assets} images. {n_dropped} rows ({pct_dropped}\%) of {dropped_assets} were dropped under the pre-registered insufficient-evidence rule. The EPSS model version {epss_sentence} {redo_sentence}

- `epss_sentence`, tanpa perubahan: "stayed at {epss_version} throughout." Dengan perubahan: "changed on {date}; the weeks from that date are reported as a separate regime, as the protocol requires."
- `redo_sentence`, tanpa pengulangan: "No stage was repeated." Dengan pengulangan: "Stage {stage} was repeated once for a technical reason ({reason}); the log is in the repository."

## 1. P7a (rezim; keluarga 1)

- **supported:** In weeks without an EPSS model change, HANFIS was not better than persistence: the skill score was {ss} (95\% CI {lo} to {hi}), and the upper bound lies below the margin of $0.05$ (P7a supported).
- **not supported:** In weeks without an EPSS model change, the upper bound of the skill score of HANFIS against persistence was {hi}, which is not below $0.05$; P7a is not supported (SS {ss}, 95\% CI {lo} to {hi}).
- **refuted** (hanya bila `keputusan` memuatnya): HANFIS was better than persistence in these weeks (SS {ss}, 95\% CI {lo} to {hi}), contrary to P7a.

## 2. P7b (hibrida; keluarga 1)

- **confirmed:** The fixed blend of HANFIS and persistence beat persistence (SS {ss}, 95\% CI {lo} to {hi}; one-sided $p={p}$, Holm threshold {thr}). P7b is confirmed.
- **not confirmed:** The fixed blend did not beat persistence by the pre-registered margin (SS {ss}, 95\% CI {lo} to {hi}; one-sided $p={p}$ against a Holm threshold of {thr}). P7b is not confirmed. This does not show that the blend equals persistence.
- **worse:** The fixed blend was worse than persistence (SS {ss}, 95\% CI {lo} to {hi}).

## 3. P7e (rumus melawan persistence; keluarga 2; asal post hoc)

- **confirmed:** The max-form formula beat persistence (SS {ss}, 95\% CI {lo} to {hi}; MSE {mse_m} against {mse_base}; one-sided $p={p}$, Holm threshold {thr}). P7e is confirmed.
- **not demonstrated:** The forward weeks did not demonstrate an advantage of the formula over persistence (SS {ss}, 95\% CI {lo} to {hi}; one-sided $p={p}$, Holm threshold {thr}). The interval does not exclude no gain, and it does not exclude the earlier out-of-fold estimate.
- **worse:** The formula was worse than persistence (SS {ss}, 95\% CI {lo} to {hi}).

## 4. P7f (HANFIS melawan rumus; keluarga 2; asal post hoc)

- **supported:** HANFIS was not better than the formula (SS {ss}, 95\% CI {lo} to {hi}; MSE {mse_m} for HANFIS against {mse_base} for the formula). The upper bound lies below $0.05$, so P7f is supported.
- **refuted:** HANFIS was better than the formula (SS {ss}, 95\% CI {lo} to {hi}), the opposite of the out-of-fold result. P7f is refuted (lihat skenario C di bawah).
- **not demonstrated:** The forward weeks neither showed HANFIS to be better than the formula nor excluded it (SS {ss}, 95\% CI {lo} to {hi}).

## 5. P7d (informasi di atas persistence; sekunder)

- **informative:** The mean weekly Spearman correlation between predicted and realised change relative to the four-week lag was {rho} (lower 95\% bound {lo}), so HANFIS carries information about change that persistence lacks.
- **not informative:** The mean weekly Spearman correlation was {rho} (lower 95\% bound {lo}); the lower bound does not exceed zero.

## 6. Sensitivitas per minggu (selalu dilaporkan)

- **sama:** A bootstrap clustered by week ({n_weeks_boot} weeks) gives the same decision for {hypotheses} (SS {ss_w}, 95\% CI {lo_w} to {hi_w} for P7e).
- **berbeda:** A bootstrap clustered by week gives a different decision for {hypotheses}. With so few weeks and shared weekly shocks, we call these decisions fragile and do not build conclusions on them.

## 7. Skenario gabungan (satu dipilih menurut keputusan P7a, P7e, P7f)

Kalimat Discussion, Abstract, dan Conclusion dipilih dari satu skenario dan tidak diganti.

**A. P7e confirmed, P7f supported.**
- Discussion: Forward weeks confirm the earlier finding: a max-form formula in the exploitability and threat-intelligence inputs matches or beats the trained model, and HANFIS adds structure and a readable rule base, not accuracy.
- Abstract: In a pre-registered forward evaluation, the formula beat persistence and HANFIS did not beat the formula.
- Conclusion: The accuracy of HANFIS on this task is bounded by a simple formula; its value lies in structure and interpretability.

**B. P7e not demonstrated, P7f supported.**
- Discussion: Six forward weeks could not separate the formula from persistence, while HANFIS again did not beat the formula. Persistence stays a strong baseline on this target, and a longer window is needed to decide between the formula and persistence.
- Abstract: In a pre-registered forward evaluation, HANFIS did not beat a max-form formula; the formula's advantage over persistence was not demonstrated in six weeks.
- Conclusion: As in A, with the formula's advantage over persistence stated as open.

**C. P7f refuted** (HANFIS better than the formula forward).
- Wajib: tulis amendemen bernomor sebelum mengubah Abstract, Discussion, dan Conclusion; hasil ini membalik temuan E11 sampai E24.
- Discussion: In the forward weeks HANFIS beat the formula, which contradicts the out-of-fold results (E11 to E24). We report it as observed in one window of six weeks and treat it as needing replication, because the earlier analyses, run on the same images with a longer history, pointed the other way.

**D. P7a not supported.**
- Discussion: In weeks without a model change, HANFIS was not shown to be worse than persistence by the registered criterion; the regime claim of the protocol is therefore not supported, and we do not extend it.

## 8. Kalimat wajib (selalu ada di subbagian hasil E7)

- P7e and P7f have a post hoc origin: they were added to the protocol before the freeze but derive from analyses of earlier data (E11 to E14).
- Registration: tag `e7-prereg-2026-10-12` (commit `dbed812`), OSF registration https://osf.io/ahcvs/ (DOI 10.17605/OSF.IO/AHCVS), results archived on Zenodo (version DOI to be added after D2).
- One forward window of six weeks, {n_assets} images, shared weekly shocks: the result does not extend to other EPSS model versions or to other image sets.
- Analyses after the freeze (E14c and E15 to E24) are post hoc and descriptive; none of them changes a registered decision.

## 9. Dilarang

- Mengganti varian setelah melihat angka; menghapus varian yang tidak terpakai sebelum hasil ditulis.
- Menyebut hasil tak terbukti sebagai "tidak ada beda" atau "setara".
- Menambah analisis untuk "menyelamatkan" hipotesis yang tidak terkonfirmasi.
- Memakai `--today` atau mengulang `evaluate` dan `formula`.

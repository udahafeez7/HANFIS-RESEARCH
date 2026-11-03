# Additional file 1: indeks

Berkas `manuscript/additional_file_1.tex` (13 halaman) memuat apa yang dipindah dari naskah utama. Isi tabel dan gambar identik dengan aslinya. Catatan suplemen memuat teks asli bagian yang diringkas di naskah, kata per kata.

## Peta pemindahan tabel dan gambar

| Item di Additional file 1 | Label asli di naskah | Isi |
|---|---|---|
| Table S1 | `tab1` | Gerbang persiapan testbed |
| Table S2 | `tab:e1-ablation` | Ablasi E1 pada data sintetis |
| Table S3 | `tab:e4-epss` | Sensitivitas pergantian model EPSS (E4) |
| Table S4 | `tab:e6` | Kesetiaan penjelasan (E6) |
| Table S5, S6 | `tab:e15`, `tab:e15d` | Utilitas peringkat (E15) |
| Table S7 | `tab:e16` | Strata perubahan masukan (E16) |
| Table S8 | `tab:e21` | Kalibrasi (E21) |
| Figure S1 | `fig:methodology-mindmap` | Peta metodologi (TikZ) |
| Figure S2 | `fig:e3-baselines` | Baseline wajib (data sama dengan tabel baseline di badan) |
| Figure S3 | `fig:e4-skill-scores` | Skill score E4 (data sama dengan tabel E4 di badan) |

## Caption yang ada di berkas

| Label | Caption (awal) |
|---|---|
| tab1 | Experimental preparation, acceptance criteria, and methodological purpose. |
| tab:e1-ablation | E1 ablation: membership family $\times$ monotonicity, 5 seeds per cell. |
| tab:e4-epss | Post hoc sensitivity of the confirmatory comparison to the EPSS model change: full run versus weeks whose labels all pre-date 2026-06-15 (skill score, |
| tab:e6 | Explanation-fidelity checks on the 25 saved models. Pairs are the positive-control images P0-IF with and without the active filter; $S^{+}$ denotes th |
| tab:e15 | Weekly ranking utility (E15, post hoc): mean over weeks of the Spearman correlation between predicted score and realised label, and precision at the t |
| tab:e15d | Paired weekly differences in ranking utility (E15, post hoc); 95\% week-bootstrap intervals in brackets. |
| tab:e16 | Input-change strata at four weeks (E16, post hoc): rows, mean squared error (persistence / formula / HANFIS), and skill against persistence with 95\%  |
| tab:e21 | Calibration of four-week out-of-fold predictions (E21, post hoc). Mean error (prediction minus label), and slope $\beta$ and intercept $\alpha$ of the |
| fig:methodology-mindmap | Methodological mind map linking the cloud-native testbed, telemetry acquisition, monitoring-overhead controls, reproducibility evidence, and HANFIS in |
| fig:e3-baselines | Mandatory baselines' skill against climatology, pooled over 5 folds. A single CVSS score now adds modest skill over climatology (22\%, up from essenti |
| fig:e4-skill-scores | E4 confirmatory results: HANFIS skill score against each comparator with 95\% group-clustered bootstrap confidence intervals. Green bars exclude zero  |

## Catatan suplemen

- Supplementary note S1: Experimental platform and telemetry validation (original text of Section~\ref{subsec3.2})
- Supplementary note S2: Ablation and robustness analysis (original text of Section~\ref{subssec4.5})
- Supplementary note S3: Explanation fidelity (original text of Section~\ref{sec:e6})
- Supplementary note S4: Prioritisation utility (original text of Section~\ref{subsec:e15})
- Supplementary note S5: Error anatomy and the EPSS model change (original text of Section~\ref{subsec:e16})
- Supplementary note S6: Calibration, recalibration and stacking, E21 to E24 (original text of Section~\ref{subsec:e21})
- Supplementary note S7: Limitations (original text of Section~\ref{sec5}, subsection Limitations)

## Tabel yang tetap di badan naskah

Sembilan tabel tetap karena angka abstrak terlacak ke sana: jumlah aturan dan parameter (`tab:rules-params`), baseline wajib (`tab:e3-baselines`), hasil konfirmatori E4 (`tab:e4-results`), sapuan bottleneck (`tab:e5-results`), overhead observabilitas (`tab:overhead`), Shapley (`tab:e8`), E9 sampai E11 (`tab:e9`), sapuan horizon (`tab:e14`), baris tak terkena pergantian model (`tab:e19`). Tabel kesepuluh adalah hasil E7 (`tab:e7-results`).

## Catatan teknis

- Rujukan silang dari catatan suplemen ke naskah memakai `xr-hyper` terhadap `sn-article.aux`. Kompilasi naskah dulu.
- Templat Springer (`sn-jnl`) meminta naskah sebagai satu berkas `.tex`; Additional file 1 diunggah sebagai berkas tambahan terpisah.


---
Dokumen ini disusun dengan bantuan asisten AI (Claude, Anthropic) dari berkas repositori dan keluaran terminal sesi kerja 2 sampai 3 November 2026. Angka dan kutipan naskah diambil langsung dari berkas; pertimbangan ditandai sebagai pertimbangan.

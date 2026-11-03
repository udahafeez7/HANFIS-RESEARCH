# Hasil E7 dan aturan klaim

## Hasil resmi (D2, 2 November 2026)

Sumber: `results_python/e7/e7_results_20261102T135357Z.json` (sha256 `4cfcbf0d60741005b54d7025d2f95f2f1a75086067af37deae0aed4f1fd74302`) dan `e7_formula_results_20261102T135420Z.json` (sha256 `419f1f5bb9e5b7795285caf138df27c599a1e2695897cf701aa67d4a7fdf2780`). Enam minggu uji (2026-08-31 sampai 2026-10-05), 720 asset-week, 120 image (119 kelompok), tanpa baris yang dijatuhkan, versi model EPSS tetap v2026.06.15, tidak ada tahap yang diulang.

| Hipotesis | Perbandingan | Skill score (SS) | CI 95% | Keputusan |
|---|---|---|---|---|
| P7a | HANFIS terhadap persistence | -3,757 | [-9,177; -1,594] | Didukung (HANFIS tidak lebih baik) |
| P7b | Hibrida terhadap persistence | -0,807 | [-2,507; -0,160] | Lebih buruk |
| P7d | Spearman perubahan mingguan, HANFIS | +0,066 | [-0,074; +0,201] | Tidak terbukti |
| P7e | Rumus terhadap persistence | +0,340 | [+0,060; +0,628] | Terkonfirmasi |
| P7f | HANFIS terhadap rumus | -6,208 | [-13,677; -3,188] | Didukung (HANFIS tidak lebih baik) |

MSE: persistence 0,396, rumus 0,261, HANFIS 1,884. Lambda hibrida 0,5109. Skill score dihitung dari MSE gabungan dengan bootstrap per image (2.000 resampel); nilai p 0,0005 adalah lantai bootstrap (1/2001), bukan nilai tepat. P7a dan P7b satu keluarga Holm, P7e dan P7f keluarga lain. Sensitivitas bootstrap per minggu (6 kluster) memberi keputusan yang sama untuk P7e dan P7f.

Pembanding deskriptif (E11, out-of-fold, sudah ada di naskah): MSE rumus 0,27, persistence 0,42, HANFIS 0,41. Maju: rumus dan persistence hampir sama dengan angka itu, HANFIS naik ke 1,884. Penyebabnya tidak diuji. Dugaan bahwa pergantian model EPSS 2026-06-15 menggeser sebaran masukan adalah dugaan yang belum diuji; mengujinya berarti analisis post hoc yang tidak boleh mengubah keputusan terdaftar.

## Teks hasil di naskah (subbagian baru)

```latex
\subsection{Prospective evaluation (E7): forward results}\label{subsec:e7-results}
The design of Section~\ref{subsec:e7} was executed once on 2026-11-02, and no stage was repeated. The evaluation covers 6 forward weeks (2026-08-31 to 2026-10-05) and 720 asset-weeks from 120 images (119 image groups). No row was dropped under the pre-registered insufficient-evidence rule, so every asset stayed in the analysis, including \texttt{cockroachdb}. The EPSS model version stayed at v2026.06.15 throughout.

Table~\ref{tab:e7-results} lists the registered decisions. In weeks without an EPSS model change, HANFIS was not better than persistence: the skill score was $-3.757$ (95\% CI $-9.177$ to $-1.594$), and the upper bound lies below the margin of $0.05$ (P7a supported). The fixed blend was worse than persistence (SS $-0.807$, 95\% CI $-2.507$ to $-0.160$). The max-form formula beat persistence (SS $0.340$, 95\% CI $0.060$ to $0.628$; MSE $0.261$ against $0.396$; one-sided $p=0.0005$, Holm threshold $0.0125$). P7e is confirmed. HANFIS was not better than the formula (SS $-6.208$, 95\% CI $-13.677$ to $-3.188$; MSE $1.884$ for HANFIS against $0.261$ for the formula). The upper bound lies below $0.05$, so P7f is supported. The mean weekly Spearman correlation between predicted and realised change was $0.066$ (lower 95\% bound $-0.074$); the lower bound does not exceed zero, so P7d is not demonstrated. A bootstrap clustered by week (6 weeks) gives the same decision for P7e and P7f (SS $0.340$, 95\% CI $0.100$ to $0.758$ for P7e). The reported $p$ values equal $1/2001$, the smallest value that a bootstrap of 2{,}000 resamples can give.

\begin{table}[h]
\caption{E7 forward results: skill score (pooled mean squared error, bootstrap clustered by image, 2{,}000 resamples) with 95\% CI. P7a and P7b form one Holm family, P7e and P7f another; P7e and P7f are post hoc in origin.}\label{tab:e7-results}
\begin{tabular}{@{}llccl@{}}
\toprule
Hypothesis & Comparison & SS & 95\% CI & Decision \\
\midrule
P7a & HANFIS against persistence & $-3.757$ & [$-$9.177, $-$1.594] & Supported \\
P7b & Blend against persistence & $-0.807$ & [$-$2.507, $-$0.160] & Worse \\
P7e & Formula against persistence & 0.340 & [0.060, 0.628] & Confirmed \\
P7f & HANFIS against formula & $-6.208$ & [$-$13.677, $-$3.188] & Supported \\
\botrule
\end{tabular}
\end{table}

Against the out-of-fold results of Section~\ref{subsec:e9}, where the MSE was 0.27 for the formula, 0.42 for persistence and 0.41 for HANFIS, the forward MSE of the formula (0.261) and of persistence (0.396) stayed close, while that of HANFIS rose to 1.884.

P7e and P7f have a post hoc origin: they were added to the protocol before the freeze but derive from analyses of earlier data (E11 to E14). The protocol is tagged \texttt{e7-prereg-2026-10-12} (commit \texttt{dbed812}) and registered on the Open Science Framework (\texttt{https://osf.io/ahcvs/}; DOI \texttt{10.17605/OSF.IO/AHCVS}); the forward outputs are tagged \texttt{e7-results-2026-11-02}, and a Zenodo version DOI will be added. This is one forward window of six weeks and 120 images with shared weekly shocks, so the result does not extend to other EPSS model versions or to other image sets. Analyses after the freeze (E14c and E15 to E24) are post hoc and descriptive; none of them changes a registered decision.
```

## Rancangan E7 di naskah (Methods)

```latex
\subsection{Prospective evaluation (E7): pre-registered design}\label{subsec:e7}
The confirmatory comparison and the post hoc analyses reported above use data whose labels were already known when the questions were asked. To obtain an evaluation that does not, we froze a forward-evaluation protocol before any label for the test weeks was computed. The protocol, the five final HANFIS models (trained only on labelled weeks up to 2026-07-27, the first test week minus the 30-day embargo), the blend weight, the coefficients of the max-form formula of Section~\ref{subsec:e9}, and all analysis scripts were committed and tagged (\texttt{e7-prereg-2026-10-12}, created on 2026-10-12 at 15:04 +0700). A script verified that the tagged tree is identical to the working files. The evaluation script refuses to run unless this verification passes, and it runs only once. The protocol was also registered on the Open Science Framework before any forward label was computed (registration date 2026-10-13; \texttt{https://osf.io/ahcvs/}; DOI \texttt{10.17605/OSF.IO/AHCVS}). The analyses E14c and E15 to E20 were run on earlier data after the freeze and before the registration; the registration lists E15 to E20 and does not list E14c.

The test weeks are the Mondays $t$ from 2026-08-31 with $t+28$ days not later than the data date $D_2=\text{2026-11-02}$, six weeks in total; fewer than six matured weeks postpone the study rather than relax its criteria. Weekly EPSS and CISA KEV snapshots after 2026-09-21 are downloaded only after the tag, the vulnerability database is frozen once on $D_2$, and every image is rescanned with it. The predictors are HANFIS (mean of five seeds), persistence (the label of week $t-4$), a fixed blend of the two ($\lambda=0.5109$, fitted on out-of-fold predictions), and the formula. Skill scores against persistence use pooled mean squared error with a bootstrap clustered by image (2{,}000 resamples). Two families of one-sided hypotheses are tested, each with its own Holm correction~\cite{holm1979simple} at $\alpha=0.025$: whether HANFIS and the blend improve on persistence (P7a, P7b), and whether the formula improves on persistence while HANFIS is not better than the formula (P7e, P7f). The direction of predicted change is a secondary hypothesis (P7d). Rows with unresolved vulnerability-range evidence are dropped only if they amount to at most 2\% of the test-week rows, and an asset that loses all of its test weeks leaves the analysis and is reported (\texttt{cockroachdb} is expected to). The results are reported in Section~\ref{subsec:e7-results}.
```

## Istilah baku

- Pakai: supported, confirmed, not confirmed, not demonstrated, worse, refuted.
- Jangan pakai: "trend", "marginally significant", "almost confirmed".
- Hasil yang tidak terbukti ditulis "not demonstrated", bukan "tidak berbeda" atau "setara".
- Kecocokan string keputusan: DIDUKUNG = supported, TERKONFIRMASI = confirmed, TIDAK TERKONFIRMASI = not confirmed, TIDAK TERBUKTI = not demonstrated, LEBIH BURUK = worse, DIBANTAH = refuted.

## Klaim yang boleh dan tidak boleh

| Tidak boleh di naskah pertama | Alasan |
|---|---|
| HANFIS sebagai istilah baru | Soozanchi dkk. (2010) memakai nama itu lebih dulu; naskah sudah menyatakannya di Literature Review |
| Edge atau Jetson | Node Jetson hanya klien telemetri; H5 diturunkan ke pekerjaan lanjutan |
| Policy enforcement | Lapisan penerjemah kebijakan bukan kontribusi (A-63); dirancang, tidak dievaluasi |
| Overhead kausal observabilitas | Hanya pengukuran overhead testbed dua node, bukan efek kausal pada risiko |
| DMM | Di luar naskah pertama |
| Penjelasan berlapis | Dicabut (A-43); H6c gagal; kesetiaan penjelasan hanya "benar rata-rata, tidak merata" |
| "Dynamic" sebagai skor berbasis telemetri | Telemetri runtime hanya untuk mengukur overhead, bukan masukan model |

Makna "pre-registered" di naskah: protokol bertanggal dan bertag di repositori. Hanya E7 yang juga terdaftar di OSF (`10.17605/OSF.IO/AHCVS`). P7e dan P7f berasal dari analisis post hoc (E11 sampai E14) dan wajib dinyatakan begitu.

## Kalimat wajib di subbagian hasil E7 (sudah ada)

1. P7e dan P7f berasal post hoc: ditambahkan ke protokol sebelum pembekuan tetapi diturunkan dari analisis data lebih awal (E11 sampai E14).
2. Registrasi: tag `e7-prereg-2026-10-12` (komit `dbed812`), registrasi OSF, tag hasil `e7-results-2026-11-02`; DOI versi Zenodo akan ditambahkan.
3. Satu jendela maju enam minggu, 120 image, guncangan mingguan bersama: hasil tidak meluas ke versi model EPSS lain atau himpunan image lain.
4. Analisis setelah pembekuan (E14c dan E15 sampai E24) bersifat post hoc dan deskriptif; tidak ada yang mengubah keputusan terdaftar.


---
Dokumen ini disusun dengan bantuan asisten AI (Claude, Anthropic) dari berkas repositori dan keluaran terminal sesi kerja 2 sampai 3 November 2026. Angka dan kutipan naskah diambil langsung dari berkas; pertimbangan ditandai sebagai pertimbangan.

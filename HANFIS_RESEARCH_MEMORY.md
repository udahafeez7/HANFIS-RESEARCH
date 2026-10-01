# HANFIS_RESEARCH_MEMORY.md

> Memori proyek HANFIS. Dibaca ulang pada awal setiap sesi kerja (manusia maupun asisten AI).
> Diperbarui hanya melalui amendemen bernomor (A-xx) atau penutupan blocker (F-xx).
> Versi: 2.7 · Tanggal: 2026-09-28 · Pemilik: tim HANFIS (Universitas Andalas)

## 0. Identitas dan target akhir

- Judul penelitian (administratif, sesuai proposal): *Evaluasi Risiko Dinamis pada Orkestrasi Kontainer: Integrasi Adaptive Neuro-Fuzzy dan Domain Mapping Matrix (DMM) untuk Pemodelan Ancaman Siber*. DMM tidak lagi diaplikasikan (lihat A-00).
- Judul kerja naskah: *HANFIS: Hierarchical ANFIS for Evidence-Based Dynamic Risk Scoring of Cloud-Native Kubernetes Deployments* (tanpa "Edge" pada naskah pertama).
- Target akhir: (1) manuskrip Q1, target Springer *Journal of Cloud Computing*, submit awal Desember 2026; (2) kode yang dapat direproduksi pada `udahafeez7/HANFIS-RESEARCH`, lingkungan WSL Ubuntu, venv `anfis`, repositori lokal di `/mnt/c/Research/ANFIS` (NTFS, tidak peka huruf besar-kecil).
- Skema pendanaan: Penelitian Kepakaran LPPM Universitas Andalas 2026 (Tahap A–E, 12 bulan).

## 1. Tiga dokumen sumber kebenaran (pagar P1)

| Lapisan | Dokumen | Isi |
|---|---|---|
| Arsitektur model | `HANFIS_Mathematical_Scheme_18_August_2026` + amendemen A-01…A-08 | 7 input, 3 panel Sugeno, MF, komposisi, L(θ), kompleksitas |
| Pipeline data | `hanfis_sec33_target_definition.tex` + protokol label + kontrak data v2 | sumber resmi, tujuh input, agregasi per aset, label yₙ |
| Prosedur mutu | Memo Perbaikan Metodologis 2026-09-21 + protokol mutu | gerbang fail-closed, checksum, audit sampel, nomenklatur |

Setiap usulan perubahan harus menyebut lapisan dan dokumen yang diubah. Usulan tanpa keduanya ditolak.

## 2. Keputusan beku

- **Input (7):** x₁ CVSS, x₂ Exploitability (= EPSS(t) × ρ), x₃ Patch Risk, x₄ MFA Risk, x₅ Kubernetes Exposure, x₆ Asset Criticality, x₇ Threat Intelligence. Semua ternormalisasi [0,1]; nilai hilang = status *unknown*, bukan nol. Semua `risk_direction = higher_is_riskier`.
- **Arsitektur:** tiga panel Sugeno orde pertama: V(x₁,x₂,x₃)→v, E(x₄,x₅,x₆)→e, I(v,e,x₇)→r; r = clip(r̃,0,1). m = 2 pada input mentah; m_I = 3 pada v dan e di panel Integrasi (A-02). Bottleneck k = 1 dasar; sapuan k ∈ {1,2,4} hanya di E5.
- **Pelatihan:** ujung-ke-ujung (gradien mengalir lewat v, e); tidak ada target antara; OOF stacking tidak dipakai pada data nyata. LSE tertutup + ridge untuk konsekuen (A-06); keluarga MF dan konstrain monotonik (A-03, A-04) ditetapkan dari hasil E1 sebelum E4.
- **Label:** yₙ = label temporal §3.3: y(a,t) = (100/Δ) Σ maxᵥ[Xᵥ(τ)·S_{v,a}(τ)], Δ = 30 hari, dari snapshot EPSS/KEV mingguan bersegel. Tidak ada label pakar sebagai target. Penilaian manusia hanya untuk pemeriksaan kesalahan data dan audit sampel ≥10% keputusan runtime.
- **Rentang versi (Patch Risk):** sumber utama Alpine secdb; sumber kedua rentang CNA/NVD; pembanding sadar cabang; status ∈ {AFFECTED_VERSION_RANGE, NOT_IN_AFFECTED_VERSION_RANGE, INSUFFICIENT_EVIDENCE}; ketidaksepakatan → INSUFFICIENT_EVIDENCE.
- **ρ (keterjangkauan runtime, A-01):** 0 tidak terpasang/di luar rentang · 0,1 terpasang tanpa ketergantungan · 0,25 transitif, modul tidak aktif · 0,6 aktif dan termuat, pemicu belum terbukti · 1 termuat dan pemicu tersedia.
- **Agregasi per aset (A-01):** x₁(a) = max CVSS atas CVE AFFECTED dan terjangkau; x₂(a) = max EPSS×ρ; x₃(a) = f(proporsi AFFECTED belum ter-patch, usia perbaikan tertua). Satuan observasi: aset-minggu.
- **Pembagian data:** GroupTimeSplit per aplikasi + temporal, embargo 30 hari, ≥5 fold OOF, ≥5 seed; mean ± SD.
- **Pembanding wajib:** persistence, klimatologi, CVSS tunggal, flat ANFIS penuh (referensi, peringatan overfitting), FlatANFISMatched via subtractive clustering (±5% parameter), Fuzzyfortify (pemetaan input eksplisit; 5 kasus acuan = external-reference-only).
- **Testbed:** Mini PC (Windows 11, WSL2, Docker Desktop Kubernetes; 10.176.68.126; NodePort 30080; ns hanfis-research; Prometheus eksternal 127.0.0.1:29090) + Jetson Orin Nano (jetson@10.176.68.96) sebagai klien telemetri. Inferensi HANFIS di klaster. H5 (edge) → future work.

## 3. Klaim: boleh dan tidak boleh (pagar P11)

- **Boleh:** dataset dan pipeline bukti; pelatihan ujung-ke-ujung dengan variabel antara berjangkar semantik dan monoton; kurva akurasi–kompleksitas via bottleneck; protokol evaluasi dengan baseline dan metrik utilitas; penjelasan berlapis (jejak, masking, permukaan).
- **Tidak boleh (naskah pertama):** istilah HANFIS sebagai baru (Soozanchi dkk. memakainya lebih dulu, A-07); edge/Jetson; C5 policy enforcement; overhead kausal observabilitas; non-inferioritas H1 sebelum E4; DMM.

## 4. Amendemen

| ID | Tanggal | Lapisan | Isi singkat |
|---|---|---|---|
| A-00 | 2026-09-21 | Naskah | DMM dihapus dari arsitektur; judul naskah disesuaikan; judul administratif tetap sampai persetujuan LPPM |
| A-01 | 2026-09-21 | Skema §3 | ρ bertingkat memodulasi x₂; aturan agregasi per aset |
| A-02 | 2026-09-22 | Skema §3 | v, e sebagai variabel linguistik {rendah, sedang, tinggi}, MF terhubung, m_I = 3 |
| A-03 | 2026-09-22 | Skema §2, kode | Keluarga MF terhubung trapesium (Ruspini) sebagai varian; ablasi E1/E4 |
| A-04 | 2026-09-22 | Skema §3, kode | Konsekuen monoton nonnegatif (softplus) pada panel bawah dan Integrasi; ablasi on/off |
| A-05 | 2026-09-22 | Kode baseline | FlatANFISMatched via subtractive clustering; inisialisasi clustering sebagai varian |
| A-06 | 2026-09-22 | Skema §5, kode | LSE tertutup β = (ΦᵀΦ+λI)⁻¹Φᵀy, λ ≥ 1e−3; LSE bergantian panel bawah di E2 |
| A-07 | 2026-09-22 | Naskah | Kutip HANFIS terdahulu; nyatakan pembeda; pertimbangkan penanda HANFIS-DRS |
| A-08 | 2026-09-22 | Kode explain | Jejak firing + masking kelompok aturan + surface view; uji kesetiaan P0→P0-IF |
| A-09 | 2026-09-22 | Kode training | Konfigurasi pelatihan beku: hibrida LSE+Adam, 3 restart pra-registrasi, patience 100, min_epochs 200, lr 1e-2, ridge 1e-3 |
| A-10 | 2026-09-22 | Skema §2–3 | Keluarga MF Gauss dengan konstrain monotonik AKTIF untuk E4 (pelanggaran 0,17% vs 0,72%; harga 0,11 RMSE) |
| A-11 | 2026-09-28 | Testbed | Kontrol positif P0-IF diterima: OFF ρ=0,25, ON ρ=1,0 (libgd dan libexpat terpetakan 2/2 pod, pemicu HTTP 200) |
| A-12 | 2026-09-28 | Pipeline data | Kontrak data v2 (aset-minggu): image_id, week_start_utc, reachability_level, version_range_status, TI 0–1, unknown = null |
| A-13 | 2026-09-28 | Pipeline data | Label §3.3 diimplementasikan (patch 0024–0025): CVE aktif iff `PublishedDate` ≤ t; y = 100·mean_{τ∈{t+7,…,t+28}} maxᵥ Xᵥ(τ)·Sᵥₐ(τ), Xᵥ = max(EPSS, 1[KEV per τ]), **S = ρᵥ** (tanpa ρ label jenuh di 100 dan P0-IF ON/OFF tak berbeda); x₇ = indikator KEV per t; x₃ per kontrak v2 {0,1,2} (§2 rumus proporsi/usia **harus diselaraskan**); y = null bila jendela 30 hari melewati snapshot terakhir. Status: **DISAHKAN FINAL 2026-09-29** setelah dicek terhadap formula literal `hanfis_sec33_target_definition.tex` (agregasi max dan skala 100/Δ raw adalah definisi §3.3 itu sendiri, bukan pilihan bebas; x₃ kontrak v2 {0,1,2} sudah menjadi implementasi berjalan). Tindak lanjut: Skema §2 (rumus proporsi/usia x₃) harus diamendemen mengikuti kontrak v2, bukan sebaliknya -- belum dikerjakan. |
| A-14 | 2026-09-28 | Testbed | A-11 dipindahkan ke image `hanfis/p0if:1.1` = `sha256:795470a2adc37e39c848c9581c39b56dfbb80fa96c095c0d78b5f774a86e105b`; capture **v5 PASS** dengan kontras identik v4 (OFF 0/0/0, ON 2/2/1, pemicu 200). Image A-11 lama (`e9c0780b…`) tidak lagi ada di store Docker. **Pagar P13:** deployment penelitian memakai tag unik yang tidak pernah ditulis ulang (`1.0`, `1.1`, …); identitas dicatat dari `imageID` pod dan `trivy_image_id.txt`; digest lokal tidak dapat ditarik kubelet Docker Desktop (`NotFound`), jangan `set image` dengan `@sha256` |
| A-15 | 2026-09-28 | Testbed + pipeline | Image `hanfis/p0if:1.1` (`alpine:3.21` + `apk add`) ternyata **0 CVE** (Alpine 3.21.8, paket terkini) → tidak sah sebagai sumber varians label. P0-IF dibangun ulang sebagai **1.2** = `sha256:4b3e7080b453f4549a3a8e31dea91d3d009c0de9fa61cb5efbfdaeb44f0dc3d5`, `FROM nginxinc/nginx-unprivileged@sha256:65e3e85…` (basis P0, Alpine 3.21.3, 68 paket) **tanpa `apk add`**; capture **v6 PASS** (OFF 0/0/0, ON 2/2/1, pemicu 200); bundel Trivy `p0if_trivy_scan_y1J0WBRb`. **P13 diperluas:** basis Dockerfile dipatok digest; `apk add` dilarang pada image kontrol. Tabel aset-minggu 171 baris, positif 1,000, asset_id 3, grup image 2; kontras ON/OFF: y_min 0,0424 vs 0,0202 (2,1×), y_max identik 4,82 (agregasi max dipegang CVE lain, lihat keputusan terbuka). Pelajaran: satu pindaian hanya memuat CVE yang diketahui saat pemindaian (P0: 109 → 135 CVE dalam 14 hari) → pindai ulang semua image dengan DB beku pada tanggal pembekuan dataset |
| A-16 | 2026-09-28 | Kode splits | `GroupTimeSplit` (patch 0019) tidak menghasilkan fold pada panel lengkap (semua image setiap minggu): baris uji yang image-nya punya riwayat latih dibuang → semua blok kosong. Semantik baru (patch 0030): image dibagi deterministik (permutasi berseed `group_seed=20260928`, round robin) ke n kelompok; fold k melatih kelompok lain sampai `cutoff`, menguji kelompok k di blok k setelah embargo 30 hari; blok pertama dimulai hanya bila ≥ `min_train_weeks` minggu latih muat sebelum embargo. Setiap image diuji tepat sekali; ON/OFF se-`image_id` selalu sekelompok |

| A-17 | 2026-09-29 | Kode training | E2 (LSE bergantian kedua panel bawah, patch 0035) diuji pada 27 aset nyata di dua pengaturan (ridge 1e-3 tetap; ridge adaptif; min_train_weeks 4 dan 8). Hasil tidak konsisten dan kadang memburuk saat n_train membesar (fold 1, min_train_weeks=8: n_train=304, RMSE 8,48 -- lebih buruk dari fold n_train lebih kecil), membantah hipotesis awal 'kurang data'. **Keputusan: A-09 tetap `fit_hybrid` (hanya panel Integrasi diselesaikan tertutup) sebagai konfigurasi beku untuk E4**; `fit_hybrid_lower_alternating` (E2) ditunda sebagai jalur riset terbuka, dugaan kerja: interaksi proyeksi monoton (softplus + refit intersep) dengan solve gabungan bergantian selama banyak epoch, belum didiagnosis lewat jejak kondisi matriks per-epoch. |
| A-18 | 2026-09-29 | Kode training | Menyusul A-17 (E2 ditunda): pada inventaris diperluas ke 100 aset (5.700 baris; n_train per fold 272-2.754, naik dari 72-767), `fit_hybrid_lower_alternating` (E2) stabil di semua fold dan **konsisten lebih baik** dari `fit_hybrid` (A-09 default): RMSE rata-rata 0,50 vs 1,12, std 0,58 vs 0,86 (ridge adaptif). Ketidakstabilan A-17 (fold RMSE meledak hingga 10,86) terkonfirmasi murni soal skala data per fold, bukan cacat numerik permanen -- menambah `min_train_weeks` pada inventaris kecil tidak menolong (memperburuk), memperluas inventaris menolong. **Keputusan: E2 dipertimbangkan ulang sebagai kandidat kuat konfigurasi latih E4**, digantung pada satu ulangan pilot lagi setelah inventaris final (~110-120 aset, patch 0042) untuk memastikan stabil pada skala penuh sebelum menggantikan A-09 secara resmi. |
| A-19 | 2026-09-29 | Kode training | Menyusul A-18: pilot E2 final pada inventaris penuh (n_train per fold 296-2.992) menegaskan `fit_hybrid_lower_alternating` unggul di 4 dari 5 fold dan pada rata-rata (RMSE 0,77±0,52 vs `fit_hybrid` 1,21±0,85; fold 2 pengecualian, 1,44 vs 0,60, tidak meledak). **A-09 diperbarui: `fit_hybrid_lower_alternating` (ridge adaptif) diadopsi resmi menggantikan `fit_hybrid` sebagai skema pelatihan beku untuk E4.** Restart/patience/min_epochs A-09 lainnya tidak berubah. Perhatian terpisah: build terakhir melaporkan `no_INSUFFICIENT_EVIDENCE: false` (HOLD_TRAINING) -- gerbang §9 belum resmi lolos sampai sumber baris INSUFFICIENT_EVIDENCE terdiagnosis dan ditutup. |
| A-20 | 2026-10-01 | Hasil E4 | Run konfirmatori pertama (`results_python/e4/predictions_20261001T040745Z.csv`, 109 aset, 5 fold x 5 seed x 3 restart): H1a (vs CVSS) SS=0,969 [0,939;0,990] **terkonfirmasi**; H1c (vs ridge-7) SS=0,715 [0,518;0,893] **terkonfirmasi**; H2 (vs FlatANFISMatched) SS=0,816 [0,649;0,933] **terkonfirmasi**; H1b (vs persistence) SS=0,300 [-0,035;0,417] **belum terkonfirmasi** (konsisten dengan E3 -- persistence tetap palang tersulit); H2' (flat penuh) SS=0,324, dilaporkan tanpa kriteria. **Verifikasi margin H2**: periksa per-fold menunjukkan HANFIS unggul di kelima fold tanpa kecuali (SS 0,275-0,986, tak pernah negatif); y_matched melebar ke luar rentang wajar (-0,155 s/d 11,3, std 3,3-4,4) sementara y_hanfis tetap di rentang masuk akal -- menunjukkan FlatANFISMatched gagal berekstrapolasi pada wilayah jarang tercakup 8 klasternya, bukan artefak val_idx (val_idx acak hanya memilih restart, identik untuk kedua model; evaluasi SS berasal dari blok uji terpisah temporal/grup). **Ditafsirkan sebagai bukti keselarasan arsitektur V/E/I dengan struktur generatif label**, bukan bug. |
| A-21 | 2026-10-01 | Hasil E5 | Sapuan lebar bottleneck k (`hanfis_bottleneck.py`, modul terpisah dari HANFIS/A-09): k=1 cocok tepat 176 parameter/34 aturan (identik HANFIS); k=2 menelan 178 aturan/1.152 parameter (6,5x); **k=3/4 ditolak** karena meledak kombinatorial (1.458/13.138 aturan) -- temuan ini sendiri dilaporkan sebagai bukti alasan desain bottleneck skalar. Hasil empiris k=1 vs k=2: k=2 lebih buruk di **semua** 5 fold (RMSE 8,3-26,3 vs 2,5-3,1), tapi **bercampur (confounded)**: sapuan memakai skema latih sederhana (hanya panel Integrasi diselesaikan tertutup, bukan E2) dan proyeksi monoton tanpa refit intersep -- keduanya sudah terbukti (E1) menelan biaya akurasi yang membesar seiring jumlah aturan. **Belum bisa dibaca bersih** sebagai bukti lebar bottleneck itu sendiri buruk. Tindak lanjut: generalisasi skema E2 ke v,e vektor sebelum sapuan ini dianggap bersih. Naskah diperbarui (patch 0056) dengan 4 gambar nyata (E3, E4, E5 x2) dan §4.4 melaporkan temuan ini apa adanya, termasuk perancunya. |
## 5. Blocker manuskrip F1–F9 (status 2026-09-22)

F1 target sintetis → **bahan baku ditutup**: snapshot EPSS/KEV bersegel 57 minggu (2025-08-25…2026-09-21; KEV 2026.09.27, 1.728 entri; `data/real/snapshots/manifest.json`), tabel aset-minggu kontrak v2 berjalan (`scripts/build_asset_weeks.py`; 171 baris = P0 + P0-IF 1.2 ON/OFF, A-15); **gerbang §9 lolos 2026-09-28** (tag `m2-gate-training-authorized-20260928`): 27 aset (`configs/image_candidates.csv`, 24 image resmi dipatok digest pada tanggal beku + P0 + P0-IF ON/OFF), 1.539 baris, 1.431 berlabel, non-NA 0,93, INSUFFICIENT 0, `TRAINING_AUTHORIZED`. 5 image 0 CVE (alpine, busybox, memcached, redis, temurin). CVE tanpa `PublishedDate` diberi tanggal Senin pertama kemunculan di EPSS (patch 0031); yang tidak pernah muncul dikecualikan (debian 16, node-slim 16, wordpress 37). Target 120 image tetap untuk naskah; ≥ 27 cukup untuk E4. Catatan: model EPSS berganti `v2025.03.14` → `v2026.06.15` pada 2026-06-15 (ancaman validitas; kolom `epss_model_version` di diagnostik, batas fold jangan memotong di situ); pada EPSS nyata y P0 ≈ 0,02 pada skala 0–100 → transformasi skala label dan ambang "positif" harus ditetapkan di E3 · F2 H3 terbantah → dinyatakan ulang sebagai hipotesis mekanisme · F3 kontradiksi telemetri → **ditutup** (10 pasangan v3.0, node CPU +99,4 mCPU p=0,002; latensi P95 gagal tolak H0, CI [−0,13;+0,27] ms) · F4 B4.10 → **terbuka** · F5 held-out → **diimplementasikan** (GroupTimeSplit A-16, 5 fold, embargo 30 hari; E3 baseline dijalankan) · F6 headline m=3 → **terbuka** · F7 Fuzzyfortify → direncanakan (A-05, E4) · F8 threat model → ditutup · F9 template → **terbuka**.

## 6. Nomenklatur

P0 = deployment nginx baseline; P0-IF = P0 dengan image_filter aktif (kontrol positif); V5/V8 = checkpoint queue CVE; Run 1–17 = pasangan telemetri; checkpoint bernama PASS_/HOLD_; E0–E7 = eksperimen; M1–M6 = tonggak; A-xx = amendemen; F-xx = blocker; P1–P12 = pagar pengaman; D1–D19 = checklist deploy.

Tiga angka wajib di setiap laporan harian: jumlah baris event_id (aset-minggu), proporsi non-NA/positif, status TRAINING_AUTHORIZED.

## 7. Pelajaran literatur (satu kalimat per sumber)

- **Raju–Zhou–Kisner 1991; Wang 1999:** hierarki menekan mⁿ menjadi linier dan tetap aproksimator universal — dasar H2.
- **Lee–Chung–Yu 2003 (L-HFS):** variabel antara harus bermakna; reduksi hanya bila jumlah nilai antara kecil (total₁ − total₂ < 0) — dasar A-02 dan diagnostik pola kolom di E5.
- **Juston dkk. 2024:** MF terhubung Ruspini, LSE tertutup P = yA⁺, konstrain struktural, masking aturan — dasar A-03, A-04, A-06, A-08; DDPG ditolak.
- **Soozanchi dkk. (HANFIS penutur):** istilah HANFIS dan pengelompokan fitur sudah ada; subtractive clustering untuk premis; data kecil = klaim rapuh — dasar A-05, A-07.
- **Parthiban–Krishna 2026:** tiga ANFIS bertingkat dengan variabel antara berlabel; hibrida; klaim tingkat sistem; surface view — dasar E1 (ujung-ke-ujung karena tak berlabel), A-08, metrik utilitas.

## 8. Jadwal (jalur kritis M2–M3)

M1 21–27 Sep · M2 28 Sep–11 Okt · M3 12 Okt–1 Nov · M4 19 Okt–8 Nov · M5 2–15 Nov · M6 16 Nov–5 Des.
E0 selesai/perbaiki case · E1–E2 Sep minggu 4–Okt minggu 1 · E3 Okt minggu 3 (gerbang) · E4–E7 Nov minggu 1–3.

## 9. Gerbang go/no-go sebelum E4

Protokol beku bertanggal · ≥10 obs/parameter (≥1.320 baris) · non-NA ≥25% · assert_no_leakage lolos · snapshot EPSS/KEV lengkap · semua baseline berjalan pada pilot · tidak ada INSUFFICIENT_EVIDENCE di data latih · semua pengujian lulus di Linux ext4 dan WSL.

## 10. Cara memperbarui berkas ini

1. Tambahkan baris amendemen atau ubah status blocker; jangan menimpa entri lama.
2. Perbarui tanggal dan versi di kepala berkas.
3. Commit dengan pesan `memory: A-xx ...` atau `memory: close F-x ...`.

## 11. Status eksperimen (2026-09-28)

- E0 pipeline, E-INT (m_I), E1 (keluarga MF × monotonik) selesai; A-09 dan A-10 beku.
- Telemetri: 10 pasangan protokol v3.0 dianalisis; F3 ditutup; §4.1 naskah tersedia di
  `manuscript/results_efficiency.tex`.
- Kontrol positif P0-IF diterima (A-11): sumber varians label pertama tersedia.
- 2026-09-28: snapshot EPSS/KEV bersegel (patch 0023); tabel aset-minggu kontrak v2 (patch 0024–0025); P0-IF dipindah ke image 1.1, capture v5 PASS (A-14); inventaris `configs/assets.csv` = p0-baseline, p0if-on, p0if-off (patch 0026). P0-IF 1.1 ditemukan 0 CVE → dibangun ulang 1.2 dari basis P0, capture v6 PASS (A-15, patch 0027). Dokumentasi algoritma: Claude Doc *HANFIS — Dokumentasi Algoritma dan Komputasi (2026-09-28)*. Inventaris 27 aset + gerbang §9 lolos (patch 0029–0032). **E3 baseline (results_python/e3/baselines_20260928T064854Z)**, 5 fold, 20–21 image latih / 5–6 uji: persistence (lag 4 minggu, kausal) R² 0,83 raw / 0,86 log1p, ss_clim 0,85–0,86; ridge 7-masukan R² 0,86 raw, ss_clim 0,89, ss_pers −0,14 ± 1,18 (setara persistence); CVSS tunggal R² −0,45 / −7,2 (tidak menjelaskan paparan); klimatologi R² < 0 (label sangat berbeda antar-image). **Palang H1/H2 = persistence, bukan CVSS.** Berikutnya: praregistrasi E4 (SESOI, eksklusi, koreksi multiplisitas, uji berpasangan per fold terhadap persistence dan ridge-7), keputusan A-13 final (agregasi max vs noisy-OR, skala y raw vs log1p, x₃), cek anomali wordpress (516 CVE ber-PublishedDate > 2026-09-21).
- Berikutnya: E3 (gerbang go/no-go pada data nyata P0 dan P0-IF) memakai `GroupTimeSplit`
  (embargo 30 hari) dan kontrak data v2.

## 12. Protokol verifikasi patch (wajib, ditetapkan 2026-09-28)

- Lingkup uji resmi (identik dengan `scripts/apply_latest_patch.sh` baris 56): `python -m pytest -q test tests` dari `/mnt/c/Research/ANFIS`. Ada **dua** direktori uji: `test/` (test_environment, test_hanfis_dataset_validation, test_hanfis_end2end, test_hanfis_feature_contract, test_hanfis_target_contract, test_telemetry_validation) dan `tests/` (test_splits, test_telemetry_pipeline); total 70 tes per 2026-09-28. `pytest tests` saja hanya mengumpulkan 36. **Jangan** `pytest` tanpa argumen dari akar repo: folder `Jetson Orin/Telemetry/hanfis_protocol_v3/` berisi salinan cadangan modul uji bernama sama (`test_server_collector_v4_mock.py`) → 9 error koleksi, bukan kegagalan kode.
- Urutan verifikasi setiap patch: (1) verifikasi numerik pada referensi JAX bila menyentuh model, (2) `ast.parse`, (3) `python -m pytest -q test tests`, (4) terapkan ke snapshot bersih dengan `git am -3`, (5) `git format-patch` ke `Patch/NNNN/`.
- Pengiriman: zip ke `C:\Research\ANFIS\Patch` (WSL `/mnt/c/Research/ANFIS/Patch`), diekstrak ke `/tmp/pNNNN`, diterapkan `./scripts/apply_latest_patch.sh` atau `git am -3 /tmp/pNNNN/*.patch`. Skrip penerap hanya bila konteks diff tidak tersedia; skrip harus gagal-tertutup (assert tepat 1 kemunculan) dan idempoten.
- Lingkungan: venv `/home/hafiz/.venvs/anfis` (aktivasi: `source /home/hafiz/.venvs/anfis/bin/activate`), Python 3.12.3, numpy 2.5.1, pandas 2.3.3 (numpy ≥ 2.5 memicu DeprecationWarning `generic unit` untuk `pd.Timedelta("30D")` maupun `pd.Timedelta(days=30)`; pakai `pd.Timedelta(n, unit="D")`). Nomor patch terakhir: 0033. Alur GitHub: satu patch = satu commit di `research/amend-a02-a06` dengan `(patch NNNN)` di pesan; push tiap siklus; `main` hanya lewat PR di akhir tonggak; tag pada gerbang. Patch baru (berkas baru saja) dikirim sebagai `git format-patch`; patch yang menyentuh berkas lama hanya bila isi berkas itu ada di sesi (unggah dulu).
- Bukti Trivy: `scripts/scan_image_evidence.sh <slug> <image@sha256|name:tag>` → `data/evidence/<slug>_trivy_scan_<rand>/` (layout = bundel P0; `cache/` tidak di-commit; `git add -f` karena `data/` diabaikan). Trivy 0.74.0 di `/home/hafiz/.local/bin`. Bundel: P0 `p0_trivy_scan_r9NceXFV` (DB 2026-09-14, 109 CVE), P0-IF 1.1 `p0if_trivy_scan_oIB3UEcn` (0 CVE, tidak dipakai), P0-IF 1.2 `p0if_trivy_scan_y1J0WBRb` (aktif). Trivy DB tidak boleh diperbarui di tengah kampanye pindai: pakai `--skip-db-update` setelah unduhan pertama pada tanggal beku.

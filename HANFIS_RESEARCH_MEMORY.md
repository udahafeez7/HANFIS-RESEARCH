# HANFIS_RESEARCH_MEMORY.md

> Memori proyek HANFIS. Dibaca ulang pada awal setiap sesi kerja (manusia maupun asisten AI).
> Diperbarui hanya melalui amendemen bernomor (A-xx) atau penutupan blocker (F-xx).
> Versi: 2.2 · Tanggal: 2026-09-28 · Pemilik: tim HANFIS (Universitas Andalas)

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

## 5. Blocker manuskrip F1–F9 (status 2026-09-22)

F1 target sintetis → sebagian ditangani (label temporal; skala belum) · F2 H3 terbantah → dinyatakan ulang sebagai hipotesis mekanisme · F3 kontradiksi telemetri → **ditutup** (10 pasangan v3.0, node CPU +99,4 mCPU p=0,002; latensi P95 gagal tolak H0, CI [−0,13;+0,27] ms) · F4 B4.10 → **terbuka** · F5 held-out → direncanakan (GroupTimeSplit) · F6 headline m=3 → **terbuka** · F7 Fuzzyfortify → direncanakan (A-05, E4) · F8 threat model → ditutup · F9 template → **terbuka**.

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
- Berikutnya: E3 (gerbang go/no-go pada data nyata P0 dan P0-IF) memakai `GroupTimeSplit`
  (embargo 30 hari) dan kontrak data v2.

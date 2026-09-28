# HANFIS-RESEARCH

Hierarchical ANFIS for evidence-based dynamic risk scoring of cloud-native Kubernetes deployments.
Penelitian Kepakaran LPPM Universitas Andalas 2026 (Fakultas Teknologi Informasi). Target: Springer *Journal of Cloud Computing*, submit awal Desember 2026.

**Status 2026-09-28:** gerbang go/no-go §9 lolos (tag `m2-gate-training-authorized-20260928`): 27 aset × 57 minggu, 1.431 baris berlabel, baseline E3 dijalankan. Dokumen sumber kebenaran: `HANFIS_RESEARCH_MEMORY.md` (dibaca ulang setiap sesi; diperbarui hanya lewat amendemen A-xx).

## Apa yang ada di sini

| Direktori | Isi |
| --- | --- |
| `python_hanfis/` | model (`hanfis_models.py`), pemisah `GroupTimeSplit` (`splits.py`, A-16), snapshot bersegel (`snapshots.py`), pembangun tabel aset-minggu (`asset_weeks.py`) |
| `scripts/` | `fetch_snapshots.py` (EPSS/KEV, SHA-256), `scan_image_evidence.sh` + `scan_inventory.sh` (bundel Trivy per image), `assign_posture.py` (faktorial postur), `build_asset_weeks.py` (kontrak v2 + gerbang), `e3_baselines.py`, `apply_latest_patch.sh` |
| `configs/` | `anfis_source_schema_v2.json` (kontrak aset-minggu), `assets.csv` (inventaris), `image_candidates.csv` |
| `data/` | `real/snapshots/manifest.json` (segel; berkas mentah tidak di-commit), `evidence/<slug>_trivy_scan_*/` (bundel bukti), `processed/asset_weeks_v2_*` (status build) |
| `Kubernetes/` | manifes testbed; `p0if/` = kontrol positif (Dockerfile 1.2 dari basis P0 yang dipatok digest) |
| `results_python/` | `evidence/` (capture reachability v1–v6), `e3/` (baseline), eksperimen E0–E1 |
| `test/`, `tests/` | 93 tes; lingkup resmi `python -m pytest -q test tests` |
| `manuscript/` | LaTeX (§3.3 target, threat model, §4.1 efisiensi) |

## Pipeline data (§3.3)

1. `python scripts/fetch_snapshots.py fetch --start 2025-08-25 --end 2026-09-21` — 57 berkas harian EPSS + katalog KEV, disegel.
2. `scripts/scan_inventory.sh` — tarik image pada tanggal beku, patok digest, pindai dengan DB Trivy beku, tambah baris inventaris dengan postur faktorial.
3. `python scripts/build_asset_weeks.py --start 2025-08-25 --end 2026-09-21` — satu baris per (aset, minggu ISO): x1..x7 hanya dari informasi yang tersedia pada `week_start`, label y = 100·mean_τ max_v X_v(τ)·ρ_v atas 30 hari berikutnya (A-13), validasi kontrak v2, tiga angka wajib, `STATUS=TRAINING_AUTHORIZED|HOLD_TRAINING`.
4. `python scripts/e3_baselines.py --n-splits 5` — persistence, klimatologi, CVSS tunggal, ridge-7 di bawah `GroupTimeSplit` (embargo 30 hari, setiap image diuji tepat sekali).

## Cara kerja

- Lingkungan: WSL Ubuntu, venv `/home/hafiz/.venvs/anfis` (Python 3.12.3, numpy 2.5.1, pandas 2.3.3), Docker Desktop Kubernetes, Trivy 0.74.0.
- Setiap perubahan = satu patch bernomor (`Patch/pNNNN.zip` → `git am -3`), diverifikasi `ast.parse` → pytest → `git am` pada snapshot bersih sebelum dikirim; pesan commit memuat `(patch NNNN)`.
- Cabang kerja `research/amend-a02-a06`; `main` hanya lewat PR di akhir tonggak; tag pada setiap gerbang.
- Pagar: deployment dan basis Dockerfile dipatok digest/tag unik (P13); `apk add` dilarang pada image kontrol; data dan bukti gagal-tertutup (manifest SHA-256, `INSUFFICIENT_EVIDENCE` menghentikan pelatihan).

Detail arsitektur (7 masukan, tiga panel Sugeno, 34 aturan / 176 parameter), pelatihan hibrida LSE+Adam, dan keputusan beku ada di `HANFIS_RESEARCH_MEMORY.md` §2 dan dokumentasi algoritma.

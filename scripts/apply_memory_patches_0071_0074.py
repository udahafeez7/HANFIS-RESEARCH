#!/usr/bin/env python3
"""Catat patch 0071-0074 di HANFIS_RESEARCH_MEMORY.md (akar repo). Hanya MENAMBAH satu bagian di akhir;
satu-satunya baris yang diubah: 'Nomor patch terakhir: NNNN' bila tepat 1 kali. Idempoten, tidak menimpa apa pun."""
import re, sys, shutil, pathlib
P = pathlib.Path("HANFIS_RESEARCH_MEMORY.md")
s = P.read_text(encoding="utf-8")
TAG = "## Catatan sesi 2026-10-06 (patch 0071-0074)"
if TAG in s:
    print("Sudah diterapkan; tidak ada perubahan."); sys.exit(0)
SEC = f"""
{TAG}

| Patch | Lapisan | Isi singkat |
|---|---|---|
| 0071 | Kode uji | `tests/test_telemetry_pipeline.py`: `PROJECT_ROOT / "telemetry"` -> `"Telemetry"`; tes kini 126 passed + 11 subtests di Linux ext4 (sebelumnya gagal koleksi karena ext4 peka huruf besar-kecil) |
| 0072 | Naskah + skrip | Kalimat basi inventaris di sec. 3.5 diganti (120 aset final); `scripts/check_fold_epss_boundary.py` |
| 0073 | Naskah | Sisa template Springer di backmatter dibuang (blok Supplementary information bawaan dan Editorial Policies); Acknowledgements/Declarations utuh |
| 0074 | Naskah + hasil | Sensitivitas post hoc pra-pergantian EPSS (Tabel `tab:e4-epss`, sec. 4.5); kalimat basi di Discussion/Conclusion/Limitations dibuang; '120 images' -> '120 assets'; `hypertexnames=false` (13 peringatan duplicate destination -> 0) |

Temuan:
- Gerbang §9 pada tabel E4bis (`data/processed/asset_weeks_v2_120assets_e4bis.csv`): 6.833 baris event_id, 120 aset, 119 grup image, 57 minggu, non-NA 0,9303, positif 0,8882, INSUFFICIENT 0, `TRAINING_AUTHORIZED`. Praregistrasi E4: tag `e4-prereg-2026-09-29`, patch 0048 dan 0050. Tes leakage: `tests/test_splits.py`. Tes lulus di ext4 dan WSL.
- `hanfis_sec33_target_definition.tex` tidak ada di mesin; A-13 diverifikasi terhadap rumus di sec. 3.5 naskah (horizon 30 hari, stride 7, S = rho, X = max(EPSS, KEV), Patch Risk {{0,1,2}}).
- Batas fold vs pergantian model EPSS (2026-06-15), `GroupTimeSplit` 5 fold, embargo 30, min_train_weeks 4: fold 0-2 semua label pra-pergantian; fold 3 blok uji melintasi; fold 4 uji sepenuhnya pasca-pergantian. Praregistrasi E4 TIDAK menyebut pergantian model, jadi analisis ini post hoc.
- Sensitivitas pra-pergantian (`results_python/e4bis_120_preEPSS`, 4.560 baris, 38 minggu sampai 2026-05-11, 720 baris uji, seed beku, tabel dibuat `scripts/make_pre_epss_change_table.py`): H1a 0,973 [0,939; 0,991], H1c 0,728 [0,484; 0,901], H2 0,913 [0,753; 0,974] tetap terkonfirmasi; H1b -0,055 [-2,731; 0,201] belum terkonfirmasi. Skor tidak sebanding langsung (latih dan uji sama-sama berubah).
- Celah reproduksi: `meta_*.json` E4 tidak menyimpan argumen run (epochs, n_restarts, lag_weeks, embargo_days); log asli hanya 'nohup: ignoring input'. Usulan: simpan `vars(args)` ke meta di versi `e4_run.py` berikutnya.
- Belum ada di tabel E4: Fuzzyfortify (pembanding wajib di memori, 'external-reference-only'); nyatakan di naskah atau tambahkan.
"""
out = s.rstrip("\n") + "\n" + SEC
pat = re.compile(r"Nomor patch terakhir: \d{4}")
n = len(pat.findall(out))
if n == 1: out = pat.sub("Nomor patch terakhir: 0074", out); print("Nomor patch terakhir -> 0074")
else: print(f"PERINGATAN: 'Nomor patch terakhir' ditemukan {n}x; tidak diubah, ubah manual.")
shutil.copy(P, str(P) + ".pre-0071-0074.bak")
P.write_text(out, encoding="utf-8")
for ln in out.splitlines()[:8]:
    if "Versi:" in ln: print("Kepala saat ini ->", ln.strip())
print("OK")

#!/usr/bin/env python3
"""Catat patch 0066-0070 di HANFIS_RESEARCH_MEMORY.md (akar repo). Hanya MENAMBAH bagian di akhir
berkas; satu-satunya baris yang diubah adalah 'Nomor patch terakhir: NNNN' bila ada tepat 1 kali.
Tidak menimpa apa pun. Idempoten. Cetak baris kepala agar versi/tanggal dinaikkan manual."""
import re, sys, shutil, pathlib
P = pathlib.Path("HANFIS_RESEARCH_MEMORY.md")
s = P.read_text(encoding="utf-8")
TAG = "## Catatan sesi 2026-10-06 (patch 0066-0070)"
if TAG in s:
    print("Sudah diterapkan; tidak ada perubahan."); sys.exit(0)
SEC = f"""
{TAG}

| Patch | Lapisan | Isi singkat |
|---|---|---|
| 0066 | Naskah §3 | Opsi A: blok protokol telemetri lama (Run 1-5, checkpoint B4.11B) diganti subseksi *Observability-Overhead Protocol (external-v3.0)*; Run 7-16 (10 pasangan, 5 ON-OFF + 5 OFF-ON); target-definition dan §3.2 dipertahankan; "five paired runs" -> ten |
| 0067 | Testbed | P0-IF 1.2 (Dockerfile `FROM` terpatok digest, tanpa `apk add`), `p0if.yaml` 1.0 -> 1.2, `restore_candidates_csv.py` membuang kunci None, `first_seen_cache.json` (CVE tanpa kemunculan EPSS = null, aturan patch 0031) |
| 0068 | Naskah §3.2 | Kolom evidence Tabel 1 = bukti Run 7-16; subseksi protokol menyebut bootstrap 10.000 resampel (fixed seed) |
| 0069 | Naskah §3.2 | Gerbang dijelaskan sebagai prosedur; klaim lolos disandarkan pada arsip dan manifest Run 7-16, bukan pada B4.10-B4.11B (konsisten dengan penutupan F4: PASS asli tidak dapat dibuktikan maupun dibantah) |
| 0070 | Naskah §3.2 | Satu kalimat status gerbang pengembangan dilunakkan, isi faktual sama |

Temuan:
- Sumber CI Tabel overhead (mis. node CPU [96,29; 103,35]) = `Telemetry/analyze_pairs.py` -> `results_python/telemetry/paired_effects_v3.csv`: bootstrap 10.000 resampel, seed 20260721, uji sign-flip eksak untuk n <= 20 (2^n kombinasi; p-floor 0,002 pada n = 10; cabang Monte Carlo 20.000 flip hanya untuk n > 20).
- `Jetson Orin/Telemetry/hanfis_protocol_v3/analyze_cumulative_v3.py` (default 20.000 resampel, seed 20260829) adalah analisis kumulatif terpisah (3 Sep, `RunsV3/cumulative_analysis_v3/`); angka 20.000 di JSON-nya tidak berlaku untuk Tabel naskah.
- Skrip patch naskah dikumpulkan di `scripts/` (`apply_opsiA_sec3.py`, `apply_table1_evidence.py`, `apply_sec32_gates.py`, `apply_sec32_soften.py`).
- Verifikasi tiap patch: `python -m pytest -q test tests` = 126 passed, 11 subtests; kompilasi pdflatex+bibtex bersih, 25 halaman.
"""
out = s.rstrip("\n") + "\n" + SEC
pat = re.compile(r"Nomor patch terakhir: \d{4}")
if len(pat.findall(out)) == 1:
    out = pat.sub("Nomor patch terakhir: 0070", out)
    print("Nomor patch terakhir -> 0070")
else:
    print(f"PERINGATAN: 'Nomor patch terakhir' ditemukan {len(pat.findall(out))}x; tidak diubah, ubah manual.")
shutil.copy(P, str(P) + ".pre-0066-0070.bak")
P.write_text(out, encoding="utf-8")
for ln in out.splitlines()[:8]:
    if "Versi:" in ln: print("Kepala saat ini ->", ln.strip())
print("OK")

#!/usr/bin/env python3
"""Tambah amendemen A-40 (klaim Fuzzyfortify disesuaikan dengan audit reproduksi) setelah A-39 di
HANFIS_RESEARCH_MEMORY.md, plus peta komit lanjutan 2026-10-06. Gagal-tertutup: tepat satu baris '| A-39 |',
tidak ada '| A-40 |'. Idempoten. Tidak menimpa baris lain."""
import sys, shutil, pathlib
P = pathlib.Path("HANFIS_RESEARCH_MEMORY.md")
lines = P.read_text(encoding="utf-8").split("\n")
if any(l.startswith("| A-40 |") for l in lines):
    print("A-40 sudah ada; tidak ada perubahan."); sys.exit(0)
idx = [i for i, l in enumerate(lines) if l.startswith("| A-39 |")]
if len(idx) != 1: sys.exit(f"ABORT: baris A-39 ditemukan {len(idx)}x (harus 1)")
i = idx[0]
if i + 1 < len(lines) and lines[i + 1].startswith("| A-"): sys.exit("ABORT: ada amendemen setelah A-39")
A40 = ("| A-40 | 2026-10-06 | Naskah (abstrak, sec. 1 H1b, kontribusi C5, sec. 4.3) + Pembanding | Klaim Fuzzyfortify disesuaikan dengan bukti audit. "
       "Protokol pembanding (comparison_20260914_v3) mensyaratkan 4 input asli (`complexity_resilience_index`, `impact`, `base_score`, `exploitability`) dan "
       "melarang pemetaan proksi tak-terlapor; model yang diadaptasi hanya sensitivitas. Audit reproduksi 5 kasus terbit GAGAL "
       "(`STATUS=HOLD_FUZZYFORTIFY_REPRODUCTION_GAP`): skor reproduksi lebih rendah di semua kasus, selisih 5,94-20,97 (MAE 12,04, skala 0-100), "
       "empat dari lima identik 49,5. Naskah tidak lagi mengklaim perbandingan Fuzzyfortify; kalimat 'persistence, not Fuzzyfortify or CVSS, is the "
       "strongest baseline on the pilot' dikoreksi karena Fuzzyfortify tidak pernah dievaluasi pada pilot. Penyebab selisih (paper vs kode) BELUM diketahui; "
       "bila terselesaikan, Fuzzyfortify hanya boleh kembali sebagai sensitivitas. Bukti: `Jetson Orin/Telemetry/hanfis_protocol_v3/comparison_20260914_v3/` (komit 48c10e1) |")
lines.insert(i + 1, A40)
out = "\n".join(lines)
TAG = "## Peta komit lanjutan (2026-10-06, setelah patch 0074)"
if TAG not in out:
    out = out.rstrip("\n") + f"""

{TAG}

| Komit | Isi |
|---|---|
| ac74c3f | memory: catat patch 0071-0074 |
| 7d4d27a | memory: v2.19 |
| c44d246 | memory: A-39 + peta patch; e4_run menyimpan `args` ke meta |
| c7cb23d | chore: .gitignore artefak build dan cadangan |
| 48c10e1 | manuscript: klaim Fuzzyfortify (A-40); audit Fuzzyfortify dikomit |
| 1327491 | manuscript: tab:overhead lengkap dari results_efficiency.tex (tabularx) |
| eaef23b | chore: skrip figur E3/E5 dan catatan_keputusan_20261002.md terlacak |
| 3ed82d2 | manuscript: tiga Overfull hbox diperbaiki (rules-params, persamaan label, mind map) |

Status naskah: PDF 25 halaman; tanpa `undefined`/`multiply defined`/duplicate destination; sisa satu Overfull 8,6 pt (mind map). 126 passed + 11 subtests (ext4 dan WSL).
Terbuka: bibliografi `nist_zta_cloudnative_2023` dan Soozanchi dkk. (butuh sumber dari peneliti); penyebab selisih Fuzzyfortify; `apply_*.py` lama di akar repo belum diarsipkan.
"""
shutil.copy(P, str(P) + ".pre-a40.bak")
P.write_text(out, encoding="utf-8"); print("OK: A-40 ditambahkan setelah A-39")

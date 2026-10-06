#!/usr/bin/env python3
"""
Amend HANFIS_RESEARCH_MEMORY.md with A-36 (E5 bottleneck sweep re-run on
the completed 120-asset inventory -- significance flips in both arms).

Run from repo root (/mnt/c/Research/ANFIS):
    python3 apply_a36_memory_amendment.py

Fail-closed, same pattern as A-34/A-35: regex anchor on "## 5." heading,
refuses to run if "A-36" already present. No changes written unless the
anchor is found.

After running, review before committing:
    git diff HANFIS_RESEARCH_MEMORY.md
    git add HANFIS_RESEARCH_MEMORY.md
    git commit -m "memory: A-36 -- E5 bottleneck sweep re-run on completed
    120-asset inventory: k=1 and k=2's significance vs persistence both
    flipped direction; paired k=1-vs-k=2 comparison strengthened"
"""
import re
import sys
from pathlib import Path

MEMFILE = Path("HANFIS_RESEARCH_MEMORY.md")

NEW_ROW = (
    "| A-36 | 2026-10-06 | Eksperimen E5 + Naskah \u00a74.4 | "
    "E5 (sweep lebar bottleneck k=1,2) dijalankan ulang pada inventaris "
    "120-aset lengkap (skema `alternating`, sama dengan A-19/E4; smoke "
    "test `test_bottleneck_smoke.py` 12 lolos sebelum run). **Status "
    "signifikansi kedua k berbalik arah, bukan cuma bergeser:** k=1 "
    "SS_pers=0,169 [\u22120,330;0,343] \u2014 dulu CI seluruhnya positif "
    "[0,111;0,392] (signifikan), **sekarang CI melewati nol (tidak lagi "
    "signifikan)**; k=2 SS_pers=\u22120,622 [\u22122,259;\u22120,100] \u2014 dulu CI "
    "melewati nol [\u22121,681;0,180] (tidak signifikan), **sekarang CI "
    "seluruhnya negatif (signifikan ke arah buruk)**. Namun "
    "**perbandingan berpasangan k=1 vs k=2 justru menguat**: "
    "d_ss=0,791 [0,354;2,037], 100% resample mendukung k=1 (dulu 0,414 "
    "[0,179;1,815]) \u2014 k=1 tetap unggul RMSE di semua 5 fold (sign test "
    "p=0,0625, sama seperti 109-aset). Kesimpulan arsitektur **tidak "
    "berubah**: bottleneck sempit (k=1) tetap pilihan desain yang benar, "
    "k=2 tetap underpowered di semua fold (obs/param 0,3\u20132,9, naik dari "
    "0,26\u20132,6 lama). **Temuan tambahan di luar skala-aset:** figur "
    "`fig_e5_bottleneck_curve.pdf` yang ada di naskah ternyata sudah "
    "lama tidak cocok dengan caption-nya sendiri (menunjukkan RMSE "
    "mentah 2,5\u201320 berjudul \"confounded, see text\", bukan plot "
    "SS_pers+CI yang dideskripsikan caption) \u2014 dibuat ulang benar "
    "lewat skrip baru `make_e5_figure.py` (sebelumnya tidak ada skrip "
    "tersimpan, sama seperti E3). Satu sub-temuan (ablasi "
    "`clamp_intermediates`, biaya skill k=1=0,019 vs k=2=0,394) **belum** "
    "di-rerun di 120-aset \u2014 naskah diberi catatan eksplisit, bukan "
    "dibiarkan ambigu. File: `results_python/e5_120/e5_sweep_"
    "20261006T043146Z.csv`, `e5_predictions_20261006T043146Z.csv`, "
    "`e5_skill_ci_20261006T043146Z.csv`. |"
)


def main() -> None:
    if not MEMFILE.exists():
        sys.exit(f"ERROR: {MEMFILE} not found -- run from repo root. "
                  f"No changes made.")

    text = MEMFILE.read_text(encoding="utf-8")

    if "A-36" in text:
        sys.exit("ERROR: 'A-36' already appears in the file -- refusing "
                  "to double-apply. No changes made.")

    m5 = re.search(r"^## 5\..*$", text, flags=re.MULTILINE)
    if not m5:
        sys.exit("ERROR: could not find '## 5.' heading -- aborting, no "
                  "changes written to disk.")
    insert_at = m5.start()
    text = text[:insert_at] + NEW_ROW + "\n" + text[insert_at:]

    MEMFILE.write_text(text, encoding="utf-8")
    print("OK: wrote A-36 amendment row.")
    print("\nReview before committing:  git diff HANFIS_RESEARCH_MEMORY.md")


if __name__ == "__main__":
    main()

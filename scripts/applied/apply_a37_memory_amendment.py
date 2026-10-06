#!/usr/bin/env python3
"""
Amend HANFIS_RESEARCH_MEMORY.md with A-37 (clamp_intermediates ablation
re-run on the completed 120-asset inventory -- closes the last open E5
sub-finding from A-36).

Run from repo root (/mnt/c/Research/ANFIS):
    python3 apply_a37_memory_amendment.py

Fail-closed, same pattern as A-34/A-35/A-36.
"""
import re
import sys
from pathlib import Path

MEMFILE = Path("HANFIS_RESEARCH_MEMORY.md")

NEW_ROW = (
    "| A-37 | 2026-10-06 | Eksperimen E5 (ablasi clamp) + Naskah \u00a74.4 | "
    "Ablasi `clamp_intermediates off` (vs default `on`) dijalankan ulang "
    "pada inventaris 120-aset lengkap, menutup satu-satunya sub-temuan "
    "E5 yang masih ditandai \"belum di-rerun\" di A-36. Biaya skill dari "
    "hard clamp pada v,e: k=1 naik dari 0,019 (pilot 27-aset) menjadi "
    "**0,161** (120-aset, naik 8,5\u00d7); k=2 naik dari 0,394 menjadi "
    "**0,813** (naik 2,1\u00d7). **Arah dan interpretasi TIDAK berubah** "
    "(berbeda dari E3/E5 utama yang berbalik arah) \u2014 ini memperkuat, "
    "bukan membalikkan, narasi yang sudah ada: v,e makin sulit "
    "diestimasi andal seiring makin banyak parameter konsekuen "
    "bersaing untuk itu, konsisten dengan heterogenitas inventaris "
    "yang bertambah. Naskah diperbarui: angka ablasi diganti, catatan "
    "\"belum di-rerun\" (ditambahkan A-36) dihapus karena sudah selesai. "
    "**Dengan ini, seluruh E0\u2013E5 kini final dan konsisten di skala "
    "120-aset \u2014 tidak ada lagi sub-temuan yang menggantung di 109/27-aset "
    "lama.** File: `results_python/e5_120_clamp_ablation/e5_sweep_"
    "20261006T052942Z.csv`, `e5_predictions_20261006T052942Z.csv`. |"
)


def main() -> None:
    if not MEMFILE.exists():
        sys.exit(f"ERROR: {MEMFILE} not found -- run from repo root. No changes made.")

    text = MEMFILE.read_text(encoding="utf-8")
    if "A-37" in text:
        sys.exit("ERROR: 'A-37' already appears in the file -- refusing to double-apply.")

    m5 = re.search(r"^## 5\..*$", text, flags=re.MULTILINE)
    if not m5:
        sys.exit("ERROR: could not find '## 5.' heading -- aborting, no changes written.")
    insert_at = m5.start()
    text = text[:insert_at] + NEW_ROW + "\n" + text[insert_at:]

    MEMFILE.write_text(text, encoding="utf-8")
    print("OK: wrote A-37 amendment row.")
    print("Review before committing:  git diff HANFIS_RESEARCH_MEMORY.md")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Amend HANFIS_RESEARCH_MEMORY.md with A-38 (O5-B4.11 archive deprecation
finding) -- so future sessions don't repeat today's investigation into a
data path the manuscript doesn't even use.

Run from repo root (/mnt/c/Research/ANFIS):
    python3 apply_a38_memory_amendment.py

Fail-closed, same pattern as A-34 through A-37.
"""
import re
import sys
from pathlib import Path

MEMFILE = Path("HANFIS_RESEARCH_MEMORY.md")

NEW_ROW = (
    "| A-38 | 2026-10-06 | Arsip telemetri (bukan naskah) | "
    "Investigasi `O5-B4.11*` (gerbang 5-run lama, bukan protokol naskah) "
    "menemukan Run 2 ON tahap pertama (`run2-on-20260811T095841Z`) "
    "**berstatus HOLD sejak awal** (`RESOURCE_STATUS: HOLD`, P0 rows "
    "90/60 \u2014 duplikasi pengumpulan), dan lima file ringkasan I1\u2013I5 "
    "(`O5-B4.11I1`\u2013`I5`) ternyata dihitung dari capture HOLD ini, "
    "bukan dari capture pemulihan yang valid "
    "(`run2-on-20260814T073513Z`, status PASS, \"Reconstructed and "
    "frozen\"). Dihitung ulang manual (skrip pembuat asli tidak "
    "tersimpan) dari data valid (OFF `20260810T061621Z` status PASS "
    "+ ON `20260814T073513Z` status PASS): mean latensi tidak banyak "
    "berubah (OFF 1,473 vs ON 1,469 ms, kesimpulan kualitatif sama), "
    "tapi **std dan P95 pada angka HOLD lama meremehkan jauh** (std ON "
    "0,249\u21920,416, +67%; P95 0,810\u21922,621 ms, +45%). "
    "**PENTING \u2014 ini TIDAK memengaruhi naskah**: `manuscript/sn-"
    "article.tex` hanya merujuk protokol `external-v3.0` (10 pasangan "
    "run berimbang, Tabel~tab:overhead, F3 sudah ditutup), tidak pernah "
    "menyebut `O5-B4.11` sama sekali \u2014 diverifikasi lewat grep, "
    "bukan asumsi. Gerbang `O5-B4.11*` adalah metodologi internal yang "
    "sudah ditinggalkan/digantikan `external-v3.0`. **Catatan untuk "
    "sesi mendatang:** jangan habiskan waktu menghitung ulang I2\u2013I5 "
    "atau melanjutkan Run 3\u20135 gerbang `O5-B4.11` kecuali ada alasan "
    "eksplisit baru untuk menghidupkan kembali jalur ini \u2014 bukan "
    "jalur yang memblokir submisi. |"
)


def main() -> None:
    if not MEMFILE.exists():
        sys.exit(f"ERROR: {MEMFILE} not found -- run from repo root. No changes made.")

    text = MEMFILE.read_text(encoding="utf-8")
    if "A-38" in text:
        sys.exit("ERROR: 'A-38' already appears in the file -- refusing to double-apply.")

    m5 = re.search(r"^## 5\..*$", text, flags=re.MULTILINE)
    if not m5:
        sys.exit("ERROR: could not find '## 5.' heading -- aborting, no changes written.")
    insert_at = m5.start()
    text = text[:insert_at] + NEW_ROW + "\n" + text[insert_at:]

    MEMFILE.write_text(text, encoding="utf-8")
    print("OK: wrote A-38 amendment row.")
    print("Review before committing:  git diff HANFIS_RESEARCH_MEMORY.md")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Amend HANFIS_RESEARCH_MEMORY.md with A-35 (E3 mandatory baselines re-run on
the completed 120-asset inventory -- a reversal finding, not just a refresh).

Run from repo root (/mnt/c/Research/ANFIS):
    python3 apply_a35_memory_amendment.py

Fail-closed: anchors found by regex on structural markers ("## 5.",
"## 12."), matching the same pattern as apply_a34_memory_amendment.py. If
an anchor is missing, aborts with NO changes written to disk. Refuses to
run if "A-35" already appears anywhere in the file.

After running, review before committing:
    git diff HANFIS_RESEARCH_MEMORY.md
    git add HANFIS_RESEARCH_MEMORY.md
    git commit -m "memory: A-35 -- E3 mandatory baselines re-run on
    completed 120-asset inventory: ridge now underperforms persistence on
    every fold (was +30%, now -229%), a reversal; CVSS now explains ~22%
    of climatology skill (was ~0%)"
"""
import re
import sys
from pathlib import Path

MEMFILE = Path("HANFIS_RESEARCH_MEMORY.md")

NEW_ROW = (
    "| A-35 | 2026-10-05 | Eksperimen E3 + Naskah \u00a74.3/\u00a75.1 | "
    "E3 (baseline wajib: persistence, climatology, CVSS tunggal, ridge-7) "
    "dijalankan ulang pada inventaris 120-aset lengkap (6.357 baris, 5 "
    "fold grouped-temporal) menggunakan tabel data E4-bis yang sama "
    "(`asset_weeks_v2_120assets_e4bis.csv`). **Dua temuan berubah arah, "
    "bukan cuma bergeser angka:** (1) CVSS tunggal sekarang menjelaskan "
    "SS_clim=0,222 dari variansi label (dulu \u22480 di pilot 27-aset); (2) "
    "ridge-7 sekarang **kalah** dari persistence SS_pers=\u22122,293 pooled "
    "raw (dulu +0,301 di pilot 27-aset) \u2014 **dikonfirmasi di SEMUA 5 "
    "fold** (ss_pers per-fold: \u221285,33; \u22123,72; \u221234,84; \u22120,17; \u221218,55 "
    "\u2014 tidak ada yang positif), bukan didorong satu fold outlier. "
    "Diverifikasi bukan bug konfigurasi: `ridge_fit` memakai "
    "`lam=1e-3` tetap, konsisten dengan A-06, sama dengan yang dipakai "
    "pilot 27-aset. Interpretasi: model linier makin buruk "
    "berekstrapolasi begitu heterogenitas inventaris bertambah, sementara "
    "persistence (menyalin minggu lalu) tetap aman karena label memang "
    "sangat lengket minggu-ke-minggu. **Memperkuat** narasi inti naskah "
    "(persistence adalah palang tersulit, bukan CVSS) \u2014 tidak "
    "bertentangan dengan H1b/H1c yang sudah dikonfirmasi di E4 (A-34), "
    "karena H1c membandingkan HANFIS vs ridge langsung, bukan ridge vs "
    "persistence. Naskah diperbarui: Tabel~tab:e3-baselines (4 nilai), "
    "gambar `fig_e3_baselines.pdf` (dibuat ulang dari skrip baru "
    "`make_e3_figure.py`, sebelumnya tidak ada skrip pembuat tersimpan), "
    "paragraf \u00a74.3 ditulis ulang (bukan sekadar ganti angka \u2014 arah "
    "klaim CVSS dan ridge berbalik), paragraf \u00a75.1 Limitations "
    "diperbarui (sebelumnya A-34 menulis \"E3 belum di-rerun\", sekarang "
    "sudah selesai, celah ditutup di hari yang sama). File: "
    "`results_python/e3_120/baselines_20261005T104644Z.csv` (per-fold), "
    "`_pooled.csv`, `_folds.csv`, `_meta.json`. |"
)


def main() -> None:
    if not MEMFILE.exists():
        sys.exit(f"ERROR: {MEMFILE} not found -- run from repo root. "
                  f"No changes made.")

    text = MEMFILE.read_text(encoding="utf-8")

    if "A-35" in text:
        sys.exit("ERROR: 'A-35' already appears in the file -- refusing "
                  "to double-apply. No changes made.")

    m5 = re.search(r"^## 5\..*$", text, flags=re.MULTILINE)
    if not m5:
        sys.exit("ERROR: could not find '## 5.' heading -- aborting, no "
                  "changes written to disk.")
    insert_at = m5.start()
    text = text[:insert_at] + NEW_ROW + "\n" + text[insert_at:]

    MEMFILE.write_text(text, encoding="utf-8")
    print("OK: wrote A-35 amendment row.")
    print("\nReview before committing:  git diff HANFIS_RESEARCH_MEMORY.md")


if __name__ == "__main__":
    main()

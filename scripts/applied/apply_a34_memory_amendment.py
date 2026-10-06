#!/usr/bin/env python3
"""
Amend HANFIS_RESEARCH_MEMORY.md with A-34 (E4-bis, 120-asset results).

Run from repo root (/mnt/c/Research/ANFIS):
    python3 apply_a34_memory_amendment.py

What it does:
  1. Inserts a new amendment row (A-34) at the end of the "## 4. Amendemen"
     table, right before the "## 5." heading.
  2. Appends a dated status paragraph to the end of "## 11. Status
     eksperimen", right before the "## 12." heading.
  3. Bumps the header "> Versi: 2.17 ... Tanggal: 2026-10-02" to
     "2.18 ... 2026-10-05" (warns, does not fail, if that exact line isn't
     found -- update it by hand in that case).

Fail-closed: anchors are found by regex on structural markers ("## 5.",
"## 12."), not by matching a literal paragraph of text, because the content
this script was written against came from an OCR'd terminal screenshot and
cannot be trusted byte-for-byte. If an anchor is missing, the script aborts
with NO changes written to disk. It also refuses to run if "A-34" already
appears anywhere in the file, to avoid double-applying.

After running, review before committing:
    git diff HANFIS_RESEARCH_MEMORY.md
    git add HANFIS_RESEARCH_MEMORY.md
    git commit -m "memory: A-34 -- E4-bis (120 assets) results + per-fold
    variance-inflation finding (H1a/H1c/H2 confirmed, H1b not; CI widening
    traced to folds 0-1, not the 11 new candidate assets)"
"""
import re
import sys
from pathlib import Path

MEMFILE = Path("HANFIS_RESEARCH_MEMORY.md")

NEW_ROW = (
    "| A-34 | 2026-10-05 | Eksperimen E4-bis + Memori \u00a711 | "
    "E4-bis (120 aset, 6.833 baris, 7 cockroachdb dikecualikan karena "
    "CVE-2026-54876 under_investigation) dijalankan: "
    "H1a SS=0,9674 [0,9513;0,9802] p_Holm=0,0000 **TERKONFIRMASI**; "
    "H1c SS=0,6961 [0,5270;0,8163] p_Holm=0,0000 **TERKONFIRMASI**; "
    "H2 SS=0,6654 [0,2686;0,8441] p_Holm=0,0000 **TERKONFIRMASI** "
    "(turun dari 0,8163 di 27-aset, CI dua kali lebih lebar \u2014 lihat "
    "catatan per-fold); H1b SS=0,0146 [-0,6072;0,2462] p_Holm=0,6045 "
    "**belum terkonfirmasi** (konsisten dengan 27-aset); H2' (flat penuh, "
    "tak diuji) SS=0,2527. "
    "**Diagnosis per-fold (GroupTimeSplit A-16, 5 fold):** CI H2 yang "
    "melebar didorong oleh fold 0 (SS vs persistence=-16,35) dan fold 1 "
    "(HANFIS kalah dari persistence, matched, DAN flat_full sekaligus); "
    "diverifikasi **bukan** artefak 11 aset kandidat baru (hanya etcd-3-5 "
    "muncul di top-residual fold 0, tidak dominan). Residual terbesar "
    "didominasi aset lama (locust, etcd, n8n, grafana, rsyslog) dengan "
    "**var(y_hanfis) \u226b var(y_true)** (rasio 1,3\u00d7\u20132314\u00d7) pada aset "
    "berlabel nyaris datar minggu-ke-minggu \u2014 HANFIS tidak meredam noise "
    "snapshot EPSS/CVSS harian meski agregat mingguan tidak berarti, "
    "sementara persistence nyaris sempurna di aset ini. Dicatat sebagai "
    "temuan mekanisme/batasan genuin untuk \u00a7Diskusi, bukan bug pipeline. "
    "File: `results_python/e4bis_120/E4_skill_scores_20261005T073222Z.csv`, "
    "`E4_report_20261005T073222Z.md`, "
    "`predictions_20261002T103905Z.csv` (1.080 baris), "
    "`manuscript/figures/e4bis_120/` (3 gambar + `e4_per_fold_skill.csv` + "
    "provenance). **Belum dikerjakan:** re-run `e4_run.py --save-models` "
    "pada 120-aset untuk gambar PDP/surface-view (A-08, patch 0068) \u2014 "
    "run ini belum pakai flag itu. |"
)

NEW_STATUS_PARAGRAPH = (
    "- 2026-10-05: **E4-bis (120 aset) selesai** (rincian lengkap: A-34). "
    "Gerbang \u00a79 lolos 2026-10-02 (tag "
    "`e4bis-gate-training-authorized-20261002`, commit `87ae00e`), patch "
    "0066\u20130068 (gambar E4, flag `--save-models`, PDP/surface-view) "
    "terpasang dan 126 tes lulus sebelum run. H1a/H1c/H2 terkonfirmasi "
    "pada skala 120-aset, H1b masih belum \u2014 pola sama seperti 27-aset, "
    "memberi keyakinan hasil tidak sensitif terhadap ukuran inventaris. "
    "Temuan baru: beberapa image berlabel hampir konstan (grafana, etcd, "
    "rsyslog) menunjukkan HANFIS berfluktuasi jauh lebih besar dari label "
    "sungguhan (rasio varians hingga >1000\u00d7) \u2014 kandidat penjelasan "
    "utama kenapa H1b belum terkonfirmasi. Berikutnya: putuskan apakah "
    "re-run dengan `--save-models` untuk PDP (A-08) sebelum atau sesudah "
    "menulis \u00a71\u2013\u00a72 naskah (F9)."
)


def main() -> None:
    if not MEMFILE.exists():
        sys.exit(f"ERROR: {MEMFILE} not found -- run this from the repo root "
                  f"(/mnt/c/Research/ANFIS). No changes made.")

    text = MEMFILE.read_text(encoding="utf-8")

    if "A-34" in text:
        sys.exit("ERROR: 'A-34' already appears in the file -- refusing to "
                  "double-apply. Inspect manually (git diff / git log) "
                  "before re-running. No changes made.")

    # 1. Insert the new amendment row right before the "## 5." heading.
    m5 = re.search(r"^## 5\..*$", text, flags=re.MULTILINE)
    if not m5:
        sys.exit("ERROR: could not find a line starting with '## 5.' -- "
                  "aborting, no changes written to disk.")
    insert_at = m5.start()
    text = text[:insert_at] + NEW_ROW + "\n" + text[insert_at:]

    # 2. Append the new status paragraph at the end of "## 11." section,
    #    i.e. right before the next "## 12." heading.
    m12 = re.search(r"^## 12\..*$", text, flags=re.MULTILINE)
    if not m12:
        sys.exit("ERROR: could not find a line starting with '## 12.' -- "
                  "aborting. NOTE: step 1's change above was computed but "
                  "NOT written to disk (the file is only written once, at "
                  "the end, after both steps succeed) -- safe to fix and "
                  "re-run from scratch.")
    insert_at2 = m12.start()
    text = text[:insert_at2] + NEW_STATUS_PARAGRAPH + "\n\n" + text[insert_at2:]

    # 3. Best-effort header version/date bump -- warn, don't fail, if absent.
    text, n_sub = re.subn(
        r"(> Versi:\s*)2\.17(\s*\u00b7\s*Tanggal:\s*)2026-10-02",
        r"\g<1>2.18\g<2>2026-10-05",
        text,
    )

    MEMFILE.write_text(text, encoding="utf-8")

    print("OK: wrote A-34 amendment row + \u00a711 status paragraph.")
    if n_sub == 0:
        print("WARNING: header line '> Versi: 2.17 ... Tanggal: 2026-10-02' "
              "not found or already different -- version/date header was "
              "NOT auto-updated. Bump it by hand.", file=sys.stderr)
    else:
        print("Header bumped: Versi 2.17 -> 2.18, Tanggal -> 2026-10-05.")
    print("\nReview before committing:  git diff HANFIS_RESEARCH_MEMORY.md")


if __name__ == "__main__":
    main()

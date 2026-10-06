#!/usr/bin/env python3
"""
Fix a stale fold-structure description in Section 4.2 (Methodology) that
was never updated when the inventory grew past 27 assets -- found during a
systematic sweep for other stale numbers, not previously touched by any of
today's patches (A-34 through A-37 all targeted Results/Limitations text).

Run from repo root (/mnt/c/Research/ANFIS):
    python3 apply_fold_structure_patch.py

New fold sizes sourced directly from results_python/e3_120/
baselines_20261005T104644Z_folds.csv (train_images / test_images columns):
  fold 0: 95 train / 24 test
  fold 1: 95 train / 24 test
  fold 2: 95 train / 24 test
  fold 3: 95 train / 24 test
  fold 4: 96 train / 23 test
-> "95--96 training images against 23--24 held-out images"

Fail-closed: anchor text must appear exactly once.

After running:
    git diff manuscript/sn-article.tex
    git add manuscript/sn-article.tex
    git commit -m "manuscript: fix stale 27-asset fold-structure description
    in Methodology (Sec 4.2) -- updated to 120-asset fold sizes from
    e3_120 folds.csv, found during a systematic stale-number sweep"
"""
import sys
from pathlib import Path

TEXFILE = Path("manuscript/sn-article.tex")

OLD = (
    "On the current 27-asset inventory this\n"
    "yields 5 folds of 20--21 training images against 5--6 held-out images."
)
NEW = (
    "On the completed 120-asset inventory this\n"
    "yields 5 folds of 95--96 training images against 23--24 held-out images."
)


def main() -> None:
    if not TEXFILE.exists():
        sys.exit(f"ERROR: {TEXFILE} not found -- run from repo root. No changes made.")

    text = TEXFILE.read_text(encoding="utf-8")
    n = text.count(OLD)
    if n == 0:
        sys.exit("ERROR: anchor text not found. No changes written to disk.")
    if n > 1:
        sys.exit(f"ERROR: anchor found {n} times (expected 1) -- refusing to guess.")

    text = text.replace(OLD, NEW, 1)
    TEXFILE.write_text(text, encoding="utf-8")
    print("OK: fold-structure description updated to 120-asset numbers.")
    print("Review before committing:  git diff manuscript/sn-article.tex")


if __name__ == "__main__":
    main()

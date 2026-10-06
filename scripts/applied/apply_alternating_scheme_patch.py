#!/usr/bin/env python3
"""
Fix a second stale claim in the same Methodology paragraph (Sec 4.2):
"the alternating lower-panel closed-form training variant... has not yet
been run on the real 27-asset table at the time of writing" is no longer
true -- confirmed by cross-referencing line ~688 of this same manuscript
(written today as part of A-36), which states E5's k=1 sweep "uses exactly
A-09's training scheme -- the alternating closed-form least squares...".
This IS the same variant described at Sec 3.2 (line ~282). A-09 is the
frozen scheme used for every real-data result reported in this paper
(E4, E5, and the clamp ablation, all run repeatedly today on 109- then
120-asset data).

Run from repo root (/mnt/c/Research/ANFIS):
    python3 apply_alternating_scheme_patch.py

Fail-closed: anchor text must appear exactly once.

After running:
    git diff manuscript/sn-article.tex
    git add manuscript/sn-article.tex
    git commit -m "manuscript: fix second stale claim in Methodology --
    alternating training variant was adopted as A-09's frozen scheme and
    has been run extensively on real data, not 'not yet run' (found during
    the same stale-number sweep as the fold-structure fix)"
"""
import sys
from pathlib import Path

TEXFILE = Path("manuscript/sn-article.tex")

OLD = (
    "The alternating lower-panel\n"
    "closed-form training variant (Section~\\ref{subsec:hanfis-architecture}) has been implemented and verified\n"
    "against an independent closed-form derivation on synthetic data (mean squared error $0.78\\to4\\times10^{-4}$\n"
    "over six alternating iterations with no premise training at all), but has not yet been run on the real\n"
    "27-asset table at the time of writing."
)
NEW = (
    "The alternating lower-panel\n"
    "closed-form training variant (Section~\\ref{subsec:hanfis-architecture}) was verified against an\n"
    "independent closed-form derivation on synthetic data (mean squared error $0.78\\to4\\times10^{-4}$ over\n"
    "six alternating iterations with no premise training at all) before being adopted as amendment A-09's\n"
    "frozen training scheme, used throughout the real-data results reported below and in\n"
    "Section~\\ref{subssec4.4}."
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
    print("OK: alternating-scheme claim corrected.")
    print("Review before committing:  git diff manuscript/sn-article.tex")


if __name__ == "__main__":
    main()

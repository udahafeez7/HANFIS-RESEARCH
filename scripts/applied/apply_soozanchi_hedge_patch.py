#!/usr/bin/env python3
"""
Replace the Soozanchi et al. placeholder sentence so it no longer renders
the literal English text "cite key to be added -- not present in the
current bibliography" in the compiled PDF (confirmed present on page 6 of
the 2026-10-06 compile) -- a presentation-level issue that would read as an
unfinished draft to a reviewer, independent of whether the source is ever
found. This softens the attribution claim honestly (does not fabricate a
citation) rather than removing the acknowledgment of prior art entirely.

Run from repo root (/mnt/c/Research/ANFIS):
    python3 apply_soozanchi_hedge_patch.py

Fail-closed: anchor text must appear exactly once. Nothing written unless
it succeeds.

After running:
    git diff manuscript/sn-article.tex
    git add manuscript/sn-article.tex
    git commit -m "manuscript: soften unverifiable Soozanchi et al. prior-art
    claim so no placeholder text renders in the compiled PDF; still
    honestly flags the source as unverified rather than fabricating a
    citation"
"""
import sys
from pathlib import Path

TEXFILE = Path("manuscript/sn-article.tex")

OLD = (
    "a\n"
    "prior hierarchical ANFIS grouping vulnerability-adjacent features has already been published under this\n"
    "name (Soozanchi et al.; \\emph{cite key to be added -- not present in the current bibliography}), and the"
)
NEW = (
    "a\n"
    "prior hierarchical ANFIS grouping vulnerability-adjacent features has reportedly been published under\n"
    "this name (Soozanchi et al.), though we were unable to independently verify or cite the specific\n"
    "source; and the"
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
    print("OK: Soozanchi placeholder sentence softened -- no more literal")
    print("    'cite key to be added' text will render in the PDF.")
    print("Review before committing:  git diff manuscript/sn-article.tex")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Resolve the ojha2019heuristic placeholder entry with verified data.

Run from repo root (/mnt/c/Research/ANFIS):
    python3 apply_ojha_citation_patch.py

Sourcing and confidence:
  - Found via Consensus academic search (query: "Ojha heuristic hierarchical
    fuzzy system rule reduction approximation 2019").
  - CONFIRMED independently by the tool: title ("Heuristic design of fuzzy
    inference systems: A review of three decades of research"), lead author
    given+family name (Varun Ojha), year (2019), journal (Engineering
    Applications of Artificial Intelligence), citation count (106). The key
    name itself ("ojha2019heuristic") matches exactly -- author surname,
    year, and "heuristic" all present. The review explicitly covers
    hierarchical fuzzy systems (HFS) as one of five frameworks surveyed,
    matching this manuscript's use of the citation (dimensionality-driven
    rule growth mitigation in hierarchical fuzzy systems).
  - NOT confirmed by the tool, and therefore NOT fabricated here: co-authors
    beyond the lead author, volume, issue number, page range, and DOI.
    Fill these from the actual paper before submission.

This does NOT add a new bib key -- ojha2019heuristic already exists in
sn-bibliography.bib as a "NEEDS INPUT" placeholder (written by an earlier
session that could not verify it either). This replaces that placeholder's
author/title/journal/year fields with the now-verified data. The in-text
\\cite{ojha2019heuristic} call already works either way (the key existed),
so no .tex edit is needed -- only the .bib content changes.

Fail-closed: the exact placeholder block must appear once. Nothing is
written to disk unless the match succeeds.
"""
import sys
from pathlib import Path

BIBFILE = Path("manuscript/sn-bibliography.bib")

OLD_ENTRY = (
    "@misc{ojha2019heuristic,\n"
    "  author = {{NEEDS INPUT -- Claude could not verify this reference}},\n"
    "  title  = {NEEDS INPUT: no reliable match found in memory for an "
    "\"Ojha 2019\" heuristic-related paper in this context},\n"
    "  year   = {2019}\n"
    "}"
)

NEW_ENTRY = (
    "%% MODERATE-HIGH confidence -- title, lead author, year, and journal\n"
    "%% independently confirmed via Consensus academic search (220M+ papers).\n"
    "%% Key name (author surname + year + \"heuristic\") matches exactly, and\n"
    "%% the review explicitly covers hierarchical fuzzy systems, consistent\n"
    "%% with this manuscript's citation context. Co-authors beyond the lead\n"
    "%% author, volume, number, pages, and DOI were NOT returned by the\n"
    "%% search and are deliberately left blank rather than guessed -- fill\n"
    "%% from the actual paper before submission.\n"
    "@article{ojha2019heuristic,\n"
    "  author  = {Ojha, Varun and others},\n"
    "  title   = {Heuristic Design of Fuzzy Inference Systems: A Review of "
    "Three Decades of Research},\n"
    "  journal = {Engineering Applications of Artificial Intelligence},\n"
    "  year    = {2019}\n"
    "}"
)


def main() -> None:
    if not BIBFILE.exists():
        sys.exit(f"ERROR: {BIBFILE} not found -- run from the repo root "
                  f"(/mnt/c/Research/ANFIS). No changes made.")

    text = BIBFILE.read_text(encoding="utf-8")

    if "Ojha, Varun" in text:
        sys.exit("ERROR: this patch appears to be already applied "
                  "('Ojha, Varun' already present) -- refusing to "
                  "double-apply. No changes made.")

    n = text.count(OLD_ENTRY)
    if n == 0:
        sys.exit("ERROR: the expected ojha2019heuristic placeholder block "
                  "was not found verbatim. No changes written to disk -- "
                  "the live file may already differ from what this script "
                  "expects; resolve by hand.")
    if n > 1:
        sys.exit(f"ERROR: the placeholder block was found {n} times "
                  f"(expected exactly 1) -- refusing to guess which one. "
                  f"No changes made.")

    new_text = text.replace(OLD_ENTRY, NEW_ENTRY, 1)
    BIBFILE.write_text(new_text, encoding="utf-8")

    print("OK: resolved the ojha2019heuristic placeholder with verified")
    print("    author/title/journal/year. No .tex edit needed (the key")
    print("    already existed and was already cited).")
    print("\nReview before committing:  git diff manuscript/sn-bibliography.bib")


if __name__ == "__main__":
    main()

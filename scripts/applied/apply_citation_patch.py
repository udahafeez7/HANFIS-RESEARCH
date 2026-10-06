#!/usr/bin/env python3
"""
Add ONE verified bibliography entry (Lee, Chung and Yu 2003) and resolve its
in-text placeholder. Does NOT touch the Soozanchi et al. placeholder --
three separate Consensus searches (academic search, 220M+ papers) failed to
find a matching source, and no entry is written for anything not
independently confirmed. That placeholder is left exactly as it stands.

Run from repo root (/mnt/c/Research/ANFIS):
    python3 apply_citation_patch.py

Sourcing and confidence, for your own record:
  - Found via Consensus academic search (query: "Lee Chung Yu hierarchical
    fuzzy system reduction linguistic variables 2003", cross-checked with a
    second query quoting the abstract's own phrasing).
  - CONFIRMED independently by the tool: title ("Modeling of hierarchical
    fuzzy systems"), lead author given name (Ming-Ling Lee), year (2003),
    journal (Fuzzy Sets and Systems, abbreviated "Fuzzy Sets Syst." in the
    search result), citation count (153) -- and the abstract matches the
    manuscript's own usage (a rule-base mapping scheme for middle-layer
    variables in hierarchical fuzzy systems) almost exactly.
  - NOT confirmed by the tool, and therefore NOT fabricated here: Chung and
    Yu's given names/initials, volume, issue number, page range, and DOI.
    The manuscript's own prose already names "Lee, Chung, and Yu" as the
    authors (written before this session), which is consistent with but not
    independently re-verified by this search -- you may already have the
    full reference from wherever that naming originally came from. Fill the
    missing bib fields from the actual paper before submission; the entry
    compiles and cites correctly without them, it just prints a shorter
    reference than usual.

Fail-closed: both edits' anchor text must appear in the file EXACTLY ONCE.
Nothing is written to disk unless every edit succeeds.
"""
import sys
from pathlib import Path

BIBFILE = Path("manuscript/sn-bibliography.bib")
TEXFILE = Path("manuscript/sn-article.tex")

NEW_BIB_ENTRY = """
%% MODERATE-HIGH confidence -- title, lead author's given name, year, and
%% journal independently confirmed via Consensus academic search (220M+
%% papers; cross-checked with two differently worded queries); abstract
%% matches this manuscript's own usage almost exactly. Chung and Yu's given
%% names, volume, number, pages, and DOI were NOT returned by the search and
%% are deliberately left blank rather than guessed -- fill from the actual
%% paper before submission.
@article{lee2003hierarchical,
  author  = {Lee, Ming-Ling and Chung and Yu},
  title   = {Modeling of Hierarchical Fuzzy Systems},
  journal = {Fuzzy Sets and Systems},
  year    = {2003}
}
"""

TEX_OLD = (
    "the requirement that reduced intermediate variables remain semantically interpretable (Lee, Chung, and\n"
    "Yu 2003; \\emph{cite key to be added -- not present in the current bibliography}). A connected"
)
TEX_NEW = (
    "the requirement that reduced intermediate variables remain semantically interpretable (Lee, Chung, and\n"
    "Yu~\\cite{lee2003hierarchical}). A connected"
)


def main() -> None:
    for f in (BIBFILE, TEXFILE):
        if not f.exists():
            sys.exit(f"ERROR: {f} not found -- run from the repo root "
                     f"(/mnt/c/Research/ANFIS). No changes made.")

    bib_text = BIBFILE.read_text(encoding="utf-8")
    tex_text = TEXFILE.read_text(encoding="utf-8")

    if "lee2003hierarchical" in bib_text:
        sys.exit("ERROR: 'lee2003hierarchical' already appears in "
                  "sn-bibliography.bib -- refusing to double-apply. "
                  "No changes made.")

    n = tex_text.count(TEX_OLD)
    if n == 0:
        sys.exit("ERROR: the Lee/Chung/Yu placeholder text was not found "
                  "in sn-article.tex (exact match expected once). No "
                  "changes written to disk.")
    if n > 1:
        sys.exit(f"ERROR: the placeholder text was found {n} times "
                  f"(expected exactly 1) -- refusing to guess which one. "
                  f"No changes made.")

    new_tex = tex_text.replace(TEX_OLD, TEX_NEW, 1)
    new_bib = bib_text.rstrip("\n") + "\n" + NEW_BIB_ENTRY.lstrip("\n")

    BIBFILE.write_text(new_bib, encoding="utf-8")
    TEXFILE.write_text(new_tex, encoding="utf-8")

    print("OK: added lee2003hierarchical to sn-bibliography.bib and")
    print("    resolved its in-text placeholder in sn-article.tex.")
    print("\nThe Soozanchi et al. placeholder (line ~211) was left")
    print("untouched -- no matching source was found to cite.")
    print("\nReview before committing:")
    print("  git diff manuscript/sn-bibliography.bib manuscript/sn-article.tex")


if __name__ == "__main__":
    main()

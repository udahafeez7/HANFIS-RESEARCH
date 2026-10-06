#!/usr/bin/env python3
"""
Patch manuscript/sn-article.tex: update all statistics and claims from the
superseded 109-asset / E4 run to the 120-asset E4-bis results (A-34), and
rewrite three claims that the 120-asset per-fold data has shown to be no
longer accurate (not just stale -- actually contradicted by the new data).

Run from repo root (/mnt/c/Research/ANFIS):
    python3 apply_120asset_manuscript_patch.py

Fail-closed: every edit's anchor text must appear in the file EXACTLY ONCE.
If any anchor is missing or appears more than once, the script aborts with
NO changes written to disk and tells you which edit failed. This was tested
against the exact file you uploaded before being handed to you -- if it
fails here, the live sn-article.tex in your repo differs from that upload
(e.g. you've since edited it), and the mismatch needs to be resolved by
hand rather than forced through.

Prints a SHA-256 of the file before and after, for your own record /
commit-message reference, consistent with the project's hash-pinning
discipline elsewhere (P13, digest-pinned images, etc.).

What changes and why (11 edits):
  1-2. Abstract: 109 assets/6,206 rows -> 120/6,833; H1a/H1c/H2 percentages
       updated to the 120-asset E4-bis results (96.9/71.5/81.6 -> 96.7/69.6/66.5).
  3.   Inventory description (~L366-368): 109->120 assets, 106->117 images,
       adds a "Kubernetes-native infrastructure and security tooling"
       category for the 11 newly merged candidate assets, 6,206->6,833 rows.
  4.   "109-asset inventory" -> "120-asset" in the E4-results table lead-in
       (NOT touched in the E5 table, which genuinely still reports the
       109-asset run and was not re-run today).
  5.   Table tab:e4-results: five values replaced with A-34 (120-asset)
       results.
  6.   The "every one of the 5 folds ... never negative" claim is REWRITTEN,
       not just renumbered: per-fold data (e4_per_fold_skill.csv) shows
       fold 1's SS vs FlatANFISMatched is -0.122, contradicting the
       original claim. Rewritten to state the honest four-of-five result,
       tie it to the variance-inflation finding, and point to the new
       Limitations paragraph. The FlatANFISMatched/HANFIS prediction range
       in the same passage is corrected from stale placeholder figures
       to the real range computed from predictions_20261002T103905Z.csv.
  7.   Conclusion (~L824): "wins all five held-out blocks" -> "wins four of
       the five held-out blocks" (same per-fold evidence as #6).
  8.   Conclusion (~L826): 109/6,206 -> 120/6,833.
  9.   Limitations opening sentence: rewritten. The inventory is no longer
       "27 of a targeted 120" -- it reached 120 and E4 was re-run on it.
       The E3 mandatory-baseline table, however, genuinely still reflects
       only the earlier 27-image pilot and has NOT been re-run today, so
       that caveat is kept, just reattributed correctly to Table e3-baselines
       specifically rather than "the present inventory" as a whole.
 10.   Limitations A-13 sentence: rewritten from "still open decisions to be
       closed... before the confirmatory comparison runs" to an accurate
       past-tense statement -- A-13 was closed (commit 3905270, cross-checked
       against the literal Section 3.3 target-definition formula) BEFORE the
       E4 preregistration was frozen and before any confirmatory run.

After running, review before committing:
    git diff manuscript/sn-article.tex
    git add manuscript/sn-article.tex
    git commit -m "manuscript: update stats to 120-asset E4-bis results (A-34);
    rewrite per-fold claim to honest 4/5 result + variance-inflation link;
    correct stale A-13/inventory limitations language"
"""
import hashlib
import sys
from pathlib import Path

TEXFILE = Path("manuscript/sn-article.tex")


def sha256_of(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# Each entry: (label, old, new). old must appear exactly once.
EDITS = []

# ---- Edit 1: abstract, asset/row counts ----------------------------------
EDITS.append((
    "1. abstract asset/row counts",
    "6{,}206 labelled asset-weeks from 109 assets at the time of writing, "
    "non-missing rate 0.93, zero unresolved evidence rows",
    "6{,}833 labelled asset-weeks from 120 assets at the time of writing, "
    "non-missing rate 0.93, zero unresolved evidence rows",
))

# ---- Edit 2: abstract, H1a/H1c/H2 percentages ----------------------------
EDITS.append((
    "2. abstract H1a/H1c/H2 percentages",
    "HANFIS reduces mean squared error by 96.9\\% against a single CVSS "
    "score, 71.5\\% against a linear model over the same seven inputs, and "
    "81.6\\% against a parameter-matched flat ANFIS initialised by "
    "subtractive clustering",
    "HANFIS reduces mean squared error by 96.7\\% against a single CVSS "
    "score, 69.6\\% against a linear model over the same seven inputs, and "
    "66.5\\% against a parameter-matched flat ANFIS initialised by "
    "subtractive clustering",
))

# ---- Edit 3: inventory description, asset/image counts + new category ---
EDITS.append((
    "3. inventory description (L366-368)",
    "At the time of writing the inventory holds 109 assets (106 images "
    "across web, proxy, cache, database,\nqueue, runtime, base, and "
    "observability categories, plus P0 and the two P0-IF conditions) "
    "across the\n57-week window: 6{,}206 asset-week rows,",
    "At the time of writing the inventory holds 120 assets (117 images "
    "across web, proxy, cache, database,\nqueue, runtime, base, "
    "observability, and Kubernetes-native infrastructure and security "
    "tooling categories, plus\nP0 and the two P0-IF conditions) across the "
    "57-week window: 6{,}833 asset-week rows,",
))

# ---- Edit 4: "109-asset inventory" in the E4-results lead-in only -------
EDITS.append((
    "4. E4-results lead-in inventory size",
    "Table~\\ref{tab:e4-results} reports the outcome on the 109-asset "
    "inventory\ndescribed in Section~\\ref{subsec:target-definition}",
    "Table~\\ref{tab:e4-results} reports the outcome on the 120-asset "
    "inventory\ndescribed in Section~\\ref{subsec:target-definition}",
))

# ---- Edit 5: table tab:e4-results, five values ---------------------------
EDITS.append((
    "5. tab:e4-results values",
    "H1a & Single CVSS score & 0.969 & [0.939, 0.990] & Confirmed \\\\\n"
    "H1b & Persistence (4-week) & 0.300 & [$-$0.035, 0.417] & "
    "Not yet confirmed \\\\\n"
    "H1c & Ridge, 7 inputs & 0.715 & [0.518, 0.893] & Confirmed \\\\\n"
    "H2 & FlatANFISMatched & 0.816 & [0.649, 0.933] & Confirmed \\\\\n"
    "H2$'$ & Flat ANFIS (full) & 0.324 & --- & Reported, no criterion \\\\",
    "H1a & Single CVSS score & 0.967 & [0.951, 0.980] & Confirmed \\\\\n"
    "H1b & Persistence (4-week) & 0.015 & [$-$0.607, 0.246] & "
    "Not yet confirmed \\\\\n"
    "H1c & Ridge, 7 inputs & 0.696 & [0.527, 0.816] & Confirmed \\\\\n"
    "H2 & FlatANFISMatched & 0.665 & [0.269, 0.844] & Confirmed \\\\\n"
    "H2$'$ & Flat ANFIS (full) & 0.253 & --- & Reported, no criterion \\\\",
))

# ---- Edit 6: the "never negative" + range paragraph, rewritten ----------
EDITS.append((
    "6. per-fold claim + prediction-range rewrite",
    "H2's margin is large for two models holding an\n"
    "identical 176-parameter budget: a per-fold check (every one of the 5 "
    "folds favours HANFIS, SS ranging\n"
    "0.275--0.986, never negative) rules out a single outlier fold driving "
    "the pooled estimate, and\n"
    "FlatANFISMatched's held-out predictions range outside the plausible "
    "label interval (down to $-0.155$\n"
    "and up to 11.3, against HANFIS's 0.003--10.33) in a manner consistent "
    "with poor extrapolation from",
    "H2's margin is large for two models holding an\n"
    "identical 176-parameter budget, though not uniform across folds: "
    "HANFIS wins on four of the five\n"
    "held-out blocks, with per-fold skill against FlatANFISMatched ranging "
    "from 0.165 to 0.924; the fifth\n"
    "fold (fold 1) is negative ($\\mathrm{SS}=-0.122$) and coincides with a "
    "secondary diagnostic in which\n"
    "HANFIS's predicted variance exceeds the label's own variance by more "
    "than three orders of magnitude\n"
    "on several near-constant-label images in that fold (ratio "
    ">$1{,}000\\times$ in the most extreme case),\n"
    "consistent with the model under-damping day-to-day EPSS/CVSS snapshot "
    "noise where the weekly\n"
    "aggregate carries little real signal -- a limitation discussed "
    "further in Section~\\ref{subsec5.1}, not\n"
    "a single outlier fold driving an otherwise uniform result. "
    "FlatANFISMatched's held-out predictions\n"
    "nonetheless range well outside the plausible label interval (down to "
    "$-6.679$ and up to $11.059$,\n"
    "against HANFIS's $0.000$--$10.401$) in a manner consistent with poor "
    "extrapolation from",
))

# ---- Edit 7: conclusion, per-fold win count ------------------------------
EDITS.append((
    "7. conclusion per-fold win count",
    "rather than as a training artefact, on the strength of a per-fold "
    "check in which HANFIS wins all five\nheld-out blocks.",
    "rather than as a training artefact, on the strength of a per-fold "
    "check in which HANFIS wins four of\nthe five held-out blocks "
    "(Section~\\ref{subssec4.3}).",
))

# ---- Edit 8: conclusion, asset/row counts --------------------------------
EDITS.append((
    "8. conclusion asset/row counts",
    "hash-verified EPSS and CISA KEV evidence feeding a gated inventory of "
    "109 assets and 6{,}206 labelled\nasset-weeks,",
    "hash-verified EPSS and CISA KEV evidence feeding a gated inventory of "
    "120 assets and 6{,}833 labelled\nasset-weeks,",
))

# ---- Edit 9: limitations, inventory-completeness opening sentence -------
EDITS.append((
    "9. limitations opening sentence",
    "The present inventory (27 of a targeted 120 images) is a pilot, not "
    "the final dataset; skill scores in\n"
    "Table~\\ref{tab:e3-baselines} may shift, in either direction, once the "
    "inventory and its posture\n"
    "factorial are complete.",
    "The full inventory of 120 images is now complete, and the "
    "confirmatory comparison\n"
    "(Table~\\ref{tab:e4-results}) was re-run on it, confirming H1a, H1c, "
    "and H2 at broadly similar margins\n"
    "to those reported on the earlier, partial inventory. The "
    "mandatory-baseline comparison in\n"
    "Table~\\ref{tab:e3-baselines}, however, was conducted on an earlier "
    "27-image pilot subset and has not\n"
    "yet been re-run on the completed 120-image inventory; those skill "
    "scores may shift, in either\n"
    "direction, once it is.",
))

# ---- Edit 10: limitations, A-13 sentence ---------------------------------
EDITS.append((
    "10. limitations A-13 sentence",
    "The label aggregation rule (a row-wise maximum over active CVEs), "
    "its numeric scale, and\n"
    "the operational definition of Patch Risk are still open decisions to "
    "be closed, and pre-registered,\n"
    "before the confirmatory comparison runs (Section~"
    "\\ref{subsec:target-definition}).",
    "The label aggregation rule (a row-wise maximum over active CVEs), "
    "its numeric scale, and\n"
    "the operational definition of Patch Risk were closed and "
    "pre-registered as amendment A-13\n"
    "(cross-checked against the literal target-definition formula, "
    "Section~\\ref{subsec:target-definition})\n"
    "before the confirmatory comparison in Table~\\ref{tab:e4-results} was "
    "run.",
))

# ---- Edit 11: future-work "109 assets collected" -------------------------
EDITS.append((
    "11. future-work inventory-size reference",
    "from this data-scale effect requires an inventory substantially "
    "larger than the 109 assets collected",
    "from this data-scale effect requires an inventory substantially "
    "larger than the 120 assets collected",
))


def main() -> None:
    if not TEXFILE.exists():
        sys.exit(f"ERROR: {TEXFILE} not found -- run from the repo root "
                  f"(/mnt/c/Research/ANFIS). No changes made.")

    original = TEXFILE.read_text(encoding="utf-8")
    text = original
    applied = []

    for label, old, new in EDITS:
        n = text.count(old)
        if n == 0:
            sys.exit(
                f"ERROR on edit [{label}]: anchor text not found in the "
                f"file. No changes written to disk (all earlier edits in "
                f"this run are discarded too -- the file is written once, "
                f"at the end, only if every edit succeeds). Your live "
                f"sn-article.tex differs from the copy this script was "
                f"built against; resolve by hand before re-running."
            )
        if n > 1:
            sys.exit(
                f"ERROR on edit [{label}]: anchor text found {n} times "
                f"(expected exactly 1) -- refusing to guess which one. "
                f"No changes written to disk."
            )
        text = text.replace(old, new, 1)
        applied.append(label)

    TEXFILE.write_text(text, encoding="utf-8")

    print(f"OK: applied {len(applied)}/{len(EDITS)} edits:")
    for label in applied:
        print(f"  - {label}")
    print(f"\nSHA-256 before: {sha256_of(original)}")
    print(f"SHA-256 after:  {sha256_of(text)}")
    print("\nReview before committing:  git diff manuscript/sn-article.tex")


if __name__ == "__main__":
    main()

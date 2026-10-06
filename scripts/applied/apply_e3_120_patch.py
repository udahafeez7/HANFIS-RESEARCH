#!/usr/bin/env python3
"""
Patch manuscript/sn-article.tex with the E3 mandatory-baseline re-run on the
completed 120-asset inventory (A-35), replacing the stale 27-image-pilot
numbers throughout -- including one claim that REVERSES direction (ridge
vs. persistence), not merely shifts.

Run from repo root (/mnt/c/Research/ANFIS):
    python3 apply_e3_120_patch.py

Headline finding (raw label scale, pooled over 5 grouped-temporal folds,
6,357 rows, 120 assets):
  - Climatology:      RMSE 4.0101  SS_clim 0.000   SS_pers -37.777
  - Single CVSS:      RMSE 3.5372  SS_clim 0.222   SS_pers -29.171
  - Persistence:      RMSE 0.6440  SS_clim 0.974   SS_pers  0.000
  - Ridge, 7 inputs:  RMSE 1.1687  SS_clim 0.915   SS_pers -2.293

Two things changed in KIND, not just degree, versus the 27-image pilot:
  1. CVSS alone now explains ~22% of climatology-relative skill (was ~0%).
  2. Ridge now underperforms persistence by 229% (was +30% improvement) --
     confirmed on EVERY one of the 5 folds (per-fold ss_pers all negative:
     -85.33, -3.72, -34.84, -0.17, -18.55 in results_python/e3_120/
     baselines_20261005T104644Z.csv), so this is not one outlier fold.

Fail-closed: each edit's anchor text must appear in the file EXACTLY ONCE.
Nothing is written to disk unless every edit succeeds.

After running, review before committing:
    git diff manuscript/sn-article.tex
    git add manuscript/sn-article.tex manuscript/fig_e3_baselines.pdf
    git commit -m "manuscript: E3 mandatory baselines re-run on completed
    120-asset inventory (A-35) -- CVSS now explains ~22% of climatology
    skill (was ~0%); ridge now underperforms persistence on every fold
    (was +30%, now -229%), a reversal attributed to linear extrapolation
    as inventory heterogeneity grew. Figure and table updated to match."
"""
import sys
from pathlib import Path

TEXFILE = Path("manuscript/sn-article.tex")

EDITS = []

# ---- 1. Table lead-in row count ----
EDITS.append((
    "1. table lead-in row count",
    "Table~\\ref{tab:e3-baselines} reports the mandatory baselines on the 1{,}431 labelled rows described in",
    "Table~\\ref{tab:e3-baselines} reports the mandatory baselines on the 6{,}357 labelled rows described in",
))

# ---- 2. Table body: four rows ----
EDITS.append((
    "2. tab:e3-baselines values",
    "Climatology & 2.471 & 0.000 & $-23.35$ \\\\\n"
    "Single CVSS score & 2.470 & 0.001 & $-23.33$ \\\\\n"
    "Persistence (causal, 4-week lag) & 0.501 & 0.959 & 0.000 \\\\\n"
    "Ridge regression, all 7 inputs & 0.419 & 0.971 & 0.301 \\\\",
    "Climatology & 4.010 & 0.000 & $-37.78$ \\\\\n"
    "Single CVSS score & 3.537 & 0.222 & $-29.17$ \\\\\n"
    "Persistence (causal, 4-week lag) & 0.644 & 0.974 & 0.000 \\\\\n"
    "Ridge regression, all 7 inputs & 1.169 & 0.915 & $-2.293$ \\\\",
))

# ---- 3. Figure caption ----
EDITS.append((
    "3. fig:e3-baselines caption",
    "A single CVSS score\nadds essentially nothing over climatology; persistence and ridge already recover 96--97\\% of the\nclimatology-relative skill, setting the bar for Section~\\ref{subssec4.3}.",
    "A single CVSS score\nnow adds modest skill over climatology (22\\%, up from essentially nothing on the earlier 27-image\npilot); persistence and ridge separately recover over 90\\% of the climatology-relative skill each, though\nnot of each other -- see Table~\\ref{tab:e3-baselines} for the reversal in their relative standing.",
))

# ---- 4. Main prose paragraph (CVSS / persistence / ridge description) ----
EDITS.append((
    "4. main E3 prose paragraph",
    "A single CVSS score explains essentially none of the realised label ($\\mathrm{SS}_{\\mathrm{clim}}\\approx0$),\n"
    "confirming that static severity alone does not describe which vulnerabilities become exploitable in\n"
    "practice. A naive persistence forecast, in contrast, already recovers 96\\% of the climatology-relative\n"
    "skill: the label is strongly autocorrelated because the set of active CVEs and their EPSS scores change\n"
    "slowly week to week. A linear ridge model over all seven inputs improves on persistence by 30\\% on this\n"
    "pilot ($\\mathrm{SS}_{\\mathrm{pers}}=0.301$), which is the bar hypotheses H1b and H1c\n"
    "(Section~\\ref{sec1}) ask HANFIS to clear or match.",
    "A single CVSS score explains a modest fraction of the realised label's variance\n"
    "($\\mathrm{SS}_{\\mathrm{clim}}=0.222$) -- markedly more than on the earlier 27-image pilot\n"
    "($\\mathrm{SS}_{\\mathrm{clim}}\\approx0$), though still far below persistence or ridge -- confirming that\n"
    "static severity alone remains a poor descriptor of which vulnerabilities become exploitable in practice,\n"
    "even as the larger inventory gives it some traction. A naive persistence forecast, in contrast, recovers\n"
    "97\\% of the climatology-relative skill: the label is strongly autocorrelated because the set of active\n"
    "CVEs and their EPSS scores change slowly week to week. On the completed 120-image inventory, a linear\n"
    "ridge model over all seven inputs no longer improves on persistence -- it is now substantially worse\n"
    "($\\mathrm{SS}_{\\mathrm{pers}}=-2.293$ pooled, raw scale), a reversal from the 27-image pilot's $+0.301$,\n"
    "confirmed on every one of the five grouped-temporal folds rather than driven by one outlier\n"
    "(Section~\\ref{subsec5.1}). This is consistent with a linear model over-extrapolating as the inventory's\n"
    "heterogeneity grew, where persistence's week-to-week copy remains comparatively safe. Persistence is\n"
    "therefore the bar hypotheses H1b and H1c (Section~\\ref{sec1}) ask HANFIS to clear or match; ridge alone\n"
    "no longer clears it either.",
))

# ---- 5. Limitations paragraph (written earlier today, now outdated again) ----
EDITS.append((
    "5. limitations E3 status sentence",
    "The mandatory-baseline comparison in\n"
    "Table~\\ref{tab:e3-baselines}, however, was conducted on an earlier 27-image pilot subset and has not\n"
    "yet been re-run on the completed 120-image inventory; those skill scores may shift, in either\n"
    "direction, once it is.",
    "The mandatory-baseline comparison in\n"
    "Table~\\ref{tab:e3-baselines} has since been re-run on the completed 120-image inventory (6{,}357 rows);\n"
    "the headline shift is that a linear ridge model over all seven inputs, which improved on persistence by\n"
    "30\\% on the 27-image pilot, now underperforms it on every one of the five grouped-temporal folds\n"
    "($\\mathrm{SS}_{\\mathrm{pers}}=-2.293$ pooled, raw scale) -- a reversal, not a refinement, attributed to\n"
    "the linear model over-extrapolating as the inventory's heterogeneity grew, where persistence's\n"
    "week-to-week copy remains comparatively safe.",
))


def main() -> None:
    if not TEXFILE.exists():
        sys.exit(f"ERROR: {TEXFILE} not found -- run from the repo root "
                  f"(/mnt/c/Research/ANFIS). No changes made.")

    text = TEXFILE.read_text(encoding="utf-8")
    applied = []

    for label, old, new in EDITS:
        n = text.count(old)
        if n == 0:
            sys.exit(f"ERROR on edit [{label}]: anchor text not found. "
                      f"No changes written to disk (all edits in this run "
                      f"are discarded together). Resolve by hand.")
        if n > 1:
            sys.exit(f"ERROR on edit [{label}]: anchor found {n} times "
                      f"(expected exactly 1) -- refusing to guess. No "
                      f"changes made.")
        text = text.replace(old, new, 1)
        applied.append(label)

    TEXFILE.write_text(text, encoding="utf-8")
    print(f"OK: applied {len(applied)}/{len(EDITS)} edits:")
    for label in applied:
        print(f"  - {label}")
    print("\nDon't forget: also regenerate manuscript/fig_e3_baselines.pdf")
    print("(see make_e3_figure.py) before committing.")
    print("\nReview before committing:  git diff manuscript/sn-article.tex")


if __name__ == "__main__":
    main()

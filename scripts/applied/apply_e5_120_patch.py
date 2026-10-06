#!/usr/bin/env python3
"""
Patch manuscript/sn-article.tex with the E5 bottleneck-width sweep re-run
on the completed 120-asset inventory (A-36). Both k values' significance
status versus persistence FLIPPED (not just shifted), and the paired
k=1-vs-k=2 comparison grew stronger -- this is rewritten accordingly, not
treated as a number swap.

Run from repo root (/mnt/c/Research/ANFIS):
    python3 apply_e5_120_patch.py

Headline (120 assets, 2,000 image-clustered bootstrap resamples):
  - k=1: SS_pers=0.169 [-0.330, 0.343]  -- CI now CROSSES zero (was
    [0.111, 0.392], significant-positive on the 109-asset inventory).
  - k=2: SS_pers=-0.622 [-2.259, -0.100] -- CI now EXCLUDES zero on the
    negative side (was [-1.681, 0.180], not significant on 109 assets).
  - Paired k=1 minus k=2: d_ss=0.791 [0.354, 2.037], 100% of resamples
    favour k=1 (was 0.414 [0.179, 1.815]) -- stronger than before.
  - k=1 still pooled-RMSE-better on all five folds (same as 109-asset
    result; sign test p=0.0625 unchanged, it's a count-based floor).
  - k=2 obs/param range widened slightly: 0.3-2.9 (was 0.26-2.6).

This also fixes a PRE-EXISTING bug unrelated to the asset-count update:
manuscript/fig_e5_bottleneck_curve.pdf previously showed raw RMSE
(2.5-20 range, titled "confounded, see text") which did not match its own
LaTeX caption at all (a skill-vs-k plot with 95% CIs). The regenerated
figure (see make_e5_figure.py) now matches its caption.

One sub-finding (the clamp_intermediates ablation: costs k=1 0.019 vs.
k=2 0.394 skill) was NOT re-run today -- only the main --ks 1 2 sweep was.
This patch adds an explicit caveat rather than leaving that ambiguous.

Fail-closed: each edit's anchor text must appear in the file EXACTLY ONCE.
Nothing is written to disk unless every edit succeeds.

After running, review before committing:
    git diff manuscript/sn-article.tex
    git add manuscript/sn-article.tex manuscript/fig_e5_bottleneck_curve.pdf
    git commit -m "manuscript: E5 bottleneck sweep re-run on completed
    120-asset inventory (A-36) -- k=1's significance vs persistence
    flipped to not-significant, k=2's flipped to significantly negative;
    paired k=1-vs-k=2 comparison strengthened (d_ss 0.414->0.791). Fixes
    pre-existing fig_e5_bottleneck_curve.pdf/caption mismatch."
"""
import sys
from pathlib import Path

TEXFILE = Path("manuscript/sn-article.tex")

EDITS = []

# ---- 1. Table caption: inventory size ----
EDITS.append((
    "1. tab:e5-results caption inventory size",
    "Table~\\ref{tab:e4-results}), 109-asset inventory.}\\label{tab:e5-results}",
    "Table~\\ref{tab:e4-results}), 120-asset inventory.}\\label{tab:e5-results}",
))

# ---- 2. Table body values ----
EDITS.append((
    "2. tab:e5-results values",
    "1 & 34 / 176 & 0.617 & 0.334\\ [0.111,\\ 0.392] \\\\\n"
    "2 & 178 / 1{,}152 & 0.785 & $-0.080$\\ [$-1.681$,\\ 0.180] \\\\",
    "1 & 34 / 176 & 0.587 & 0.169\\ [$-0.330$,\\ 0.343] \\\\\n"
    "2 & 178 / 1{,}152 & 0.820 & $-0.622$\\ [$-2.259$,\\ $-0.100$] \\\\",
))

# ---- 3. Figure caption: significance direction flipped ----
EDITS.append((
    "3. fig:e5-bottleneck-curve caption",
    "$k{=}1$'s interval excludes zero; $k{=}2$'s spans from strongly negative to\nmildly positive.}\\label{fig:e5-bottleneck-curve}",
    "$k{=}1$'s interval now crosses zero; $k{=}2$'s is entirely\nnegative.}\\label{fig:e5-bottleneck-curve}",
))

# ---- 4. Main prose paragraph: H1b reference + interpretation + paired comparison ----
EDITS.append((
    "4. main E5 prose paragraph",
    "$k{=}1$ recovers skill indistinguishable from HANFIS's own H1b result\n"
    "(Table~\\ref{tab:e4-results}: $\\mathrm{SS}_{\\mathrm{pers}}=0.300$, $[-0.035,0.417]$), as the per-row\n"
    "parity above predicts. $k{=}2$'s interval does not exclude zero: on this inventory, widening the\n"
    "bottleneck demonstrates no benefit. The paired comparison on matched resampled images -- the same\n"
    "resample used for both arms, so sampling noise is shared -- gives\n"
    "$\\mathrm{SS}_{\\mathrm{pers}}(k{=}1)-\\mathrm{SS}_{\\mathrm{pers}}(k{=}2)=0.414$, 95\\% CI\n"
    "$[0.179,1.815]$, excluding zero; $k{=}1$ is pooled-RMSE-better on all five folds (two-sided sign\n"
    "test $p=0.0625$, the floor attainable with five folds).",
    "$k{=}1$ recovers skill broadly consistent with HANFIS's own H1b result\n"
    "(Table~\\ref{tab:e4-results}: $\\mathrm{SS}_{\\mathrm{pers}}=0.015$, $[-0.607,0.246]$) -- both\n"
    "confidence intervals cross zero and overlap substantially, as the per-row parity above predicts,\n"
    "though the point estimates ($0.169$ vs.\\ $0.015$) agree less closely than on the smaller inventory.\n"
    "$k{=}2$'s interval now excludes zero entirely on the negative side: on the completed 120-image\n"
    "inventory, widening the bottleneck is no longer merely unsupported by evidence -- it is\n"
    "significantly worse than persistence. The paired comparison on matched resampled images -- the same\n"
    "resample used for both arms, so sampling noise is shared -- gives\n"
    "$\\mathrm{SS}_{\\mathrm{pers}}(k{=}1)-\\mathrm{SS}_{\\mathrm{pers}}(k{=}2)=0.791$, 95\\% CI\n"
    "$[0.354,2.037]$, excluding zero (100\\% of resamples favour $k{=}1$); $k{=}1$ is pooled-RMSE-better\n"
    "on all five folds (two-sided sign test $p=0.0625$, the floor attainable with five folds) -- the same\n"
    "margin of evidence as on the smaller inventory, even as each arm's marginal significance against\n"
    "persistence flipped in opposite directions.",
))

# ---- 5. obs/param range for k=2 ----
EDITS.append((
    "5. k=2 obs/param range",
    "every $k{=}2$ fold falls under ten\nobservations per parameter (range 0.26--2.6)",
    "every $k{=}2$ fold falls under ten\nobservations per parameter (range 0.3--2.9)",
))

# ---- 6. Flag the clamp-ablation sub-finding as not yet re-run ----
EDITS.append((
    "6. clamp-ablation caveat (not yet re-run at 120 assets)",
    "A\nsecondary diagnostic separates part of this gap from pure data scarcity: disabling the hard clamp on",
    "A\nsecondary diagnostic (109-asset inventory; not yet repeated on the completed 120-asset set) separates\n"
    "part of this gap from pure data scarcity: disabling the hard clamp on",
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
    print("\nDon't forget: also regenerate manuscript/fig_e5_bottleneck_curve.pdf")
    print("(see make_e5_figure.py) before committing.")
    print("\nReview before committing:  git diff manuscript/sn-article.tex")


if __name__ == "__main__":
    main()

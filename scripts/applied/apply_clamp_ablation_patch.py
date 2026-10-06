#!/usr/bin/env python3
"""
Update the clamp_intermediates ablation sentence with the 120-asset re-run
(same direction/interpretation as before, just larger magnitudes -- no
narrative rewrite needed) and remove the "not yet repeated" caveat added
earlier today now that it has been repeated.

Run from repo root (/mnt/c/Research/ANFIS):
    python3 apply_clamp_ablation_patch.py

Headline (120-asset, --clamp-intermediates off vs on, --ks 1 2):
  k=1: SS_pers 0.330 (off) vs 0.169 (on) -> clamp costs 0.161 (was 0.019 on 109 assets)
  k=2: SS_pers 0.192 (off) vs -0.622 (on) -> clamp costs 0.813 (was 0.394 on 109 assets)
Both grew substantially, same direction as before -- strengthens, doesn't
reverse, the existing "v,e harder to estimate reliably as more consequent
parameters compete for them" interpretation.

Fail-closed: anchor text must appear exactly once. Nothing written unless
it succeeds.

After running:
    git diff manuscript/sn-article.tex
    git add manuscript/sn-article.tex
    git commit -m "manuscript: update clamp_intermediates ablation with
    120-asset re-run (A-37) -- cost grew for both k (0.019->0.161, k=1;
    0.394->0.813, k=2), same direction, strengthens existing interpretation"
"""
import sys
from pathlib import Path

TEXFILE = Path("manuscript/sn-article.tex")

OLD = (
    "A\n"
    "secondary diagnostic (109-asset inventory; not yet repeated on the completed 120-asset set) separates\n"
    "part of this gap from pure data scarcity: disabling the hard clamp on\n"
    "$v,e$ (an ablation, not the model HANFIS reports) costs $k{=}1$ only 0.019 of skill but costs $k{=}2$\n"
    "0.394 -- consistent with"
)
NEW = (
    "A\n"
    "secondary diagnostic separates part of this gap from pure data scarcity: disabling the hard clamp on\n"
    "$v,e$ (an ablation, not the model HANFIS reports) costs $k{=}1$ 0.161 of skill but costs $k{=}2$\n"
    "0.813 (both re-run on the completed 120-asset inventory; up from 0.019 and 0.394 respectively\n"
    "on the 27-image pilot) -- consistent with"
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
    print("OK: clamp-ablation sentence updated with 120-asset re-run values.")
    print("Review before committing:  git diff manuscript/sn-article.tex")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Audit the published FuzzyFortify examples against its printed FIS."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from fuzzyfortify_baseline import score_one


PUBLISHED_CASES = [
    ("Data destruction", 34.0, 4.9, 6.9, 1.9, 70.47),
    ("Endpoint DOS", 34.0, 4.2, 6.5, 2.0, 59.56),
    ("Network DOS", 34.0, 3.7, 6.3, 2.2, 55.44),
    ("Inhibit system recovery", 34.0, 4.0, 6.4, 3.1, 57.45),
    ("Resource hijacking", 34.0, 4.8, 7.5, 2.4, 74.60),
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("fuzzyfortify_reproduction_audit.csv"))
    parser.add_argument("--tolerance", type=float, default=0.05)
    parser.add_argument("--allow-gap", action="store_true")
    arguments = parser.parse_args()

    rows = []
    for name, cri, impact, base, exploitability, published in PUBLISHED_CASES:
        reproduced, _ = score_one(cri, impact, base, exploitability)
        rows.append(
            {
                "adversarial_technique": name,
                "complexity_resilience_index": cri,
                "impact": impact,
                "base_score": base,
                "exploitability": exploitability,
                "published_risk_score": published,
                "reproduced_risk_score": reproduced,
                "absolute_difference": abs(reproduced - published),
            }
        )
    result = pd.DataFrame(rows)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(arguments.output, index=False)
    maximum = float(result.absolute_difference.max())
    print(result.to_string(index=False, float_format=lambda value: f"{value:.4f}"))
    print(f"MAX_ABSOLUTE_DIFFERENCE={maximum:.4f}")
    print(f"TOLERANCE={arguments.tolerance:.4f}")
    if maximum > arguments.tolerance:
        print("STATUS=HOLD_FUZZYFORTIFY_REPRODUCTION_GAP")
        if not arguments.allow_gap:
            raise SystemExit(2)
    else:
        print("STATUS=PASS_FUZZYFORTIFY_REPRODUCTION")


if __name__ == "__main__":
    main()

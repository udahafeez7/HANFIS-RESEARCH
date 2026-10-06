#!/usr/bin/env python3
"""Faithful, fail-closed reproduction of the published FuzzyFortify FIS.

The implementation follows Tables 7 and 8 of Hersyah et al. (2025):
four crisp inputs, trapezoidal membership functions, Mamdani min/max
inference, maximum aggregation, and discrete-centroid defuzzification.

It intentionally does not map the seven HANFIS features to the four native
FuzzyFortify inputs. Such a mapping is a study-design decision and must be
declared in the comparison dataset rather than hidden in model code.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


INPUT_COLUMNS = (
    "complexity_resilience_index",
    "impact",
    "base_score",
    "exploitability",
)

CRI_MFS = {
    "low": (1.0, 1.0, 8.0, 15.0),
    "medium": (10.0, 15.0, 18.0, 25.0),
    "high": (20.0, 25.0, 45.0, 55.0),
    "very_high": (50.0, 55.0, 100.0, 100.0),
}
THREAT_MFS = {
    "low": (0.1, 0.1, 3.0, 3.9),
    "medium": (4.0, 4.0, 6.0, 6.9),
    "high": (7.0, 7.0, 8.5, 8.9),
    "critical": (9.0, 9.0, 10.0, 10.0),
}
RISK_MFS = {
    "low": (0.0, 0.0, 19.5, 39.0),
    "medium": (30.0, 40.0, 59.0, 69.0),
    "high": (60.0, 70.0, 79.5, 89.0),
    "critical": (80.0, 90.0, 100.0, 100.0),
}


class FuzzyFortifyGateError(ValueError):
    """Raised when an input or inference result is not scientifically valid."""


def trapmf(x: np.ndarray, limits: tuple[float, float, float, float]) -> np.ndarray:
    a, b, c, d = limits
    if not a <= b <= c <= d:
        raise FuzzyFortifyGateError(f"Invalid trapezoid limits: {limits}")
    values = np.asarray(x, dtype=float)
    result = np.zeros_like(values)
    if b > a:
        rising = (values > a) & (values < b)
        result[rising] = (values[rising] - a) / (b - a)
    result[(values >= b) & (values <= c)] = 1.0
    if d > c:
        falling = (values > c) & (values < d)
        result[falling] = (d - values[falling]) / (d - c)
    return result


def membership(value: float, limits: tuple[float, float, float, float]) -> float:
    return float(trapmf(np.asarray([value]), limits)[0])


def _validate_inputs(cri: float, impact: float, base: float, exploitability: float) -> None:
    values = (cri, impact, base, exploitability)
    if not np.isfinite(values).all():
        raise FuzzyFortifyGateError("All FuzzyFortify inputs must be finite.")
    if not 1.0 <= cri <= 100.0:
        raise FuzzyFortifyGateError("complexity_resilience_index must be in [1, 100].")
    for name, value in zip(INPUT_COLUMNS[1:], values[1:]):
        if not 0.1 <= value <= 10.0:
            raise FuzzyFortifyGateError(f"{name} must be in [0.1, 10].")


def score_one(
    complexity_resilience_index: float,
    impact: float,
    base_score: float,
    exploitability: float,
    universe_step: float = 0.01,
) -> tuple[float, dict[str, float]]:
    """Return crisp risk score and output activation levels."""
    _validate_inputs(complexity_resilience_index, impact, base_score, exploitability)
    if universe_step <= 0 or 100.0 / universe_step > 2_000_000:
        raise FuzzyFortifyGateError("universe_step must be positive and computationally bounded.")

    cri = {name: membership(complexity_resilience_index, mf) for name, mf in CRI_MFS.items()}
    imp = {name: membership(impact, mf) for name, mf in THREAT_MFS.items()}
    base = {name: membership(base_score, mf) for name, mf in THREAT_MFS.items()}
    exp = {name: membership(exploitability, mf) for name, mf in THREAT_MFS.items()}

    # Table 8. AND=min, OR=max. Rule 6 says "Catastrophic", while Table 7
    # calls the corresponding output set "Critical"; the latter is used here.
    rule_1 = max(min(cri["low"], imp["low"]), min(base["low"], exp["low"]))
    rule_2 = max(cri["medium"], imp["medium"], base["medium"], exp["medium"])
    rule_3 = min(cri["high"], imp["medium"], base["high"], exp["low"])
    rule_4 = min(cri["high"], imp["high"], base["high"], exp["high"])
    rule_5 = min(max(cri["high"], imp["high"]), max(base["high"], exp["high"]))
    rule_6 = max(
        min(cri["very_high"], imp["critical"]),
        min(base["critical"], exp["critical"]),
    )
    activation = {
        "low": rule_1,
        "medium": max(rule_2, rule_3),
        "high": max(rule_4, rule_5),
        "critical": rule_6,
    }

    universe = np.arange(0.0, 100.0 + universe_step / 2.0, universe_step)
    clipped = [
        np.minimum(activation[name], trapmf(universe, RISK_MFS[name]))
        for name in RISK_MFS
    ]
    aggregate = np.maximum.reduce(clipped)
    denominator = float(aggregate.sum())
    if denominator <= 0:
        raise FuzzyFortifyGateError(
            "No published FuzzyFortify rule fired; refusing to invent a fallback score."
        )
    risk = float(np.sum(universe * aggregate) / denominator)
    return risk, activation


def predict_frame(frame: pd.DataFrame) -> pd.DataFrame:
    missing = [column for column in INPUT_COLUMNS if column not in frame.columns]
    if missing:
        raise FuzzyFortifyGateError("Missing native FuzzyFortify columns: " + ", ".join(missing))
    output = frame.copy()
    scores: list[float] = []
    activations: list[dict[str, float]] = []
    for row in output.loc[:, INPUT_COLUMNS].itertuples(index=False, name=None):
        value, activation = score_one(*map(float, row))
        scores.append(value)
        activations.append(activation)
    output["fuzzyfortify_risk_score"] = scores
    for label in RISK_MFS:
        output[f"activation_{label}"] = [item[label] for item in activations]
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_csv", type=Path)
    parser.add_argument("output_csv", type=Path)
    arguments = parser.parse_args()
    frame = pd.read_csv(arguments.input_csv)
    predicted = predict_frame(frame)
    arguments.output_csv.parent.mkdir(parents=True, exist_ok=True)
    predicted.to_csv(arguments.output_csv, index=False)
    print(f"ROWS={len(predicted)}")
    print(f"OUTPUT={arguments.output_csv}")
    print("STATUS=PASS_FUZZYFORTIFY_INFERENCE")


if __name__ == "__main__":
    main()

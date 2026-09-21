#!/usr/bin/env python3
"""Fail-closed promotion gate from intake to the HANFIS source event table."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


class SourceGateError(ValueError):
    pass


def fail(message: str) -> None:
    raise SourceGateError(message)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    try:
        contract = json.loads(args.contract.read_text(encoding="utf-8"))
        required = list(contract["required_fields"])
        df = pd.read_csv(args.input, keep_default_na=False)
        missing_columns = sorted(set(required) - set(df.columns))
        if missing_columns:
            fail("Required fields missing: " + ", ".join(missing_columns))
        if df.empty:
            fail("Source intake has zero rows.")
        empty_fields = [field for field in required if df[field].astype(str).str.strip().eq("").any()]
        if empty_fields:
            fail("Required values missing in: " + ", ".join(empty_fields))
        if df["event_id"].astype(str).duplicated().any():
            fail("event_id values are not unique.")

        parsed_time = pd.to_datetime(df["timestamp_utc"], utc=True, errors="coerce")
        if parsed_time.isna().any():
            fail("timestamp_utc contains invalid timestamps.")
        df["timestamp_utc"] = parsed_time.dt.strftime("%Y-%m-%dT%H:%M:%SZ")

        for field in ("event_id", "asset_id", "evidence_id", "evidence_source", "attack_technique"):
            if df[field].astype(str).str.strip().eq("").any():
                fail(f"{field} contains an empty provenance value.")

        for field, bounds in contract["numeric_ranges"].items():
            values = pd.to_numeric(df[field], errors="coerce")
            if values.isna().any() or not np.isfinite(values).all():
                fail(f"{field} contains a missing or non-numeric value.")
            lower, upper = map(float, bounds)
            if not values.between(lower, upper, inclusive="both").all():
                fail(f"{field} is outside [{lower}, {upper}].")
            df[field] = values

        if "record_role" in df.columns:
            reference_only = df["record_role"].astype(str).str.lower().eq("external_reference_only")
            if reference_only.any():
                fail("external_reference_only rows cannot be promoted to training data.")

        promoted = df[required].copy()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        promoted.to_csv(args.output, index=False)
    except (SourceGateError, KeyError, OSError, json.JSONDecodeError, pd.errors.ParserError) as exc:
        print(f"GATE_FAIL={type(exc).__name__}:{exc}")
        print("STATUS=HOLD_SOURCE_PROMOTION")
        raise SystemExit(2)

    print(f"PROMOTED_ROWS={len(promoted)}")
    print(f"OUTPUT={args.output}")
    print("STATUS=PASS_SOURCE_PROMOTION_V1_2")


if __name__ == "__main__":
    main()

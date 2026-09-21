#!/usr/bin/env python3
"""Create row-level QC for HANFIS source intake without inventing values."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--qc-output", type=Path, required=True)
    args = parser.parse_args()

    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    required = list(contract["required_fields"])
    df = pd.read_csv(args.input, keep_default_na=False, dtype=str)

    missing_columns = sorted(set(required) - set(df.columns))
    if missing_columns:
        print("MISSING_COLUMNS=" + ",".join(missing_columns))
        print("STATUS=HOLD_SOURCE_SCHEMA")
        raise SystemExit(2)

    qc_rows: list[dict[str, object]] = []
    ranges = contract["numeric_ranges"]
    for index, row in df.iterrows():
        missing = [field for field in required if not str(row[field]).strip()]
        invalid_numeric: list[str] = []
        out_of_range: list[str] = []
        for field, bounds in ranges.items():
            raw = str(row[field]).strip()
            if not raw:
                continue
            try:
                value = float(raw)
            except ValueError:
                invalid_numeric.append(field)
                continue
            if not np.isfinite(value):
                invalid_numeric.append(field)
            elif not float(bounds[0]) <= value <= float(bounds[1]):
                out_of_range.append(field)

        reference_only = str(row.get("record_role", "")).strip().lower() == "external_reference_only"
        eligible = not missing and not invalid_numeric and not out_of_range and not reference_only
        qc_rows.append(
            {
                "row_number": index + 2,
                "event_id": row["event_id"],
                "missing_fields": "|".join(missing),
                "invalid_numeric_fields": "|".join(invalid_numeric),
                "out_of_range_fields": "|".join(out_of_range),
                "record_role": row.get("record_role", ""),
                "eligible_for_promotion": eligible,
            }
        )

    qc = pd.DataFrame(qc_rows)
    args.qc_output.parent.mkdir(parents=True, exist_ok=True)
    qc.to_csv(args.qc_output, index=False)
    eligible_count = int(qc["eligible_for_promotion"].sum()) if len(qc) else 0

    print(f"SOURCE_ROWS={len(df)}")
    print(f"ELIGIBLE_ROWS={eligible_count}")
    print(f"HELD_ROWS={len(df) - eligible_count}")
    print(f"QC_OUTPUT={args.qc_output}")
    print("STATUS=" + ("PASS_SOURCE_INTAKE_QC" if len(df) and eligible_count == len(df) else "HOLD_SOURCE_INTAKE_QC"))


if __name__ == "__main__":
    main()

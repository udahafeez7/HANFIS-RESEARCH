#!/usr/bin/env python3
"""
Validate and normalize raw HANFIS cybersecurity data.

Input:
    data/real/hanfis_source_data.csv

Output:
    data/processed/hanfis_normalized_source.csv

The raw source CSV is never modified.
"""

import csv
import json
import math
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

SOURCE_CSV = PROJECT_ROOT / "data" / "real" / "hanfis_source_data.csv"
SOURCE_SCHEMA = PROJECT_ROOT / "configs" / "anfis_source_schema.json"
OUTPUT_CSV = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "hanfis_normalized_source.csv"
)

IDENTITY_FIELDS = [
    "event_id",
    "timestamp_utc",
    "asset_id",
]

INPUT_FIELDS = [
    "cvss",
    "exploitability",
    "patch_risk",
    "mfa_risk",
    "kubernetes_exposure",
    "asset_criticality",
    "threat_intelligence",
]

EXPECTED_FIELDS = IDENTITY_FIELDS + INPUT_FIELDS


def load_schema(schema_path):
    """Load the raw-source JSON schema."""
    if not schema_path.exists():
        raise FileNotFoundError(
            f"Source schema not found: {schema_path}"
        )

    with schema_path.open("r", encoding="utf-8") as file:
        schema = json.load(file)

    schema_fields = list(schema.get("fields", {}).keys())

    if schema_fields != EXPECTED_FIELDS:
        raise ValueError(
            "Schema fields do not match the expected HANFIS fields.\n"
            f"Expected: {EXPECTED_FIELDS}\n"
            f"Schema:   {schema_fields}"
        )

    return schema


def validate_timestamp(value, row_number):
    """Validate an ISO 8601 timestamp and require UTC."""
    timestamp = value.strip()

    if not timestamp:
        raise ValueError(
            f"Row {row_number}: timestamp_utc is empty."
        )

    if not timestamp.endswith(("Z", "+00:00")):
        raise ValueError(
            f"Row {row_number}: timestamp_utc must use UTC "
            "and end with 'Z' or '+00:00'."
        )

    try:
        datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError(
            f"Row {row_number}: invalid ISO 8601 timestamp: "
            f"{timestamp}"
        ) from error


def parse_numeric_value(field, raw_value, field_schema, row_number):
    """Convert and validate one numeric input."""
    value_text = raw_value.strip()

    if value_text == "":
        raise ValueError(
            f"Row {row_number}: {field} is empty."
        )

    expected_type = field_schema.get("type")

    try:
        if expected_type == "integer":
            numeric_value = float(value_text)

            if not numeric_value.is_integer():
                raise ValueError(
                    f"Row {row_number}: {field} must be an integer."
                )

            value = int(numeric_value)
        else:
            value = float(value_text)
    except ValueError as error:
        raise ValueError(
            f"Row {row_number}: {field} contains an invalid "
            f"numeric value: {raw_value!r}"
        ) from error

    if not math.isfinite(float(value)):
        raise ValueError(
            f"Row {row_number}: {field} must be a finite number."
        )

    minimum = field_schema["minimum"]
    maximum = field_schema["maximum"]

    if not minimum <= value <= maximum:
        raise ValueError(
            f"Row {row_number}: {field}={value} is outside "
            f"the permitted range [{minimum}, {maximum}]."
        )

    return value


def normalize_inputs(values):
    """Normalize the seven HANFIS inputs to the range 0–1."""
    return {
        "cvss": values["cvss"] / 10.0,
        "exploitability": values["exploitability"] / 10.0,
        "patch_risk": values["patch_risk"] / 2.0,
        "mfa_risk": values["mfa_risk"] / 2.0,
        "kubernetes_exposure":
            values["kubernetes_exposure"] / 10.0,
        "asset_criticality":
            (values["asset_criticality"] - 1.0) / 4.0,
        "threat_intelligence": values["threat_intelligence"],
    }


def validate_normalized_values(values, row_number):
    """Confirm that every normalized input is within 0–1."""
    for field, value in values.items():
        if not 0.0 <= value <= 1.0:
            raise ValueError(
                f"Row {row_number}: normalized {field}={value} "
                "is outside the range [0.0, 1.0]."
            )


def format_normalized_value(value):
    """Store normalized values consistently."""
    return f"{value:.6f}"


def prepare_real_data():
    """Validate the raw CSV and write normalized source data."""
    schema = load_schema(SOURCE_SCHEMA)
    field_schemas = schema["fields"]

    if not SOURCE_CSV.exists():
        raise FileNotFoundError(
            f"Raw source CSV not found: {SOURCE_CSV}"
        )

    normalized_rows = []
    seen_event_ids = set()

    with SOURCE_CSV.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as source_file:
        reader = csv.DictReader(source_file)

        if reader.fieldnames != EXPECTED_FIELDS:
            raise ValueError(
                "CSV header does not match the source schema.\n"
                f"Expected: {EXPECTED_FIELDS}\n"
                f"CSV:      {reader.fieldnames}"
            )

        for row_number, row in enumerate(reader, start=2):
            if None in row:
                raise ValueError(
                    f"Row {row_number}: too many CSV columns."
                )

            if any(
                value is None or value.strip() == ""
                for value in row.values()
            ):
                raise ValueError(
                    f"Row {row_number}: missing values are not allowed."
                )

            event_id = row["event_id"].strip()
            timestamp_utc = row["timestamp_utc"].strip()
            asset_id = row["asset_id"].strip()

            if event_id in seen_event_ids:
                raise ValueError(
                    f"Row {row_number}: duplicate event_id "
                    f"{event_id!r}."
                )

            seen_event_ids.add(event_id)
            validate_timestamp(timestamp_utc, row_number)

            raw_values = {
                field: parse_numeric_value(
                    field,
                    row[field],
                    field_schemas[field],
                    row_number,
                )
                for field in INPUT_FIELDS
            }

            normalized_values = normalize_inputs(raw_values)
            validate_normalized_values(
                normalized_values,
                row_number,
            )

            output_row = {
                "event_id": event_id,
                "timestamp_utc": timestamp_utc,
                "asset_id": asset_id,
            }

            output_row.update(
                {
                    field: format_normalized_value(
                        normalized_values[field]
                    )
                    for field in INPUT_FIELDS
                }
            )

            normalized_rows.append(output_row)

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_CSV.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as output_file:
        writer = csv.DictWriter(
            output_file,
            fieldnames=EXPECTED_FIELDS,
        )
        writer.writeheader()
        writer.writerows(normalized_rows)

    print("VALIDATION PASSED")
    print(f"Rows processed : {len(normalized_rows)}")
    print(f"Unique events  : {len(seen_event_ids)}")
    print(f"Raw file kept  : {SOURCE_CSV}")
    print(f"Output written : {OUTPUT_CSV}")

    if not normalized_rows:
        print(
            "NOTE: The source CSV currently contains only a header; "
            "there were no data rows to normalize."
        )


if __name__ == "__main__":
    try:
        prepare_real_data()
    except (
        FileNotFoundError,
        json.JSONDecodeError,
        ValueError,
    ) as error:
        raise SystemExit(f"VALIDATION FAILED: {error}")
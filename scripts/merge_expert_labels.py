#!/usr/bin/env python3
"""Merge normalized HANFIS inputs with independent expert labels."""

import csv
import json
import math
from pathlib import Path
from datetime import datetime


PROJECT_ROOT = Path(__file__).resolve().parents[1]

SOURCE_CSV = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "hanfis_normalized_source.csv"
)

LABEL_CSV = (
    PROJECT_ROOT
    / "data"
    / "real"
    / "hanfis_expert_labels.csv"
)

LABEL_SCHEMA = (
    PROJECT_ROOT
    / "configs"
    / "hanfis_expert_label_schema.json"
)

OUTPUT_CSV = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "hanfis_real_data.csv"
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

TARGET_FIELDS = [
    "vulnerability_target",
    "environment_target",
    "dynamic_risk_target",
]

SOURCE_FIELDS = IDENTITY_FIELDS + INPUT_FIELDS
LABEL_FIELDS = [
    "event_id",
    "labeler_id",
    "label_timestamp_utc",
    "vulnerability_target",
    "environment_target",
    "dynamic_risk_target",
    "label_confidence",
]

OUTPUT_FIELDS = SOURCE_FIELDS + LABEL_FIELDS[1:]


def load_label_schema():
    """Validate the expert-label data contract."""
    if not LABEL_SCHEMA.exists():
        raise FileNotFoundError(
            f"Expert-label schema not found: {LABEL_SCHEMA}"
        )

    with LABEL_SCHEMA.open("r", encoding="utf-8") as file:
        schema = json.load(file)

    schema_fields = list(schema.get("fields", {}).keys())

    if schema_fields != LABEL_FIELDS:
        raise ValueError(
            "Expert-label schema fields do not match.\n"
            f"Expected: {LABEL_FIELDS}\n"
            f"Schema:   {schema_fields}"
        )


def parse_unit_interval(field, raw_value, row_number, source_name):
    """Parse a finite numeric value constrained to 0–1."""
    value_text = raw_value.strip()

    if value_text == "":
        raise ValueError(
            f"{source_name} row {row_number}: {field} is empty."
        )

    try:
        value = float(value_text)
    except ValueError as error:
        raise ValueError(
            f"{source_name} row {row_number}: "
            f"{field} is not numeric: {raw_value!r}."
        ) from error

    if not math.isfinite(value):
        raise ValueError(
            f"{source_name} row {row_number}: "
            f"{field} must be finite."
        )

    if not 0.0 <= value <= 1.0:
        raise ValueError(
            f"{source_name} row {row_number}: "
            f"{field}={value} is outside [0.0, 1.0]."
        )

    return value


def read_normalized_source():
    """Read and revalidate normalized source events."""
    if not SOURCE_CSV.exists():
        raise FileNotFoundError(
            f"Normalized source CSV not found: {SOURCE_CSV}"
        )

    rows = []
    events = {}

    with SOURCE_CSV.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(file)

        if reader.fieldnames != SOURCE_FIELDS:
            raise ValueError(
                "Normalized-source header does not match.\n"
                f"Expected: {SOURCE_FIELDS}\n"
                f"CSV:      {reader.fieldnames}"
            )

        for row_number, row in enumerate(reader, start=2):
            if None in row:
                raise ValueError(
                    f"Source row {row_number}: too many columns."
                )

            if any(
                value is None or value.strip() == ""
                for value in row.values()
            ):
                raise ValueError(
                    f"Source row {row_number}: missing value."
                )

            event_id = row["event_id"].strip()

            if event_id in events:
                raise ValueError(
                    f"Source row {row_number}: duplicate event_id "
                    f"{event_id!r}."
                )

            clean_row = {
                field: row[field].strip()
                for field in IDENTITY_FIELDS
            }

            for field in INPUT_FIELDS:
                value = parse_unit_interval(
                    field,
                    row[field],
                    row_number,
                    "Source",
                )
                clean_row[field] = f"{value:.6f}"

            rows.append(clean_row)
            events[event_id] = clean_row

    return rows, events

def validate_label_timestamp(value, row_number):
    """Validate the expert-label timestamp as ISO 8601 UTC."""
    timestamp = value.strip()

    if not timestamp.endswith(("Z", "+00:00")):
        raise ValueError(
            f"Label row {row_number}: label_timestamp_utc "
            "must use UTC."
        )

    try:
        datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError(
            f"Label row {row_number}: invalid label timestamp "
            f"{timestamp!r}."
        ) from error

    return timestamp

def read_expert_labels():
    """Read independently assigned expert targets."""
    if not LABEL_CSV.exists():
        raise FileNotFoundError(
            f"Expert-label CSV not found: {LABEL_CSV}"
        )

    labels = {}

    with LABEL_CSV.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(file)

        if reader.fieldnames != LABEL_FIELDS:
            raise ValueError(
                "Expert-label header does not match.\n"
                f"Expected: {LABEL_FIELDS}\n"
                f"CSV:      {reader.fieldnames}"
            )

        for row_number, row in enumerate(reader, start=2):
            if None in row:
                raise ValueError(
                    f"Label row {row_number}: too many columns."
                )

            if any(
                value is None or value.strip() == ""
                for value in row.values()
            ):
                raise ValueError(
                    f"Label row {row_number}: missing value."
                )

            event_id = row["event_id"].strip()

            if event_id in labels:
                raise ValueError(
                    f"Label row {row_number}: duplicate event_id "
                    f"{event_id!r}."
                )

            labeler_id = row["labeler_id"].strip()

            if not labeler_id:
                raise ValueError(
                    f"Label row {row_number}: labeler_id is empty."
                )

            label_timestamp = validate_label_timestamp(
                row["label_timestamp_utc"],
                row_number,
            )

            label_values = {
                "labeler_id": labeler_id,
                "label_timestamp_utc": label_timestamp,
            }

            for field in TARGET_FIELDS:
                value = parse_unit_interval(
                    field,
                    row[field],
                    row_number,
                    "Label",
                )
                label_values[field] = f"{value:.6f}"

            confidence = parse_unit_interval(
                "label_confidence",
                row["label_confidence"],
                row_number,
                "Label",
            )

            label_values["label_confidence"] = f"{confidence:.6f}"
            labels[event_id] = label_values

    return labels


def merge_real_data():
    """Perform a strict one-to-one event_id merge."""
    load_label_schema()
    source_rows, source_events = read_normalized_source()
    labels = read_expert_labels()

    source_ids = set(source_events)
    label_ids = set(labels)

    missing_labels = sorted(source_ids - label_ids)
    orphan_labels = sorted(label_ids - source_ids)

    if missing_labels:
        raise ValueError(
            "Source events without expert labels: "
            + ", ".join(missing_labels)
        )

    if orphan_labels:
        raise ValueError(
            "Expert labels without source events: "
            + ", ".join(orphan_labels)
        )

    merged_rows = []

    for source_row in source_rows:
        event_id = source_row["event_id"]
        merged_row = dict(source_row)
        merged_row.update(labels[event_id])
        merged_rows.append(merged_row)

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_CSV.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=OUTPUT_FIELDS,
        )
        writer.writeheader()
        writer.writerows(merged_rows)

    print("INTEGRATION PASSED")
    print(f"Source events   : {len(source_rows)}")
    print(f"Expert labels   : {len(labels)}")
    print(f"Merged rows     : {len(merged_rows)}")
    print("Join rule       : exact one-to-one event_id")
    print(f"Output written  : {OUTPUT_CSV}")


if __name__ == "__main__":
    try:
        merge_real_data()
    except (
        FileNotFoundError,
        json.JSONDecodeError,
        ValueError,
    ) as error:
        raise SystemExit(f"INTEGRATION FAILED: {error}")
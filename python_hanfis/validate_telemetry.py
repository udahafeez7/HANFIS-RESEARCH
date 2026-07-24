#!/usr/bin/env python3
"""Validate a HANFIS telemetry record against its JSON Schema."""

import argparse
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SCHEMA = PROJECT_ROOT / "schemas" / "hanfis-telemetry-v1.schema.json"


def load_json(file_path: Path) -> dict:
    """Load and return a JSON document."""
    try:
        with file_path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"GAGAL: File tidak ditemukan: {file_path}", file=sys.stderr)
        raise SystemExit(2)
    except json.JSONDecodeError as error:
        print(
            f"GAGAL: Sintaks JSON tidak valid pada "
            f"baris {error.lineno}, kolom {error.colno}: {error.msg}",
            file=sys.stderr,
        )
        raise SystemExit(2)


def format_path(error_path) -> str:
    """Convert a validation-error path into a readable field path."""
    parts = [str(part) for part in error_path]
    return " -> ".join(parts) if parts else "<root>"


def validate_record(record_path: Path, schema_path: Path) -> int:
    """Validate one telemetry record and return a process exit code."""
    schema = load_json(schema_path)
    record = load_json(record_path)

    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as error:
        print(f"GAGAL: JSON Schema tidak valid: {error.message}", file=sys.stderr)
        return 2

    validator = Draft202012Validator(
    schema,
    format_checker=FormatChecker(),
)
    errors = sorted(
        validator.iter_errors(record),
        key=lambda error: list(error.absolute_path),
    )

    if not errors:
        print("BERHASIL: Record sesuai dengan JSON Schema")
        print(f"Record : {record_path}")
        print(f"Schema : {schema_path}")
        return 0

    print(
        f"GAGAL: Ditemukan {len(errors)} kesalahan validasi.",
        file=sys.stderr,
    )

    for number, error in enumerate(errors, start=1):
        print(
            f"{number}. Field   : {format_path(error.absolute_path)}",
            file=sys.stderr,
        )
        print(f"   Masalah : {error.message}", file=sys.stderr)

    return 1


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Memvalidasi satu record telemetri HANFIS terhadap "
            "JSON Schema Draft 2020-12."
        )
    )
    parser.add_argument(
        "record",
        type=Path,
        help="Lokasi file record telemetri JSON.",
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=DEFAULT_SCHEMA,
        help=f"Lokasi JSON Schema (default: {DEFAULT_SCHEMA}).",
    )
    return parser.parse_args()


def main() -> int:
    """Run the command-line validator."""
    arguments = parse_arguments()

    record_path = arguments.record.expanduser().resolve()
    schema_path = arguments.schema.expanduser().resolve()

    return validate_record(record_path, schema_path)


if __name__ == "__main__":
    raise SystemExit(main())
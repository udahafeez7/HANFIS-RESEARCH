#!/usr/bin/env python3
"""
Automated tests for the HANFIS validation-normalization pipeline.

All test CSV files are created inside temporary directories.
The real research dataset is never modified.
"""

import csv
import importlib.util
import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "prepare_real_data.py"

spec = importlib.util.spec_from_file_location(
    "prepare_real_data",
    SCRIPT_PATH,
)

prepare_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare_module)


VALID_ROW = [
    "TEST-EVT-0001",
    "2026-07-31T04:00:00Z",
    "TEST-ASSET-01",
    "8.5",
    "7.0",
    "1",
    "2",
    "6.0",
    "4",
    "0.8",
]


class TestPrepareRealData(unittest.TestCase):
    """Test validation and normalization of HANFIS source data."""

    def setUp(self):
        """Create isolated temporary input and output locations."""
        self.temp_directory = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_directory.name)

        self.source_csv = self.temp_path / "hanfis_source_data.csv"
        self.output_csv = (
            self.temp_path / "hanfis_normalized_source.csv"
        )

        self.original_source_csv = prepare_module.SOURCE_CSV
        self.original_output_csv = prepare_module.OUTPUT_CSV

        prepare_module.SOURCE_CSV = self.source_csv
        prepare_module.OUTPUT_CSV = self.output_csv

    def tearDown(self):
        """Restore original paths and remove temporary files."""
        prepare_module.SOURCE_CSV = self.original_source_csv
        prepare_module.OUTPUT_CSV = self.original_output_csv
        self.temp_directory.cleanup()

    def write_csv(self, rows, header=None):
        """Write a controlled test CSV."""
        selected_header = (
            prepare_module.EXPECTED_FIELDS
            if header is None
            else header
        )

        with self.source_csv.open(
            "w",
            encoding="utf-8",
            newline="",
        ) as file:
            writer = csv.writer(file)
            writer.writerow(selected_header)
            writer.writerows(rows)

    def run_pipeline(self):
        """Run the pipeline while suppressing normal console output."""
        output_buffer = io.StringIO()

        with redirect_stdout(output_buffer):
            prepare_module.prepare_real_data()

        return output_buffer.getvalue()

    def test_valid_row_is_normalized_correctly(self):
        """A valid cybersecurity event must pass and normalize."""
        self.write_csv([VALID_ROW])
        output = self.run_pipeline()

        self.assertIn("VALIDATION PASSED", output)
        self.assertTrue(self.output_csv.exists())

        with self.output_csv.open(
            "r",
            encoding="utf-8",
            newline="",
        ) as file:
            result = next(csv.DictReader(file))

        expected_values = {
            "cvss": "0.850000",
            "exploitability": "0.700000",
            "patch_risk": "0.500000",
            "mfa_risk": "1.000000",
            "kubernetes_exposure": "0.600000",
            "asset_criticality": "0.750000",
            "threat_intelligence": "0.800000",
        }

        for field, expected in expected_values.items():
            self.assertEqual(result[field], expected)

        self.assertEqual(result["event_id"], "TEST-EVT-0001")
        self.assertEqual(result["asset_id"], "TEST-ASSET-01")

    def test_duplicate_event_id_is_rejected(self):
        """Two rows must not share the same event_id."""
        second_row = VALID_ROW.copy()
        second_row[1] = "2026-07-31T05:00:00Z"

        self.write_csv([VALID_ROW, second_row])

        with self.assertRaisesRegex(
            ValueError,
            "duplicate event_id",
        ):
            self.run_pipeline()

    def test_missing_value_is_rejected(self):
        """An empty required value must be rejected."""
        invalid_row = VALID_ROW.copy()
        invalid_row[3] = ""

        self.write_csv([invalid_row])

        with self.assertRaisesRegex(
            ValueError,
            "missing values are not allowed",
        ):
            self.run_pipeline()

    def test_cvss_above_maximum_is_rejected(self):
        """CVSS greater than 10 must be rejected."""
        invalid_row = VALID_ROW.copy()
        invalid_row[3] = "10.5"

        self.write_csv([invalid_row])

        with self.assertRaisesRegex(
            ValueError,
            "outside the permitted range",
        ):
            self.run_pipeline()

    def test_negative_exploitability_is_rejected(self):
        """Negative exploitability must be rejected."""
        invalid_row = VALID_ROW.copy()
        invalid_row[4] = "-1"

        self.write_csv([invalid_row])

        with self.assertRaisesRegex(
            ValueError,
            "outside the permitted range",
        ):
            self.run_pipeline()

    def test_non_integer_patch_risk_is_rejected(self):
        """Patch risk must use an integer category."""
        invalid_row = VALID_ROW.copy()
        invalid_row[5] = "1.5"

        self.write_csv([invalid_row])

        with self.assertRaisesRegex(
            ValueError,
            "invalid numeric value",
        ):
            self.run_pipeline()

    def test_non_utc_timestamp_is_rejected(self):
        """Timestamp must be explicitly expressed in UTC."""
        invalid_row = VALID_ROW.copy()
        invalid_row[1] = "2026-07-31T11:00:00+07:00"

        self.write_csv([invalid_row])

        with self.assertRaisesRegex(
            ValueError,
            "must use UTC",
        ):
            self.run_pipeline()

    def test_non_finite_value_is_rejected(self):
        """NaN and infinite numeric values must be rejected."""
        invalid_row = VALID_ROW.copy()
        invalid_row[9] = "nan"

        self.write_csv([invalid_row])

        with self.assertRaisesRegex(
            ValueError,
            "must be a finite number",
        ):
            self.run_pipeline()

    def test_incorrect_header_is_rejected(self):
        """Unexpected or reordered CSV fields must be rejected."""
        incorrect_header = prepare_module.EXPECTED_FIELDS + [
            "unexpected_column"
        ]
        invalid_row = VALID_ROW + ["unexpected_value"]

        self.write_csv(
            [invalid_row],
            header=incorrect_header,
        )

        with self.assertRaisesRegex(
            ValueError,
            "CSV header does not match",
        ):
            self.run_pipeline()


if __name__ == "__main__":
    unittest.main(verbosity=2)
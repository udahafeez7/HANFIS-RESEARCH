"""Automated tests for the HANFIS telemetry validator."""

import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

from python_hanfis.validate_telemetry import (
    DEFAULT_SCHEMA,
    validate_record,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = PROJECT_ROOT / "schemas" / "examples"


class TestTelemetryValidation(unittest.TestCase):

    def check_record(self, filename: str, expected_code: int) -> None:
        output = StringIO()

        with redirect_stdout(output), redirect_stderr(output):
            result = validate_record(
                EXAMPLES / filename,
                DEFAULT_SCHEMA,
            )

        self.assertEqual(
            result,
            expected_code,
            msg=f"Unexpected result for {filename}:\n{output.getvalue()}",
        )

    def test_valid_training_record(self):
        self.check_record("valid-training-record.json", 0)

    def test_valid_inference_record(self):
        self.check_record("valid-inference-record.json", 0)

    def test_invalid_out_of_range_record(self):
        self.check_record("invalid-out-of-range-record.json", 1)

    def test_invalid_datetime_record(self):
        self.check_record("invalid-datetime-record.json", 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
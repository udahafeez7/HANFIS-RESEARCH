"""Tests for HANFIS CSV dataset validation."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PYTHON_HANFIS_DIR = PROJECT_ROOT / "python_hanfis"

if str(PYTHON_HANFIS_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_HANFIS_DIR))

from hanfis_7input_experiment import FEATURES, load_dataset


TARGET_COLUMNS = [
    "vulnerability_target",
    "environment_target",
    "dynamic_risk_target",
]

REQUIRED_COLUMNS = FEATURES + TARGET_COLUMNS


class TestHanfisDatasetValidation(unittest.TestCase):

    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)

        self.csv_path = (
            Path(self.temporary_directory.name) / "dataset.csv"
        )

    @staticmethod
    def valid_frame() -> pd.DataFrame:
        """Create a small valid normalized HANFIS dataset."""
        return pd.DataFrame(
            {
                column: [0.25, 0.50, 0.75]
                for column in REQUIRED_COLUMNS
            }
        )

    def test_valid_dataset_is_loaded(self) -> None:
        frame = self.valid_frame()
        frame.to_csv(self.csv_path, index=False)

        loaded = load_dataset(self.csv_path)

        self.assertEqual(len(loaded), 3)
        self.assertTrue(
            np.isfinite(
                loaded[REQUIRED_COLUMNS].to_numpy(dtype=np.float64)
            ).all()
        )

    def test_missing_required_column_is_rejected(self) -> None:
        frame = self.valid_frame().drop(columns=["cvss"])
        frame.to_csv(self.csv_path, index=False)

        with self.assertRaisesRegex(
            ValueError,
            "missing required columns",
        ):
            load_dataset(self.csv_path)

    def test_empty_dataset_is_rejected(self) -> None:
        frame = self.valid_frame().iloc[0:0]
        frame.to_csv(self.csv_path, index=False)

        with self.assertRaisesRegex(
            ValueError,
            "must not be empty",
        ):
            load_dataset(self.csv_path)

    def test_nonnumeric_value_is_rejected(self) -> None:
        frame = self.valid_frame()
        frame["cvss"] = ["invalid", 0.50, 0.75]
        frame.to_csv(self.csv_path, index=False)

        with self.assertRaisesRegex(
            ValueError,
            "must be numeric",
        ):
            load_dataset(self.csv_path)

    def test_nonfinite_values_are_rejected(self) -> None:
        for invalid_value in (np.nan, np.inf, -np.inf):
            with self.subTest(invalid_value=invalid_value):
                frame = self.valid_frame()
                frame.loc[0, "threat_intelligence"] = invalid_value
                frame.to_csv(self.csv_path, index=False)

                with self.assertRaisesRegex(
                    ValueError,
                    "finite numeric values",
                ):
                    load_dataset(self.csv_path)

    def test_negative_value_is_rejected(self) -> None:
        frame = self.valid_frame()
        frame.loc[0, "mfa_risk"] = -0.01
        frame.to_csv(self.csv_path, index=False)

        with self.assertRaisesRegex(
            ValueError,
            r"within \[0, 1\]",
        ):
            load_dataset(self.csv_path)

    def test_value_above_one_is_rejected(self) -> None:
        frame = self.valid_frame()
        frame.loc[0, "dynamic_risk_target"] = 1.01
        frame.to_csv(self.csv_path, index=False)

        with self.assertRaisesRegex(
            ValueError,
            r"within \[0, 1\]",
        ):
            load_dataset(self.csv_path)


if __name__ == "__main__":
    unittest.main()
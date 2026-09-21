#!/usr/bin/env python3
"""Automated tests for expert-label integration."""

import csv
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "merge_expert_labels.py"

spec = importlib.util.spec_from_file_location(
    "merge_expert_labels",
    SCRIPT_PATH,
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


SOURCE_ROW = [
    "TEST-EVT-0001",
    "2026-07-31T04:00:00Z",
    "TEST-ASSET-01",
    "0.850000",
    "0.700000",
    "0.500000",
    "1.000000",
    "0.600000",
    "0.750000",
    "0.800000",
]

LABEL_ROW = [
    "TEST-EVT-0001",
    "CONTROL-LABELER-01",
    "2026-07-31T04:30:00Z",
    "0.820000",
    "0.740000",
    "0.860000",
    "1.000000",
]


class TestExpertLabelIntegration(unittest.TestCase):

    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_directory.name)

        self.original_paths = (
            module.SOURCE_CSV,
            module.LABEL_CSV,
            module.LABEL_SCHEMA,
            module.OUTPUT_CSV,
        )

        module.SOURCE_CSV = self.temp_path / "source.csv"
        module.LABEL_CSV = self.temp_path / "labels.csv"
        module.LABEL_SCHEMA = self.temp_path / "label_schema.json"
        module.OUTPUT_CSV = self.temp_path / "real_data.csv"

        schema = {
            "fields": {
                field: {}
                for field in module.LABEL_FIELDS
            }
        }

        module.LABEL_SCHEMA.write_text(
            json.dumps(schema),
            encoding="utf-8",
        )

    def tearDown(self):
        (
            module.SOURCE_CSV,
            module.LABEL_CSV,
            module.LABEL_SCHEMA,
            module.OUTPUT_CSV,
        ) = self.original_paths

        self.temp_directory.cleanup()

    def write_csv(self, path, header, rows):
        with path.open("w", encoding="utf-8", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(header)
            writer.writerows(rows)

    def write_valid_source(self, rows=None):
        self.write_csv(
            module.SOURCE_CSV,
            module.SOURCE_FIELDS,
            [SOURCE_ROW] if rows is None else rows,
        )

    def write_valid_labels(self, rows=None):
        self.write_csv(
            module.LABEL_CSV,
            module.LABEL_FIELDS,
            [LABEL_ROW] if rows is None else rows,
        )

    def test_valid_one_to_one_merge(self):
        self.write_valid_source()
        self.write_valid_labels()

        module.merge_real_data()

        with module.OUTPUT_CSV.open(
            "r",
            encoding="utf-8",
            newline="",
        ) as file:
            result = next(csv.DictReader(file))

        self.assertEqual(result["event_id"], "TEST-EVT-0001")
        self.assertEqual(result["cvss"], "0.850000")
        self.assertEqual(
            result["dynamic_risk_target"],
            "0.860000",
        )

    def test_missing_expert_label_is_rejected(self):
        self.write_valid_source()
        self.write_valid_labels([])

        with self.assertRaisesRegex(
            ValueError,
            "without expert labels",
        ):
            module.merge_real_data()

    def test_orphan_expert_label_is_rejected(self):
        self.write_valid_source([])

        orphan = LABEL_ROW.copy()
        orphan[0] = "ORPHAN-EVT-0001"
        self.write_valid_labels([orphan])

        with self.assertRaisesRegex(
            ValueError,
            "without source events",
        ):
            module.merge_real_data()

    def test_duplicate_expert_label_is_rejected(self):
        self.write_valid_source()
        self.write_valid_labels([LABEL_ROW, LABEL_ROW])

        with self.assertRaisesRegex(
            ValueError,
            "duplicate event_id",
        ):
            module.merge_real_data()

    def test_duplicate_source_event_is_rejected(self):
        self.write_valid_source([SOURCE_ROW, SOURCE_ROW])
        self.write_valid_labels()

        with self.assertRaisesRegex(
            ValueError,
            "duplicate event_id",
        ):
            module.merge_real_data()

    def test_target_above_one_is_rejected(self):
        invalid = LABEL_ROW.copy()
        invalid[5] = "1.20"

        self.write_valid_source()
        self.write_valid_labels([invalid])

        with self.assertRaisesRegex(
            ValueError,
            "outside",
        ):
            module.merge_real_data()

    def test_non_finite_target_is_rejected(self):
        invalid = LABEL_ROW.copy()
        invalid[3] = "nan"

        self.write_valid_source()
        self.write_valid_labels([invalid])

        with self.assertRaisesRegex(
            ValueError,
            "must be finite",
        ):
            module.merge_real_data()

    def test_incorrect_label_header_is_rejected(self):
        self.write_valid_source()
        self.write_csv(
            module.LABEL_CSV,
            ["event_id", "dynamic_risk_score"],
            [["TEST-EVT-0001", "0.86"]],
        )

        with self.assertRaisesRegex(
            ValueError,
            "header does not match",
        ):
            module.merge_real_data()

    def test_invalid_normalized_input_is_rejected(self):
        invalid = SOURCE_ROW.copy()
        invalid[3] = "1.50"

        self.write_valid_source([invalid])
        self.write_valid_labels()

        with self.assertRaisesRegex(
            ValueError,
            "outside",
        ):
            module.merge_real_data()


if __name__ == "__main__":
    unittest.main(verbosity=2)
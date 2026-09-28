import json
import sys
import unittest
from pathlib import Path

import jsonschema

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((PROJECT_ROOT / "configs" / "anfis_source_schema_v2.json").read_text())


class TestSourceSchemaV2(unittest.TestCase):
    def test_valid_example_passes(self):
        for row in json.loads((PROJECT_ROOT / "configs" / "examples" / "anfis_source_v2_valid.json").read_text()):
            jsonschema.validate(row, SCHEMA)

    def test_invalid_example_is_rejected(self):
        for row in json.loads((PROJECT_ROOT / "configs" / "examples" / "anfis_source_v2_invalid.json").read_text()):
            with self.assertRaises(jsonschema.ValidationError):
                jsonschema.validate(row, SCHEMA)

    def test_required_columns_cover_the_seven_inputs_and_the_grouping_keys(self):
        required = set(SCHEMA["required"])
        for column in ("image_id", "week_start_utc", "cvss", "exploitability", "patch_risk",
                       "mfa_risk", "kubernetes_exposure", "asset_criticality",
                       "threat_intelligence", "reachability_level", "version_range_status"):
            self.assertIn(column, required)

    def test_unknown_is_null_not_zero(self):
        row = json.loads((PROJECT_ROOT / "configs" / "examples" / "anfis_source_v2_valid.json").read_text())[0]
        row["cvss"] = None
        jsonschema.validate(row, SCHEMA)          # null allowed
        row["cvss"] = 11.0
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(row, SCHEMA)

    def test_reachability_levels_match_amendment_a01(self):
        self.assertEqual(
            [v for v in SCHEMA["properties"]["reachability_level"]["enum"] if v is not None],
            [0, 0.1, 0.25, 0.6, 1],
        )


if __name__ == "__main__":
    unittest.main()

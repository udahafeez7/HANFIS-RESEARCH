import json
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = PROJECT_ROOT / "configs" / "anfis_schema.json"
SCHEMA_PATH = (
    PROJECT_ROOT
    / "schemas"
    / "hanfis-telemetry-v1.schema.json"
)

EXPECTED_LAYERS = {
    "vulnerability_layer": {
        "cvss",
        "exploitability",
        "patch_risk",
    },
    "environmental_layer": {
        "asset_criticality",
        "mfa_risk",
        "kubernetes_exposure",
    },
    "integration_layer": {
        "threat_intelligence",
    },
}


def find_layer_properties(node, layer_name):
    """Temukan properti input suatu layer secara rekursif."""
    if isinstance(node, dict):
        properties = node.get("properties")

        if (
            node.get("title") == layer_name
            and isinstance(properties, dict)
        ):
            return set(properties)

        for key, value in node.items():
            if key == layer_name and isinstance(value, dict):
                nested = value.get("properties")
                if isinstance(nested, dict):
                    return set(nested)

            result = find_layer_properties(value, layer_name)
            if result is not None:
                return result

    elif isinstance(node, list):
        for value in node:
            result = find_layer_properties(value, layer_name)
            if result is not None:
                return result

    return None


class TestHanfisFeatureContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads(
            CONFIG_PATH.read_text(encoding="utf-8")
        )
        cls.schema = json.loads(
            SCHEMA_PATH.read_text(encoding="utf-8")
        )

    def test_config_contains_exactly_seven_unique_inputs(self):
        inputs = self.config.get("inputs", [])

        self.assertEqual(len(inputs), 7)
        self.assertEqual(len(set(inputs)), 7)

    def test_each_schema_layer_has_expected_inputs(self):
        for layer_name, expected_inputs in EXPECTED_LAYERS.items():
            with self.subTest(layer=layer_name):
                detected = find_layer_properties(
                    self.schema,
                    layer_name,
                )
                self.assertIsNotNone(detected)
                self.assertEqual(detected, expected_inputs)

    def test_config_and_schema_use_identical_inputs(self):
        config_inputs = set(self.config.get("inputs", []))
        schema_inputs = set().union(*EXPECTED_LAYERS.values())

        self.assertEqual(config_inputs, schema_inputs)

    def test_deprecated_cvss_score_is_not_used(self):
        config_inputs = set(self.config.get("inputs", []))

        self.assertNotIn("cvss_score", config_inputs)
        self.assertIn("cvss", config_inputs)

    def test_threat_intelligence_uses_normalized_range(self):
        config_range = self.config["inputs"]["threat_intelligence"]
        schema_range = self.schema["$defs"]["normalizedRiskValue"]

        self.assertEqual(config_range["minimum"], 0.0)
        self.assertEqual(config_range["maximum"], 1.0)
        self.assertEqual(
            config_range["minimum"],
            schema_range["minimum"],
        )
        self.assertEqual(
            config_range["maximum"],
            schema_range["maximum"],
        )
if __name__ == "__main__":
    unittest.main()
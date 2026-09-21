import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PYTHON_HANFIS_DIR = PROJECT_ROOT / "python_hanfis"

if str(PYTHON_HANFIS_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_HANFIS_DIR))

from hanfis_7input_experiment import synthetic_dataset


TARGET_COLUMNS = (
    "vulnerability_target",
    "environment_target",
    "dynamic_risk_target",
)


class TestHanfisTargetContract(unittest.TestCase):
    def test_synthetic_targets_use_normalized_range(self):
        frame = synthetic_dataset(
            n=512,
            seed=20260729,
        )

        violations = {}

        for target in TARGET_COLUMNS:
            series = frame[target]

            below_minimum = int((series < 0.0).sum())
            above_maximum = int((series > 1.0).sum())

            if below_minimum or above_maximum:
                violations[target] = {
                    "minimum_observed": float(series.min()),
                    "maximum_observed": float(series.max()),
                    "values_below_zero": below_minimum,
                    "values_above_one": above_maximum,
                }

        self.assertEqual(
            {},
            violations,
            (
                "Synthetic HANFIS targets must use the canonical "
                f"0–1 range. Violations: {violations}"
            ),
        )


if __name__ == "__main__":
    unittest.main()
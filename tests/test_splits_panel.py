"""Patch 0030 (A-16): GroupTimeSplit on a complete asset-week panel — every image every week."""
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "python_hanfis"))
from splits import GroupTimeSplit, embargo_timedelta, summarise_folds  # noqa: E402


def panel(n_images=27, n_weeks=57):
    weeks = pd.date_range("2025-08-25", periods=n_weeks, freq="7D", tz="UTC")
    return pd.DataFrame([{"image_id": f"img{i:02d}", "week_start_utc": w, "y": 0.1 * i + 0.01 * k}
                         for i in range(n_images) for k, w in enumerate(weeks)])


class TestPanelSplit(unittest.TestCase):
    def test_complete_panel_yields_disjoint_embargoed_folds_covering_every_image_once(self):
        frame = panel(); sp = GroupTimeSplit(n_splits=5, embargo_days=30, min_train_weeks=4)
        folds = sp.split(frame)
        self.assertEqual(len(folds), 5)
        sp.assert_no_leakage(frame, folds)
        tested = []
        for f in folds:
            train, test = frame.iloc[f.train_index], frame.iloc[f.test_index]
            self.assertEqual(set(train.image_id) & set(test.image_id), set())
            self.assertGreaterEqual(test.week_start_utc.min() - train.week_start_utc.max(), embargo_timedelta(30))
            self.assertLessEqual(train.week_start_utc.max(), f.cutoff)
            tested += list(test.image_id.unique())
        self.assertEqual(sorted(tested), sorted(frame.image_id.unique()))     # each image tested exactly once
        self.assertEqual(len(tested), len(set(tested)))

    def test_assignment_is_deterministic_and_balanced(self):
        frame = panel(); sp = GroupTimeSplit(n_splits=5)
        a1, a2 = sp.group_assignment(frame), sp.group_assignment(frame)
        self.assertEqual(a1, a2)
        counts = np.bincount(list(a1.values()), minlength=5)
        self.assertTrue(counts.max() - counts.min() <= 1)
        self.assertNotEqual(a1, GroupTimeSplit(n_splits=5, group_seed=1).group_assignment(frame))

    def test_shared_image_id_conditions_stay_together(self):
        frame = panel(n_images=6)
        frame["asset"] = frame.image_id
        frame.loc[frame.image_id == "img00", "image_id"] = "shared"
        frame.loc[frame.image_id == "img01", "image_id"] = "shared"   # ON/OFF conditions of one image
        sp = GroupTimeSplit(n_splits=3); folds = sp.split(frame); sp.assert_no_leakage(frame, folds)
        table = summarise_folds(frame, folds)
        self.assertTrue((table.test_rows > 0).all())


if __name__ == "__main__":
    unittest.main()

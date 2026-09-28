import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "python_hanfis"))

from splits import GroupTimeSplit, LeakageError, embargo_timedelta, summarise_folds  # noqa: E402


def asset_weeks(n_images: int = 12, n_weeks: int = 16, seed: int = 0) -> pd.DataFrame:
    """One row per image per week, with a target that grows over time."""
    rng = np.random.default_rng(seed)
    weeks = pd.date_range("2026-01-05", periods=n_weeks, freq="7D", tz="UTC")
    rows = []
    for i in range(n_images):
        for w, week in enumerate(weeks):
            rows.append({
                "image_id": f"img{i:02d}",
                "week_start_utc": week,
                "y": float(rng.random() * 0.2 + 0.02 * w),
            })
    return pd.DataFrame(rows)


class TestGroupTimeSplit(unittest.TestCase):
    def setUp(self):
        self.frame = asset_weeks()
        self.splitter = GroupTimeSplit(n_splits=3, embargo_days=30, min_train_weeks=4)

    def test_split_requires_the_two_key_columns(self):
        with self.assertRaises(KeyError):
            self.splitter.split(self.frame.drop(columns=["image_id"]))
        with self.assertRaises(KeyError):
            self.splitter.split(self.frame.rename(columns={"week_start_utc": "t"}))

    def test_group_disjointness_and_embargo_hold_for_every_fold(self):
        # images are split so that some appear only late, otherwise every test block would be
        # emptied by the group filter
        late = self.frame["image_id"].isin([f"img{i:02d}" for i in range(8, 12)])
        early_weeks = self.frame["week_start_utc"] < pd.Timestamp("2026-03-01", tz="UTC")
        frame = self.frame[~(late & early_weeks)].reset_index(drop=True)
        folds = self.splitter.split(frame)
        self.assertGreaterEqual(len(folds), 1)
        self.splitter.assert_no_leakage(frame, folds)
        for fold in folds:
            train, test = frame.iloc[fold.train_index], frame.iloc[fold.test_index]
            self.assertEqual(set(train["image_id"]) & set(test["image_id"]), set())
            gap = test["week_start_utc"].min() - train["week_start_utc"].max()
            self.assertGreaterEqual(gap, embargo_timedelta(30))

    def test_assert_no_leakage_detects_a_shared_image(self):
        frame = self.frame
        folds = None
        late = frame["image_id"].isin([f"img{i:02d}" for i in range(8, 12)])
        early = frame["week_start_utc"] < pd.Timestamp("2026-03-01", tz="UTC")
        clean = frame[~(late & early)].reset_index(drop=True)
        folds = self.splitter.split(clean)
        broken = folds[0]
        # inject a training row of a test image into the training index
        test_image = clean.iloc[broken.test_index]["image_id"].iloc[0]
        extra = np.flatnonzero((clean["image_id"] == test_image).to_numpy())[:1]
        tampered = [type(broken)(broken.index, np.concatenate([broken.train_index, extra]),
                                 broken.test_index, broken.cutoff, broken.test_start, broken.test_end)]
        with self.assertRaises(LeakageError):
            self.splitter.assert_no_leakage(clean, tampered)

    def test_assert_no_leakage_detects_a_violated_embargo(self):
        weeks = pd.date_range("2026-01-05", periods=10, freq="7D", tz="UTC")
        frame = pd.DataFrame([
            {"image_id": "a", "week_start_utc": w, "y": 0.1} for w in weeks[:6]
        ] + [
            {"image_id": "b", "week_start_utc": w, "y": 0.2} for w in weeks[6:]
        ])
        from splits import Fold
        fold = Fold(0, np.arange(0, 6), np.arange(6, len(frame)), weeks[5], weeks[6], weeks[-1])
        # gap is 7 days, embargo 30 -> must raise
        with self.assertRaises(LeakageError):
            GroupTimeSplit(embargo_days=30).assert_no_leakage(frame, [fold])
        # with a 3-day embargo the same fold is acceptable
        GroupTimeSplit(embargo_days=3).assert_no_leakage(frame, [fold])

    def test_no_deprecation_warnings_from_split_or_leakage_check(self):
        """Patch 0020: the embargo must not go through a generic-unit NumPy timedelta."""
        import warnings

        late = self.frame["image_id"].isin([f"img{i:02d}" for i in range(8, 12)])
        early = self.frame["week_start_utc"] < pd.Timestamp("2026-03-01", tz="UTC")
        frame = self.frame[~(late & early)].reset_index(drop=True)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            folds = self.splitter.split(frame)
            self.splitter.assert_no_leakage(frame, folds)
            summarise_folds(frame, folds)
        offenders = [str(w.message) for w in caught if issubclass(w.category, (DeprecationWarning, FutureWarning))]
        self.assertEqual(offenders, [], msg=f"unexpected warnings: {offenders}")

    def test_embargo_timedelta_is_explicit_and_equal_to_days(self):
        self.assertEqual(embargo_timedelta(30), pd.Timedelta("30D"))
        self.assertEqual(embargo_timedelta(0), pd.Timedelta("0D"))

    def test_too_few_weeks_is_refused(self):
        short = self.frame[self.frame["week_start_utc"] < pd.Timestamp("2026-02-01", tz="UTC")]
        with self.assertRaises(ValueError):
            self.splitter.split(short)

    def test_summarise_folds_reports_sizes_and_target_share(self):
        late = self.frame["image_id"].isin([f"img{i:02d}" for i in range(8, 12)])
        early = self.frame["week_start_utc"] < pd.Timestamp("2026-03-01", tz="UTC")
        frame = self.frame[~(late & early)].reset_index(drop=True)
        folds = self.splitter.split(frame)
        table = summarise_folds(frame, folds)
        self.assertEqual(len(table), len(folds))
        for column in ("train_rows", "test_rows", "train_images", "test_images", "test_target_nonzero_share"):
            self.assertIn(column, table.columns)
        self.assertTrue((table["train_rows"] > 0).all() and (table["test_rows"] > 0).all())


if __name__ == "__main__":
    unittest.main()

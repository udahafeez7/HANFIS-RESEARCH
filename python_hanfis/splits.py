"""Grouped and time-aware data splitting for HANFIS (patch 0019).

The observation unit is an asset-week: one row per image (``image_id``) per week
(``week_start_utc``). Two leakage paths have to be closed at the same time:

1. **Group leakage.** Rows from the same image are highly correlated (same packages, same
   configuration). An image must never appear in both the training and the evaluation part.
2. **Temporal leakage.** The target y(a,t) is built from EPSS/KEV evidence observed in the
   window (t, t + delta]. A training row whose outcome window overlaps an evaluation row's
   feature time leaks future information. An embargo of ``embargo_days`` (default 30, the
   width of the outcome window) is therefore applied around the split point.

``GroupTimeSplit`` yields folds in expanding-window form: fold k trains on everything up to a
cut-off, waits out the embargo, and evaluates on the following block of weeks, with the
image groups disjoint between the two sides.

Group assignment (patch 0030, amendment A-16). Images are assigned deterministically to
``n_splits`` held-out groups (seeded permutation of the sorted ``image_id`` values, round
robin). Fold k trains on the images *not* in group k up to the cut-off and evaluates the
images *of* group k inside test block k. On a complete panel (every image observed every
week) the earlier rule -- drop test rows whose image already has training history -- emptied
every test block; this rule keeps both leakage paths closed and tests every image exactly once.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

GROUP_COLUMN = "image_id"
TIME_COLUMN = "week_start_utc"


def embargo_timedelta(days: int) -> pd.Timedelta:
    """Build the embargo as an explicitly-united Timedelta.

    ``pd.Timedelta(days=n)`` goes through a NumPy timedelta64 whose unit is inferred; on
    numpy >= 2 with recent pandas this raises a DeprecationWarning about the 'generic' unit.
    The string form carries the unit explicitly and behaves identically on every version
    (patch 0020).
    """
    return pd.Timedelta(int(days), unit="D")


class LeakageError(AssertionError):
    """Raised when a split violates the grouping or the temporal embargo."""


@dataclass(frozen=True)
class Fold:
    index: int
    train_index: np.ndarray
    test_index: np.ndarray
    cutoff: pd.Timestamp
    test_start: pd.Timestamp
    test_end: pd.Timestamp

    def __len__(self) -> int:  # convenience for len(fold)
        return len(self.train_index) + len(self.test_index)


class GroupTimeSplit:
    """Expanding-window splitter with disjoint groups and a temporal embargo."""

    def __init__(
        self,
        n_splits: int = 5,
        embargo_days: int = 30,
        group_column: str = GROUP_COLUMN,
        time_column: str = TIME_COLUMN,
        min_train_weeks: int = 4,
        group_seed: int = 20260928,
    ) -> None:
        if n_splits < 1:
            raise ValueError("n_splits must be >= 1")
        self.n_splits = int(n_splits)
        self.embargo_days = int(embargo_days)
        self.group_column = group_column
        self.time_column = time_column
        self.min_train_weeks = int(min_train_weeks)
        self.group_seed = int(group_seed)

    def group_assignment(self, frame: pd.DataFrame) -> dict[str, int]:
        """Deterministic image -> held-out fold index (0..n_splits-1); stable across runs and seeds of the model."""
        images = sorted(frame[self.group_column].astype(str).unique())
        order = np.random.default_rng(self.group_seed).permutation(len(images))
        return {images[j]: int(rank % self.n_splits) for rank, j in enumerate(order)}

    def _prepare(self, frame: pd.DataFrame) -> pd.DataFrame:
        for column in (self.group_column, self.time_column):
            if column not in frame.columns:
                raise KeyError(f"missing required column: {column}")
        prepared = frame.copy()
        prepared[self.time_column] = pd.to_datetime(prepared[self.time_column], utc=True, errors="raise")
        return prepared

    def split(self, frame: pd.DataFrame) -> list[Fold]:
        prepared = self._prepare(frame)
        weeks = np.array(sorted(prepared[self.time_column].unique()))
        if len(weeks) < self.min_train_weeks + 2:
            raise ValueError(
                f"need at least {self.min_train_weeks + 2} distinct weeks, found {len(weeks)}"
            )
        embargo = embargo_timedelta(self.embargo_days)
        # The first test week must leave >= min_train_weeks training weeks *before* the embargo,
        # otherwise the first block has an empty training side and its held-out group is never
        # evaluated (patch 0030).
        earliest_cutoff = pd.Timestamp(weeks[self.min_train_weeks - 1])
        usable = np.array([w for w in weeks if pd.Timestamp(w) - embargo >= earliest_cutoff])
        if len(usable) < self.n_splits:
            raise ValueError(
                f"only {len(usable)} weeks remain after {self.min_train_weeks} training weeks and a "
                f"{self.embargo_days}-day embargo; need at least n_splits={self.n_splits}"
            )
        blocks = np.array_split(usable, self.n_splits)
        held_out = prepared[self.group_column].astype(str).map(self.group_assignment(prepared))
        folds: list[Fold] = []
        for k, block in enumerate(blocks):
            if len(block) == 0:
                continue
            test_start, test_end = pd.Timestamp(block[0]), pd.Timestamp(block[-1])
            cutoff = test_start - embargo
            in_group = (held_out == k).to_numpy()
            # Group disjointness: fold k's images are held out of training entirely and are the
            # only images evaluated in block k (A-16).
            train_mask = (prepared[self.time_column] <= cutoff) & ~in_group
            test_mask = (prepared[self.time_column] >= test_start) & (prepared[self.time_column] <= test_end) & in_group
            if not train_mask.any() or not test_mask.any():
                continue
            folds.append(
                Fold(
                    index=k,
                    train_index=np.flatnonzero(train_mask.to_numpy()),
                    test_index=np.flatnonzero(test_mask.to_numpy()),
                    cutoff=cutoff,
                    test_start=test_start,
                    test_end=test_end,
                )
            )
        if not folds:
            raise ValueError(
                "no usable fold: a held-out group has no rows inside its test block, or the embargo "
                "consumes the available weeks"
            )
        return folds

    def assert_no_leakage(self, frame: pd.DataFrame, folds: list[Fold]) -> None:
        """Raise LeakageError if any fold shares a group or violates the embargo."""
        prepared = self._prepare(frame)
        embargo = embargo_timedelta(self.embargo_days)
        for fold in folds:
            train = prepared.iloc[fold.train_index]
            test = prepared.iloc[fold.test_index]
            shared = set(train[self.group_column]) & set(test[self.group_column])
            if shared:
                raise LeakageError(f"fold {fold.index}: images on both sides: {sorted(shared)[:5]}")
            gap = test[self.time_column].min() - train[self.time_column].max()
            if gap < embargo:
                raise LeakageError(
                    f"fold {fold.index}: gap {gap} is smaller than the embargo {embargo}"
                )


def summarise_folds(frame: pd.DataFrame, folds: list[Fold], target_column: str = "y") -> pd.DataFrame:
    """One row per fold: sizes, group counts, date ranges and target variance."""
    rows = []
    for fold in folds:
        train, test = frame.iloc[fold.train_index], frame.iloc[fold.test_index]
        row = {
            "fold": fold.index,
            "train_rows": len(train),
            "test_rows": len(test),
            "train_images": train[GROUP_COLUMN].nunique(),
            "test_images": test[GROUP_COLUMN].nunique(),
            "cutoff": fold.cutoff,
            "test_start": fold.test_start,
            "test_end": fold.test_end,
        }
        if target_column in frame.columns:
            row["train_target_mean"] = float(train[target_column].mean())
            row["test_target_mean"] = float(test[target_column].mean())
            row["test_target_nonzero_share"] = float((test[target_column] > 0).mean())
        rows.append(row)
    return pd.DataFrame(rows)

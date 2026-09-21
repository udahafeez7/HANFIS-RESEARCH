"""Seven-input HANFIS experiment corresponding to the MATLAB prototype.

The internal data contract is normalized to [0, 1]. Values are converted to
the 0-100 reporting scale only when evaluation outputs are produced.
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import KFold

from hanfis_models import SugenoANFIS, fit_anfis, predict


SEED = 20260721
FEATURES = [
    "cvss",
    "exploitability",
    "patch_risk",
    "mfa_risk",
    "kubernetes_exposure",
    "asset_criticality",
    "threat_intelligence",
]
TARGET_COLUMNS = [
    "vulnerability_target",
    "environment_target",
    "dynamic_risk_target",
]
REQUIRED_COLUMNS = FEATURES + TARGET_COLUMNS

IndexSplits = tuple[np.ndarray, np.ndarray, np.ndarray]
TrainingHistory = dict[str, list[float] | float | int]


def seed_everything(seed: int) -> None:
    """Seed Python, NumPy, and PyTorch for reproducible experiments."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def synthetic_dataset(n: int, seed: int) -> pd.DataFrame:
    """Create normalized proxy data for pipeline validation only."""
    if n < 1:
        raise ValueError("The number of synthetic samples must be positive.")

    rng = np.random.default_rng(seed)
    frame = pd.DataFrame(
        rng.random((n, len(FEATURES))),
        columns=FEATURES,
    )

    frame["vulnerability_target"] = (
        0.35 * frame.cvss
        + 0.25 * frame.exploitability
        + 0.20 * frame.patch_risk
        + 0.10 * frame.cvss * frame.exploitability
        + 0.10 * frame.exploitability * frame.patch_risk
    )

    frame["environment_target"] = (
        0.25 * frame.mfa_risk
        + 0.30 * frame.kubernetes_exposure
        + 0.30 * frame.asset_criticality
        + 0.15 * frame.kubernetes_exposure * frame.asset_criticality
    )

    frame["dynamic_risk_target"] = np.clip(
        0.32 * frame.vulnerability_target
        + 0.28 * frame.environment_target
        + 0.32 * frame.threat_intelligence
        + 0.18
        * frame.threat_intelligence
        * frame.vulnerability_target,
        0.0,
        1.0,
    )

    return frame


def load_dataset(path: Path) -> pd.DataFrame:
    """Load and validate a normalized HANFIS dataset from CSV."""
    try:
        frame = pd.read_csv(path)
    except pd.errors.EmptyDataError as error:
        raise ValueError("Dataset must not be empty.") from error

    missing = sorted(set(REQUIRED_COLUMNS).difference(frame.columns))
    if missing:
        raise ValueError(
            f"Dataset is missing required columns: {missing}"
        )

    if frame.empty:
        raise ValueError("Dataset must not be empty.")

    try:
        numeric_data = frame[REQUIRED_COLUMNS].apply(
            pd.to_numeric,
            errors="raise",
        )
    except (TypeError, ValueError) as error:
        raise ValueError(
            "All required feature and target columns must be numeric."
        ) from error

    if not np.isfinite(
        numeric_data.to_numpy(dtype=np.float64)
    ).all():
        raise ValueError(
            "Required columns must contain only finite numeric values."
        )

    outside_range = (
        (numeric_data < 0.0)
        | (numeric_data > 1.0)
    )

    if outside_range.any().any():
        invalid_columns = numeric_data.columns[
            outside_range.any(axis=0)
        ].tolist()

        raise ValueError(
            "Required columns must contain values within [0, 1]. "
            f"Invalid columns: {invalid_columns}"
        )

    validated = frame.copy()
    validated[REQUIRED_COLUMNS] = numeric_data
    return validated


def split_indices(n: int, seed: int) -> IndexSplits:
    """Create deterministic 70/15/15 train-validation-test indices."""
    order = np.random.default_rng(seed).permutation(n)
    n_train = int(0.70 * n)
    n_validation = int(0.15 * n)
    n_test = n - n_train - n_validation

    if min(n_train, n_validation, n_test) < 1:
        raise ValueError(
            "Dataset is too small for a non-empty 70/15/15 split."
        )

    return (
        order[:n_train],
        order[n_train:n_train + n_validation],
        order[n_train + n_validation:],
    )


def metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
) -> dict[str, float]:
    """Calculate regression metrics on matching target and prediction scales."""
    return {
        "rmse": float(
            mean_squared_error(y_true, y_pred) ** 0.5
        ),
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "r_squared": float(r2_score(y_true, y_pred)),
    }


def train_one(
    x: np.ndarray,
    y: np.ndarray,
    splits: IndexSplits,
    n_mfs: int,
    epochs: int,
) -> tuple[SugenoANFIS, TrainingHistory]:
    """Train one Sugeno ANFIS using the supplied training and validation rows."""
    train, validation, _ = splits

    if len(train) < 1 or len(validation) < 1:
        raise ValueError(
            "Training and validation indices must both be non-empty."
        )

    model = SugenoANFIS(x.shape[1], n_mfs)
    history = fit_anfis(
        model,
        x[train],
        y[train],
        x[validation],
        y[validation],
        epochs=epochs,
    )
    return model, history


def generate_oof_predictions(
    x: np.ndarray,
    y: np.ndarray,
    splits: IndexSplits,
    n_mfs: int,
    epochs: int,
    n_splits: int = 5,
) -> tuple[SugenoANFIS, np.ndarray, TrainingHistory]:
    """Generate leakage-resistant level-one inputs for hierarchical stacking.

    Training rows receive out-of-fold predictions. The outer validation and
    test rows are predicted by the final base model trained on the outer
    training split.
    """
    train, validation, test = splits

    if n_splits < 2:
        raise ValueError("OOF requires at least two folds.")

    if len(train) < n_splits:
        raise ValueError(
            "The training split must contain at least as many rows "
            "as the requested OOF folds."
        )

    predictions = np.full(
        len(y),
        np.nan,
        dtype=np.float32,
    )

    kfold = KFold(
        n_splits=n_splits,
        shuffle=True,
        random_state=SEED,
    )

    for fold_number, (
        fit_local,
        holdout_local,
    ) in enumerate(kfold.split(train), start=1):
        fit_indices = train[fit_local]
        holdout_indices = train[holdout_local]

        inner_validation_size = max(
            1,
            int(0.15 * len(fit_indices)),
        )
        inner_validation = fit_indices[
            -inner_validation_size:
        ]
        inner_train = fit_indices[
            :-inner_validation_size
        ]

        if len(inner_train) < 1:
            raise ValueError(
                "OOF fold is too small to create an inner training split."
            )

        fold_model, _ = train_one(
            x,
            y,
            (inner_train, inner_validation, test),
            n_mfs,
            epochs,
        )

        predictions[holdout_indices] = predict(
            fold_model,
            x[holdout_indices],
        )

        print(
            f"OOF fold {fold_number}/{n_splits} selesai"
        )

    if np.isnan(predictions[train]).any():
        raise RuntimeError(
            "OOF predictions are incomplete for the training split."
        )

    final_model, history = train_one(
        x,
        y,
        splits,
        n_mfs,
        epochs,
    )

    predictions[validation] = predict(
        final_model,
        x[validation],
    )
    predictions[test] = predict(
        final_model,
        x[test],
    )

    if not np.isfinite(predictions).all():
        raise RuntimeError(
            "Base-model predictions contain non-finite values."
        )

    return final_model, predictions, history


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data",
        type=Path,
        help=(
            "CSV containing seven normalized inputs "
            "and three normalized targets"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results_python"),
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=900,
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=300,
    )
    parser.add_argument(
        "--mfs",
        type=int,
        default=2,
    )
    parser.add_argument(
        "--oof-folds",
        type=int,
        default=5,
    )
    parser.add_argument(
        "--skip-flat",
        action="store_true",
        help="Skip the seven-input Flat ANFIS comparison.",
    )
    args = parser.parse_args()

    seed_everything(SEED)
    args.output.mkdir(
        parents=True,
        exist_ok=True,
    )

    frame = (
        load_dataset(args.data)
        if args.data
        else synthetic_dataset(args.samples, SEED)
    )

    splits = split_indices(
        len(frame),
        SEED,
    )
    train, validation, test = splits

    x_vulnerability = frame[
        ["cvss", "exploitability", "patch_risk"]
    ].to_numpy(dtype=np.float32)

    x_environment = frame[
        [
            "mfa_risk",
            "kubernetes_exposure",
            "asset_criticality",
        ]
    ].to_numpy(dtype=np.float32)

    x_flat = frame[FEATURES].to_numpy(
        dtype=np.float32
    )

    # Targets remain normalized internally. Do not divide by 100 here.
    y_vulnerability = frame[
        "vulnerability_target"
    ].to_numpy(dtype=np.float32)

    y_environment = frame[
        "environment_target"
    ].to_numpy(dtype=np.float32)

    y_risk = frame[
        "dynamic_risk_target"
    ].to_numpy(dtype=np.float32)

    (
        vulnerability,
        predicted_v,
        history_v,
    ) = generate_oof_predictions(
        x_vulnerability,
        y_vulnerability,
        splits,
        args.mfs,
        args.epochs,
        args.oof_folds,
    )

    (
        environment,
        predicted_e,
        history_e,
    ) = generate_oof_predictions(
        x_environment,
        y_environment,
        splits,
        args.mfs,
        args.epochs,
        args.oof_folds,
    )

    predicted_v = np.clip(
        predicted_v,
        0.0,
        1.0,
    )
    predicted_e = np.clip(
        predicted_e,
        0.0,
        1.0,
    )

    x_integration = np.column_stack(
        [
            predicted_v,
            predicted_e,
            frame["threat_intelligence"].to_numpy(
                dtype=np.float32
            ),
        ]
    ).astype(np.float32)

    integration, history_i = train_one(
        x_integration,
        y_risk,
        splits,
        args.mfs,
        args.epochs,
    )

    # Convert to 0-100 only for evaluation and reporting.
    hanfis_prediction = (
        np.clip(
            predict(
                integration,
                x_integration[test],
            ),
            0.0,
            1.0,
        )
        * 100.0
    )
    y_test = y_risk[test] * 100.0

    rows = [
        {
            "model": "HANFIS",
            **metrics(
                y_test,
                hanfis_prediction,
            ),
            "rule_count": (
                vulnerability.rule_count
                + environment.rule_count
                + integration.rule_count
            ),
            "parameter_count": sum(
                parameter.numel()
                for model in (
                    vulnerability,
                    environment,
                    integration,
                )
                for parameter in model.parameters()
            ),
        }
    ]

    predictions = pd.DataFrame(
        {
            "observation_index": test,
            "target_risk": y_test,
            "hanfis_prediction": hanfis_prediction,
        }
    )

    flat = None
    history_flat = None

    if not args.skip_flat:
        flat, history_flat = train_one(
            x_flat,
            y_risk,
            splits,
            args.mfs,
            args.epochs,
        )

        flat_prediction = (
            np.clip(
                predict(
                    flat,
                    x_flat[test],
                ),
                0.0,
                1.0,
            )
            * 100.0
        )

        predictions[
            "flat_anfis_prediction"
        ] = flat_prediction

        rows.append(
            {
                "model": "Flat ANFIS",
                **metrics(
                    y_test,
                    flat_prediction,
                ),
                "rule_count": flat.rule_count,
                "parameter_count": sum(
                    parameter.numel()
                    for parameter
                    in flat.parameters()
                ),
            }
        )

    pd.DataFrame(rows).to_csv(
        args.output / "hanfis_7input_metrics.csv",
        index=False,
    )

    predictions.to_csv(
        args.output
        / "hanfis_7input_test_predictions.csv",
        index=False,
    )

    if args.data is None:
        frame.to_csv(
            args.output
            / "hanfis_7input_synthetic_dataset.csv",
            index=False,
        )

    bundle = {
        "vulnerability": vulnerability.state_dict(),
        "environment": environment.state_dict(),
        "integration": integration.state_dict(),
        "flat": (
            flat.state_dict()
            if flat is not None
            else None
        ),
        "n_mfs": args.mfs,
        "oof_folds": args.oof_folds,
        "features": FEATURES,
        "target_scale": "[0, 1]",
        "reporting_scale": "[0, 100]",
        "seed": SEED,
    }

    torch.save(
        bundle,
        args.output / "hanfis_7input_models.pt",
    )

    histories = {
        "vulnerability": history_v,
        "environment": history_e,
        "integration": history_i,
        "flat": history_flat,
        "stacking": {
            "method": "out_of_fold",
            "n_splits": args.oof_folds,
        },
        "splits": {
            "train": train.tolist(),
            "validation": validation.tolist(),
            "test": test.tolist(),
        },
    }

    (
        args.output
        / "hanfis_7input_training.json"
    ).write_text(
        json.dumps(histories, indent=2),
        encoding="utf-8",
    )

    plt.figure(figsize=(6, 6))
    plt.scatter(
        y_test,
        hanfis_prediction,
        alpha=0.7,
        label="HANFIS",
    )

    if (
        "flat_anfis_prediction"
        in predictions.columns
    ):
        plt.scatter(
            y_test,
            predictions[
                "flat_anfis_prediction"
            ],
            alpha=0.45,
            label="Flat ANFIS",
        )

    plt.plot(
        [0, 100],
        [0, 100],
        "k--",
    )
    plt.xlabel("Target Dynamic Risk Score")
    plt.ylabel("Prediction")
    plt.xlim(0, 100)
    plt.ylim(0, 100)
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(
        args.output
        / "hanfis_7input_evaluation.png",
        dpi=200,
    )
    plt.close()

    print(
        pd.DataFrame(rows).to_string(
            index=False
        )
    )
    print(
        f"Results saved to "
        f"{args.output.resolve()}"
    )


if __name__ == "__main__":
    main()

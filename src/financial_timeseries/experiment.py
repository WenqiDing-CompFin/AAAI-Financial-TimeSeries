"""Chronological model selection and final held-out evaluation."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .data import FEATURE_COLUMNS
from .metrics import regression_metrics


@dataclass(frozen=True)
class Split:
    train: pd.DataFrame
    validation: pd.DataFrame
    test: pd.DataFrame


def chronological_split(
    panel: pd.DataFrame, train_fraction: float = 0.60, validation_fraction: float = 0.20
) -> Split:
    """Split by unique dates, ensuring no date appears in multiple partitions."""
    if not 0 < train_fraction < 1 or not 0 < validation_fraction < 1:
        raise ValueError("split fractions must be between 0 and 1")
    if train_fraction + validation_fraction >= 1:
        raise ValueError("train and validation fractions must leave a test period")
    dates = np.array(sorted(pd.to_datetime(panel["date"]).unique()))
    train_end = max(1, int(len(dates) * train_fraction))
    validation_end = max(train_end + 1, int(len(dates) * (train_fraction + validation_fraction)))
    if validation_end >= len(dates):
        raise ValueError("not enough dates for three chronological partitions")
    train_dates = set(dates[:train_end])
    validation_dates = set(dates[train_end:validation_end])
    test_dates = set(dates[validation_end:])
    date_values = pd.to_datetime(panel["date"])
    return Split(
        train=panel.loc[date_values.isin(train_dates)].copy(),
        validation=panel.loc[date_values.isin(validation_dates)].copy(),
        test=panel.loc[date_values.isin(test_dates)].copy(),
    )


def _fit_standardizer(values: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    mean = values.mean(axis=0)
    scale = values.std(axis=0, ddof=0)
    scale[scale < 1e-12] = 1.0
    return mean, scale


def _transform(values: np.ndarray, mean: np.ndarray, scale: np.ndarray) -> np.ndarray:
    return (values - mean) / scale


def _ridge_predict(
    train_x: np.ndarray, train_y: np.ndarray, eval_x: np.ndarray, alpha: float
) -> np.ndarray:
    if alpha <= 0:
        raise ValueError("alpha must be positive")
    design = np.column_stack([np.ones(len(train_x)), train_x])
    regularizer = np.eye(design.shape[1])
    regularizer[0, 0] = 0.0
    coefficients = np.linalg.solve(
        design.T @ design + alpha * regularizer,
        design.T @ train_y,
    )
    return np.column_stack([np.ones(len(eval_x)), eval_x]) @ coefficients


def run_experiment(
    panel: pd.DataFrame,
    alphas: tuple[float, ...] = (0.01, 0.1, 1.0, 10.0),
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Select Ridge alpha on validation data and report the untouched test set."""
    split = chronological_split(panel)
    train_x = split.train.loc[:, FEATURE_COLUMNS].to_numpy(float)
    val_x = split.validation.loc[:, FEATURE_COLUMNS].to_numpy(float)
    train_y = split.train["target_return_1m"].to_numpy(float)
    val_y = split.validation["target_return_1m"].to_numpy(float)
    mean, scale = _fit_standardizer(train_x)
    train_x = _transform(train_x, mean, scale)
    val_x = _transform(val_x, mean, scale)

    validation_scores = []
    for alpha in alphas:
        val_pred = _ridge_predict(train_x, train_y, val_x, alpha)
        validation_scores.append({"alpha": alpha, **regression_metrics(val_y, val_pred)})
    selected_alpha = min(validation_scores, key=lambda row: row["mse"])["alpha"]

    combined = pd.concat([split.train, split.validation], ignore_index=True)
    combined_x = combined.loc[:, FEATURE_COLUMNS].to_numpy(float)
    combined_y = combined["target_return_1m"].to_numpy(float)
    combined_mean, combined_scale = _fit_standardizer(combined_x)
    combined_x = _transform(combined_x, combined_mean, combined_scale)
    test_x = _transform(
        split.test.loc[:, FEATURE_COLUMNS].to_numpy(float), combined_mean, combined_scale
    )
    test_y = split.test["target_return_1m"].to_numpy(float)
    ridge_test_pred = _ridge_predict(combined_x, combined_y, test_x, selected_alpha)
    persistence_pred = split.test["return_1m"].to_numpy(float)

    metrics_rows = []
    for model, predicted in (("persistence", persistence_pred), ("ridge", ridge_test_pred)):
        metrics_rows.append(
            {
                "split": "test",
                "model": model,
                "selected_alpha": selected_alpha if model == "ridge" else np.nan,
                "n_observations": len(test_y),
                "start_date": str(split.test["date"].min().date()),
                "end_date": str(split.test["date"].max().date()),
                **regression_metrics(test_y, predicted),
            }
        )
    predictions = split.test[["date", "ticker", "target_return_1m"]].copy()
    predictions = predictions.rename(columns={"target_return_1m": "actual"})
    predictions["persistence"] = persistence_pred
    predictions["ridge"] = ridge_test_pred
    return pd.DataFrame(metrics_rows), predictions

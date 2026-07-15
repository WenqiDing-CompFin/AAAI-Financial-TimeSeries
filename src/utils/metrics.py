"""Evaluation metrics for classification and regression tasks."""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
)


def classification_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    average: str = "macro",
) -> dict[str, float]:
    """Accuracy and F1 for multi-class event prediction."""
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "f1": float(f1_score(y_true, y_pred, average=average, zero_division=0)),
    }


def regression_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    """MSE / MAE / RMSE for minute-level forecasting."""
    mse = float(mean_squared_error(y_true, y_pred))
    mae = float(mean_absolute_error(y_true, y_pred))
    return {
        "mse": mse,
        "mae": mae,
        "rmse": float(np.sqrt(mse)),
    }


def format_metrics(metrics: dict[str, Any]) -> str:
    return ", ".join(f"{k}={v:.4f}" if isinstance(v, float) else f"{k}={v}" for k, v in metrics.items())

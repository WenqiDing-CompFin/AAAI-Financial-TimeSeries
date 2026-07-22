"""Small, dependency-light regression and directional metrics."""

from __future__ import annotations

import numpy as np


def regression_metrics(actual: np.ndarray, predicted: np.ndarray) -> dict[str, float]:
    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)
    if actual.shape != predicted.shape or actual.size == 0:
        raise ValueError("actual and predicted must be non-empty arrays of equal shape")
    errors = predicted - actual
    return {
        "mse": float(np.mean(errors**2)),
        "mae": float(np.mean(np.abs(errors))),
        "directional_accuracy": float(np.mean(np.sign(actual) == np.sign(predicted))),
    }

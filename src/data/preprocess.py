"""Preprocessing utilities for financial windows and labels."""

from __future__ import annotations

from typing import Tuple

import numpy as np


def make_windows(series: np.ndarray, window_size: int, stride: int = 1) -> np.ndarray:
    """
    Convert (T, C) series into overlapping windows of shape (N, window_size, C).
    """
    if series.ndim != 2:
        raise ValueError(f"Expected (T, C) array, got shape {series.shape}")
    t, _ = series.shape
    if t < window_size:
        raise ValueError(f"Series length {t} < window_size {window_size}")
    starts = np.arange(0, t - window_size + 1, stride)
    return np.stack([series[s : s + window_size] for s in starts], axis=0)


def build_event_labels(
    close: np.ndarray,
    indices: np.ndarray,
    window_size: int,
    threshold: float = 0.01,
) -> np.ndarray:
    """
    Original TimeCAP finance labeling:
      0 = decrease (>1% drop next day)
      1 = neutral
      2 = increase (>1% rise next day)
    `indices` are start positions of each window in the raw close series.
    """
    labels = []
    for start in indices:
        end = start + window_size - 1
        if end + 1 >= len(close):
            labels.append(1)
            continue
        ret = (close[end + 1] - close[end]) / max(abs(close[end]), 1e-8)
        if ret <= -threshold:
            labels.append(0)
        elif ret >= threshold:
            labels.append(2)
        else:
            labels.append(1)
    return np.asarray(labels, dtype=np.int64)


def train_val_test_split(
    n: int,
    train_ratio: float = 0.6,
    val_ratio: float = 0.2,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Chronological split indices."""
    n_train = int(n * train_ratio)
    n_val = int(n * val_ratio)
    train_idx = np.arange(0, n_train)
    val_idx = np.arange(n_train, n_train + n_val)
    test_idx = np.arange(n_train + n_val, n)
    return train_idx, val_idx, test_idx


def zscore(x: np.ndarray, eps: float = 1e-5) -> np.ndarray:
    mean = x.mean(axis=0, keepdims=True)
    std = x.std(axis=0, keepdims=True)
    return (x - mean) / (std + eps)

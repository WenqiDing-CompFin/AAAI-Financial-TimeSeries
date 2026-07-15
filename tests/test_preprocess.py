"""Unit tests for preprocessing and sample data."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data.preprocess import build_event_labels, make_windows, train_val_test_split
from src.data.sample_data import generate_sample_finance_dataset, generate_sample_minute_dataset
from src.data.dataset import FinanceEventDataset, MinuteForecastDataset


def test_make_windows():
    x = np.arange(20, dtype=float).reshape(10, 2)
    windows = make_windows(x, window_size=4, stride=2)
    assert windows.shape == (4, 4, 2)
    np.testing.assert_array_equal(windows[0, :, 0], [0, 2, 4, 6])


def test_build_event_labels():
    close = np.array([100.0, 100.0, 100.0, 100.0, 103.0, 99.0], dtype=float)
    # window_size=3, index 0 ends at t=2, next=t=3 -> 0% -> neutral
    # index 1 ends at t=3, next=t=4 -> +3% -> increase
    # index 2 ends at t=4, next=t=5 -> ~-3.9% -> decrease
    labels = build_event_labels(close, indices=np.array([0, 1, 2]), window_size=3, threshold=0.01)
    assert labels.tolist() == [1, 2, 0]


def test_split_sizes():
    tr, va, te = train_val_test_split(100, 0.6, 0.2)
    assert len(tr) == 60
    assert len(va) == 20
    assert len(te) == 20
    assert tr[-1] + 1 == va[0]


def test_sample_datasets(tmp_path: Path):
    daily = generate_sample_finance_dataset(tmp_path / "finance_daily", n_days=120, window_size=20)
    assert daily["npz"].exists()
    ds = FinanceEventDataset(tmp_path / "finance_daily", split="train")
    item = ds[0]
    assert item["x_time"].shape == (20, 9)
    assert item["y"].ndim == 0

    minute = generate_sample_minute_dataset(tmp_path / "minute", n_bars=400, window_size=60, horizon=5)
    assert minute["npz"].exists()
    mds = MinuteForecastDataset(tmp_path / "minute", split="train")
    mitem = mds[0]
    assert mitem["x_time"].shape == (60, 5)
    assert mitem["y"].shape == (5,)


def test_model_forward(tmp_path: Path):
    import torch
    from src.models import MultiModalEncoder

    generate_sample_finance_dataset(tmp_path / "finance_daily", n_days=80, window_size=20)
    ds = FinanceEventDataset(tmp_path / "finance_daily", split="all")
    batch_x = torch.stack([ds[i]["x_time"] for i in range(4)], dim=0)
    texts = [ds[i]["text"] for i in range(4)]
    model = MultiModalEncoder(enc_in=9, seq_len=20, num_outputs=3, d_model=64, n_heads=4, e_layers=1, d_ff=128, patch_len=4, stride=2)
    logits, emb = model(batch_x, texts)
    assert logits.shape == (4, 3)
    assert emb.shape[0] == 4

"""PyTorch datasets for TimeCAP financial experiments."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import torch
from torch.utils.data import Dataset

from .preprocess import train_val_test_split


def _load_summaries(path: Path) -> List[str]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    parts = [p.strip() for p in text.split("\n-----\n")]
    return parts


class FinanceEventDataset(Dataset):
    """Daily multi-asset event classification (decrease / neutral / increase)."""

    class_names = ["decrease", "neutral", "increase"]

    def __init__(
        self,
        root: Union[str, Path],
        split: str = "train",
        train_ratio: float = 0.6,
        val_ratio: float = 0.2,
        normalize: bool = True,
    ):
        root = Path(root)
        npz_path = root / "dataset.npz"
        if not npz_path.exists():
            raise FileNotFoundError(
                f"Missing {npz_path}. Run `python scripts/prepare_sample_data.py` first."
            )
        blob = np.load(npz_path, allow_pickle=True)
        self.time_series = blob["time_series"].astype(np.float32)
        self.indices = blob["indices"].astype(np.int64)
        self.labels = blob["labels"].astype(np.int64)
        self.channels = [str(c) for c in blob["channels"].tolist()]
        self.window_size = int(blob["window_size"][0])
        self.summaries = _load_summaries(root / "summaries.txt")
        self.normalize = normalize
        self.num_feature = self.time_series.shape[1]
        self.max_seq_len = self.window_size

        n = len(self.indices)
        train_idx, val_idx, test_idx = train_val_test_split(n, train_ratio, val_ratio)
        split_map = {"train": train_idx, "val": val_idx, "test": test_idx, "all": np.arange(n)}
        if split not in split_map:
            raise ValueError(f"Unknown split: {split}")
        self.sample_idx = split_map[split]

    def __len__(self) -> int:
        return len(self.sample_idx)

    def __getitem__(self, i: int) -> Dict[str, Any]:
        idx = int(self.sample_idx[i])
        start = int(self.indices[idx])
        x = self.time_series[start : start + self.window_size].copy()
        if self.normalize:
            mu = x.mean(axis=0, keepdims=True)
            std = x.std(axis=0, keepdims=True) + 1e-5
            x = (x - mu) / std
        text = self.summaries[idx] if idx < len(self.summaries) else ""
        return {
            "x_time": torch.from_numpy(x),
            "text": text,
            "y": torch.tensor(self.labels[idx], dtype=torch.long),
            "index": idx,
        }


class MinuteForecastDataset(Dataset):
    """Minute-level multi-step return forecasting."""

    def __init__(
        self,
        root: Union[str, Path],
        split: str = "train",
        train_ratio: float = 0.7,
        val_ratio: float = 0.15,
        normalize: bool = True,
    ):
        root = Path(root)
        npz_path = root / "dataset.npz"
        if not npz_path.exists():
            raise FileNotFoundError(
                f"Missing {npz_path}. Run `python scripts/prepare_sample_data.py` first."
            )
        blob = np.load(npz_path, allow_pickle=True)
        self.time_series = blob["time_series"].astype(np.float32)
        self.indices = blob["indices"].astype(np.int64)
        self.targets = blob["targets"].astype(np.float32)
        self.channels = [str(c) for c in blob["channels"].tolist()]
        self.window_size = int(blob["window_size"][0])
        self.horizon = int(blob["horizon"][0])
        self.summaries = _load_summaries(root / "summaries.txt")
        self.normalize = normalize
        self.num_feature = self.time_series.shape[1]
        self.max_seq_len = self.window_size

        n = len(self.indices)
        train_idx, val_idx, test_idx = train_val_test_split(n, train_ratio, val_ratio)
        split_map = {"train": train_idx, "val": val_idx, "test": test_idx, "all": np.arange(n)}
        self.sample_idx = split_map[split]

    def __len__(self) -> int:
        return len(self.sample_idx)

    def __getitem__(self, i: int) -> Dict[str, Any]:
        idx = int(self.sample_idx[i])
        start = int(self.indices[idx])
        x = self.time_series[start : start + self.window_size].copy()
        if self.normalize:
            mu = x.mean(axis=0, keepdims=True)
            std = x.std(axis=0, keepdims=True) + 1e-5
            x = (x - mu) / std
        text = self.summaries[idx] if idx < len(self.summaries) else ""
        return {
            "x_time": torch.from_numpy(x),
            "text": text,
            "y": torch.from_numpy(self.targets[idx]),
            "index": idx,
        }


def collate_batch(batch: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "x_time": torch.stack([b["x_time"] for b in batch], dim=0),
        "text": [b["text"] for b in batch],
        "y": torch.stack([b["y"] for b in batch], dim=0),
        "index": torch.tensor([b["index"] for b in batch], dtype=torch.long),
    }

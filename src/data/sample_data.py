"""Synthetic sample datasets so the repo runs without proprietary market dumps."""

from __future__ import annotations

from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd


CHANNEL_NAMES = [
    "sp500",
    "vix",
    "nikkei",
    "ftse",
    "gold",
    "crude_oil",
    "eur_usd",
    "usd_jpy",
    "usd_cny",
]


def _gbm(n: int, start: float, mu: float, sigma: float, rng: np.random.Generator) -> np.ndarray:
    shocks = rng.normal(mu, sigma, size=n)
    path = start * np.exp(np.cumsum(shocks))
    return path.astype(np.float64)


def generate_sample_finance_dataset(
    out_dir: str | Path,
    n_days: int = 260,
    window_size: int = 20,
    seed: int = 42,
) -> Dict[str, Path]:
    """
    Create a small daily multi-asset sample mimicking the TimeCAP finance setup.
    Writes CSV + NPZ under `out_dir` (default: data/sample/finance_daily).
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)

    starts = {
        "sp500": 4000.0,
        "vix": 18.0,
        "nikkei": 28000.0,
        "ftse": 7500.0,
        "gold": 1800.0,
        "crude_oil": 75.0,
        "eur_usd": 1.08,
        "usd_jpy": 140.0,
        "usd_cny": 7.1,
    }
    vols = {
        "sp500": 0.01,
        "vix": 0.03,
        "nikkei": 0.012,
        "ftse": 0.009,
        "gold": 0.008,
        "crude_oil": 0.02,
        "eur_usd": 0.004,
        "usd_jpy": 0.005,
        "usd_cny": 0.003,
    }

    data = {name: _gbm(n_days, starts[name], 0.0002, vols[name], rng) for name in CHANNEL_NAMES}
    # VIX tends to spike when SPX drops
    data["vix"] = np.clip(data["vix"] + rng.normal(0, 0.5, n_days), 10.0, 80.0)

    dates = pd.bdate_range("2023-01-02", periods=n_days)
    df = pd.DataFrame(data, index=dates)
    df.index.name = "date"

    series = df[CHANNEL_NAMES].to_numpy()
    indices = np.arange(0, n_days - window_size)
    # labels from next-day SPX return
    close = df["sp500"].to_numpy()
    labels = []
    for s in indices:
        end = s + window_size - 1
        ret = (close[end + 1] - close[end]) / close[end]
        if ret <= -0.01:
            labels.append(0)
        elif ret >= 0.01:
            labels.append(2)
        else:
            labels.append(1)
    labels = np.asarray(labels, dtype=np.int64)

    summaries = []
    for i, s in enumerate(indices):
        trend = "firming" if close[s + window_size - 1] >= close[s] else "softening"
        vol_state = "elevated" if data["vix"][s : s + window_size].mean() > 20 else "contained"
        summaries.append(
            f"Equities look {trend} over the recent window while volatility remains {vol_state}. "
            f"Cross-asset cues suggest a cautious near-term risk tone. "
            f"FX and commodity co-moves are mixed, pointing to selective positioning."
        )

    csv_path = out_dir / "time_series.csv"
    npz_path = out_dir / "dataset.npz"
    summary_path = out_dir / "summaries.txt"
    meta_path = out_dir / "README.md"

    df.to_csv(csv_path)
    np.savez_compressed(
        npz_path,
        time_series=series,
        indices=indices,
        labels=labels,
        channels=np.array(CHANNEL_NAMES),
        window_size=np.array([window_size]),
    )
    summary_path.write_text("\n-----\n".join(summaries), encoding="utf-8")
    meta_path.write_text(
        "# Sample daily finance dataset\n\n"
        "Synthetic multi-asset daily series for local demos and unit tests.\n"
        "Replace with real processed data under `data/processed/` for experiments.\n",
        encoding="utf-8",
    )
    return {
        "csv": csv_path,
        "npz": npz_path,
        "summaries": summary_path,
        "readme": meta_path,
    }


def generate_sample_minute_dataset(
    out_dir: str | Path,
    n_bars: int = 780,
    window_size: int = 60,
    horizon: int = 5,
    seed: int = 7,
) -> Dict[str, Path]:
    """Synthetic SPY-like 1-minute OHLCV for forecasting demos."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)

    close = _gbm(n_bars, 450.0, 0.0, 0.0008, rng)
    open_ = np.roll(close, 1)
    open_[0] = close[0]
    high = np.maximum(open_, close) * (1 + rng.uniform(0, 0.001, n_bars))
    low = np.minimum(open_, close) * (1 - rng.uniform(0, 0.001, n_bars))
    volume = rng.integers(50_000, 400_000, size=n_bars).astype(np.float64)

    df = pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close, "volume": volume}
    )
    series = df.to_numpy()
    max_start = n_bars - window_size - horizon
    indices = np.arange(0, max_start)
    # regression target: future horizon close returns relative to last close in window
    targets = []
    for s in indices:
        last = close[s + window_size - 1]
        future = close[s + window_size : s + window_size + horizon]
        targets.append((future - last) / last)
    targets = np.asarray(targets, dtype=np.float64)

    summaries = []
    for s in indices:
        move = close[s + window_size - 1] - close[s]
        tone = "bid-driven grind higher" if move > 0 else "offer-led drift lower"
        summaries.append(
            f"Intraday tape shows a {tone} with moderate participation. "
            f"Range expansion is limited and liquidity looks orderly into the next few minutes."
        )

    csv_path = out_dir / "ohlcv.csv"
    npz_path = out_dir / "dataset.npz"
    summary_path = out_dir / "summaries.txt"

    df.to_csv(csv_path, index=False)
    np.savez_compressed(
        npz_path,
        time_series=series,
        indices=indices,
        targets=targets,
        channels=np.array(["open", "high", "low", "close", "volume"]),
        window_size=np.array([window_size]),
        horizon=np.array([horizon]),
    )
    summary_path.write_text("\n-----\n".join(summaries), encoding="utf-8")
    return {"csv": csv_path, "npz": npz_path, "summaries": summary_path}

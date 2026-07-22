"""Deterministic offline data generation and leakage-safe feature construction."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


FEATURE_COLUMNS = ("return_1m", "return_3m", "volatility_6m", "volume_change_1m")


def generate_synthetic_prices(
    seed: int = 7, assets: int = 30, periods: int = 180
) -> pd.DataFrame:
    """Generate monthly prices for an offline, reproducible demonstration.

    This is a pipeline fixture, not a calibrated market simulator. The target is
    deliberately generated from lagged returns and a slowly changing common
    regime so that the baseline has a measurable but modest signal.
    """
    if assets < 5 or periods < 24:
        raise ValueError("Use at least 5 assets and 24 periods.")
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2010-01-31", periods=periods, freq="ME")
    tickers = [f"A{i:03d}" for i in range(assets)]
    asset_bias = rng.normal(0.0, 0.0015, assets)
    asset_vol = rng.uniform(0.012, 0.035, assets)
    previous = np.zeros(assets)
    prices = np.full(assets, 100.0)
    records: list[dict[str, object]] = []

    for step, date in enumerate(dates):
        regime = 0.002 * np.sin(step / 9.0) + rng.normal(0.0, 0.003)
        returns = (
            0.001
            + regime
            + asset_bias
            + 0.10 * previous
            + rng.normal(0.0, asset_vol)
        )
        returns = np.clip(returns, -0.35, 0.35)
        prices *= 1.0 + returns
        volume = rng.lognormal(mean=12.0, sigma=0.35, size=assets)
        for idx, ticker in enumerate(tickers):
            records.append(
                {
                    "date": date,
                    "ticker": ticker,
                    "close": float(prices[idx]),
                    "volume": float(volume[idx]),
                }
            )
        previous = returns

    return pd.DataFrame.from_records(records)


def build_feature_panel(prices: pd.DataFrame) -> pd.DataFrame:
    """Create features known at month ``t`` and the target return at ``t+1``.

    All shifts and rolling windows are performed within ticker. The target is
    never used in feature construction, and the final row for each ticker is
    dropped because its next-month return is unavailable.
    """
    required = {"date", "ticker", "close", "volume"}
    missing = required.difference(prices.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    if prices[["date", "ticker"]].duplicated().any():
        raise ValueError("Each date/ticker pair must be unique.")
    panel = prices.copy()
    panel["date"] = pd.to_datetime(panel["date"], errors="coerce")
    if panel["date"].isna().any() or panel["ticker"].isna().any():
        raise ValueError("date and ticker must be valid and non-missing.")
    if (panel["close"] <= 0).any() or (panel["volume"] <= 0).any():
        raise ValueError("close and volume must be positive.")
    panel = panel.sort_values(["ticker", "date"]).reset_index(drop=True)
    grouped = panel.groupby("ticker", sort=False)
    returns = grouped["close"].pct_change(fill_method=None)
    panel["return_1m"] = returns
    panel["return_3m"] = grouped["close"].shift(1).div(grouped["close"].shift(4)).sub(1)
    panel["volatility_6m"] = returns.groupby(panel["ticker"], sort=False).transform(
        lambda values: values.rolling(6, min_periods=6).std(ddof=1).shift(1)
    )
    panel["volume_change_1m"] = grouped["volume"].pct_change(fill_method=None)
    panel["target_return_1m"] = grouped["close"].shift(-1).div(panel["close"]).sub(1)
    panel = panel.dropna(subset=[*FEATURE_COLUMNS, "target_return_1m"])
    return panel.reset_index(drop=True)


def save_synthetic_panel(path: str | Path, seed: int = 7) -> None:
    """Write the generated raw panel for inspection or downstream experiments."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    generate_synthetic_prices(seed=seed).to_csv(destination, index=False)

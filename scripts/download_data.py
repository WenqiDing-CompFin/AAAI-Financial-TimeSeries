#!/usr/bin/env python3
"""
Download public market data for the financial adaptation experiments.

Daily mode: multi-asset panel approximating the original TimeCAP finance channels.
Minute mode: SPY 1-minute OHLCV via yfinance (limited history from Yahoo).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


TICKERS_DAILY = {
    "sp500": "^GSPC",
    "vix": "^VIX",
    "nikkei": "^N225",
    "ftse": "^FTSE",
    "gold": "GC=F",
    "crude_oil": "CL=F",
    "eur_usd": "EURUSD=X",
    "usd_jpy": "JPY=X",
    "usd_cny": "CNY=X",
}


def download_daily(start: str, end: str, out_dir: Path) -> Path:
    import yfinance as yf

    frames = []
    for name, ticker in TICKERS_DAILY.items():
        print(f"Downloading {name} ({ticker})...")
        df = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=True)
        if df.empty:
            raise RuntimeError(f"No data for {ticker}")
        close = df["Close"]
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]
        close.name = name
        frames.append(close)

    panel = pd.concat(frames, axis=1).dropna().sort_index()
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "time_series.csv"
    panel.to_csv(csv_path)

    window_size = 20
    series = panel.to_numpy(dtype=np.float64)
    indices = np.arange(0, len(panel) - window_size)
    close = panel["sp500"].to_numpy()
    labels = []
    for s in indices:
        end_i = s + window_size - 1
        ret = (close[end_i + 1] - close[end_i]) / close[end_i]
        if ret <= -0.01:
            labels.append(0)
        elif ret >= 0.01:
            labels.append(2)
        else:
            labels.append(1)

    np.savez_compressed(
        out_dir / "dataset.npz",
        time_series=series,
        indices=indices,
        labels=np.asarray(labels, dtype=np.int64),
        channels=np.array(list(TICKERS_DAILY.keys())),
        window_size=np.array([window_size]),
    )
    # Placeholder summaries — replace by running agent contextualization
    summaries = [
        "Market tape shows mixed risk sentiment across equities, vol, FX, and commodities."
        for _ in indices
    ]
    (out_dir / "summaries.txt").write_text("\n-----\n".join(summaries), encoding="utf-8")
    print(f"Saved daily panel -> {csv_path} ({len(panel)} rows)")
    return csv_path


def download_minute(symbol: str, out_dir: Path, window_size: int = 60, horizon: int = 5) -> Path:
    import yfinance as yf

    print(f"Downloading {symbol} 1-minute bars (Yahoo limits lookback)...")
    df = yf.download(symbol, period="5d", interval="1m", progress=False, auto_adjust=True)
    if df.empty:
        raise RuntimeError(f"No minute data for {symbol}")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0].lower() for c in df.columns]
    else:
        df.columns = [c.lower() for c in df.columns]
    cols = ["open", "high", "low", "close", "volume"]
    df = df[cols].dropna()

    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "ohlcv.csv"
    df.to_csv(csv_path)

    series = df.to_numpy(dtype=np.float64)
    close = df["close"].to_numpy()
    max_start = len(df) - window_size - horizon
    indices = np.arange(0, max(max_start, 0))
    targets = []
    for s in indices:
        last = close[s + window_size - 1]
        future = close[s + window_size : s + window_size + horizon]
        targets.append((future - last) / last)

    np.savez_compressed(
        out_dir / "dataset.npz",
        time_series=series,
        indices=indices,
        targets=np.asarray(targets, dtype=np.float64),
        channels=np.array(cols),
        window_size=np.array([window_size]),
        horizon=np.array([horizon]),
    )
    summaries = [
        "Intraday liquidity and short-horizon momentum appear orderly in the recent minute window."
        for _ in indices
    ]
    (out_dir / "summaries.txt").write_text("\n-----\n".join(summaries), encoding="utf-8")
    print(f"Saved minute bars -> {csv_path} ({len(df)} rows)")
    return csv_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["daily", "minute"], default="daily")
    parser.add_argument("--start", default="2019-01-01")
    parser.add_argument("--end", default="2023-12-31")
    parser.add_argument("--symbol", default="SPY")
    parser.add_argument("--out-root", default="data/processed")
    args = parser.parse_args()

    out_root = Path(args.out_root)
    if args.mode == "daily":
        download_daily(args.start, args.end, out_root / "finance_daily")
    else:
        download_minute(args.symbol, out_root / "minute")


if __name__ == "__main__":
    main()

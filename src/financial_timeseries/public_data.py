"""Official public factor returns for a real-market forecasting baseline."""

from __future__ import annotations

import csv
import hashlib
import io
import re
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd


SOURCE_PAGE = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html"
FIVE_FACTOR_URL = (
    "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
    "F-F_Research_Data_5_Factors_2x3_CSV.zip"
)
MOMENTUM_URL = (
    "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
    "F-F_Momentum_Factor_CSV.zip"
)
PUBLIC_FEATURE_COLUMNS = (
    "market_excess",
    "size",
    "value",
    "profitability",
    "investment",
    "momentum",
    "market_return_3m",
    "market_volatility_6m",
)


def parse_monthly_factor_csv(
    text: str, expected_columns: tuple[str, ...]
) -> pd.DataFrame:
    """Parse the first YYYYMM monthly block from a Data Library CSV."""
    rows = list(csv.reader(io.StringIO(text)))
    header_index = next(
        (
            index
            for index, row in enumerate(rows)
            if set(expected_columns).issubset(value.strip() for value in row)
        ),
        None,
    )
    if header_index is None:
        raise ValueError(f"Could not find monthly header: {expected_columns}")
    header = [value.strip() for value in rows[header_index]]
    records: list[dict[str, object]] = []
    for row in rows[header_index + 1 :]:
        if not row or not re.fullmatch(r"\d{6}", row[0].strip()):
            break
        record: dict[str, object] = {
            "date": pd.Period(row[0].strip(), freq="M").to_timestamp("M")
        }
        for position, column in enumerate(header[1:], start=1):
            if not column:
                continue
            value = float(row[position].strip())
            record[column] = np.nan if value <= -99.0 else value / 100.0
        records.append(record)
    if not records:
        raise ValueError("No monthly factor observations found")
    return pd.DataFrame(records).sort_values("date").reset_index(drop=True)


def _read_archive(
    url: str, cache_dir: Path, timeout_seconds: int = 30
) -> tuple[str, dict[str, str]]:
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = cache_dir / url.rsplit("/", 1)[-1]
    if path.exists():
        payload = path.read_bytes()
    else:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "financial-timeseries-baseline/0.1"},
        )
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            payload = response.read()
        path.write_bytes(payload)
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        members = [name for name in archive.namelist() if name.lower().endswith(".csv")]
        if len(members) != 1:
            raise ValueError(f"Expected one CSV in {path.name}, found {members}")
        member = members[0]
        text = archive.read(member).decode("cp1252")
    return text, {
        "url": url,
        "cache_file": path.name,
        "archive_member": member,
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def load_public_factor_returns(
    cache_dir: str | Path = "data/raw/fama_french",
) -> tuple[pd.DataFrame, dict[str, object]]:
    """Download and align official monthly five-factor and momentum returns."""
    destination = Path(cache_dir)
    five_text, five_metadata = _read_archive(FIVE_FACTOR_URL, destination)
    momentum_text, momentum_metadata = _read_archive(MOMENTUM_URL, destination)
    five = parse_monthly_factor_csv(
        five_text, ("Mkt-RF", "SMB", "HML", "RMW", "CMA", "RF")
    )
    momentum = parse_monthly_factor_csv(momentum_text, ("Mom",))
    returns = five.merge(momentum, on="date", how="inner", validate="one_to_one")
    returns = returns.rename(
        columns={
            "Mkt-RF": "market_excess",
            "SMB": "size",
            "HML": "value",
            "RMW": "profitability",
            "CMA": "investment",
            "RF": "risk_free",
            "Mom": "momentum",
        }
    )
    metadata: dict[str, object] = {
        "source_page": SOURCE_PAGE,
        "return_unit": "decimal monthly return",
        "five_factor_archive": five_metadata,
        "momentum_archive": momentum_metadata,
        "source_start": str(returns["date"].min().date()),
        "source_end": str(returns["date"].max().date()),
        "source_observations": len(returns),
    }
    return returns, metadata


def build_public_forecast_panel(returns: pd.DataFrame) -> pd.DataFrame:
    """Build month-t factor features for month-t+1 market-excess prediction."""
    required = {
        "date",
        "market_excess",
        "size",
        "value",
        "profitability",
        "investment",
        "momentum",
    }
    missing = required.difference(returns.columns)
    if missing:
        raise ValueError(f"Missing public factor columns: {sorted(missing)}")
    panel = returns.sort_values("date").copy()
    panel["market_return_3m"] = (
        panel["market_excess"].add(1.0).rolling(3, min_periods=3).apply(np.prod).sub(1.0)
    )
    panel["market_volatility_6m"] = panel["market_excess"].rolling(
        6, min_periods=6
    ).std(ddof=1)
    panel["target_return_1m"] = panel["market_excess"].shift(-1)
    panel["ticker"] = "US_MARKET_EXCESS"
    panel = panel.dropna(subset=[*PUBLIC_FEATURE_COLUMNS, "target_return_1m"])
    return panel.reset_index(drop=True)

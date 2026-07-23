"""Run a held-out forecasting baseline on official U.S. factor returns."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from financial_timeseries.experiment import calendar_split, run_experiment  # noqa: E402
from financial_timeseries.public_data import (  # noqa: E402
    PUBLIC_FEATURE_COLUMNS,
    build_public_forecast_panel,
    load_public_factor_returns,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Forecast next-month official U.S. market excess return"
    )
    parser.add_argument(
        "--cache-dir", type=Path, default=ROOT / "data/raw/fama_french"
    )
    parser.add_argument(
        "--output-dir", type=Path, default=ROOT / "results/public_market"
    )
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    returns, source_metadata = load_public_factor_returns(args.cache_dir)
    panel = build_public_forecast_panel(returns)
    split = calendar_split(panel, train_end="2004-12-31", validation_end="2014-12-31")
    metrics, predictions = run_experiment(
        panel,
        feature_columns=PUBLIC_FEATURE_COLUMNS,
        persistence_column="market_excess",
        split=split,
    )
    metrics.to_csv(args.output_dir / "metrics.csv", index=False)
    predictions.to_csv(args.output_dir / "test_predictions.csv", index=False)
    metadata = {
        **source_metadata,
        "features_at_month_t": list(PUBLIC_FEATURE_COLUMNS),
        "target": "official U.S. market excess return at month t+1",
        "train_end": "2004-12-31",
        "validation_period": "2005-01 through 2014-12",
        "test_period": "2015-01 through latest",
        "selection_metric": "validation mean squared error",
        "test_is_used_for_model_selection": False,
        "claim_boundary": (
            "Real aggregate factor returns; forecasting baseline only, not a "
            "TimeCAP reimplementation or investable trading strategy."
        ),
    }
    with (args.output_dir / "experiment_metadata.json").open(
        "w", encoding="utf-8"
    ) as handle:
        json.dump(metadata, handle, indent=2)

    chart = predictions.set_index("date")[["actual", "persistence", "ridge"]]
    rolling = chart.rolling(12, min_periods=6).mean()
    ax = rolling.plot(figsize=(10, 5), title="Held-out rolling 12-month mean return")
    ax.axhline(0.0, color="black", linewidth=0.8)
    ax.set_ylabel("Monthly return")
    ax.grid(alpha=0.25)
    ax.figure.tight_layout()
    ax.figure.savefig(args.output_dir / "heldout_predictions.png", dpi=160)
    plt.close(ax.figure)
    print(metrics.to_string(index=False))
    print("\nOfficial aggregate market data; no investable strategy claim is made.")


if __name__ == "__main__":
    main()

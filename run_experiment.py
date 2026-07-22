"""Run the offline financial forecasting experiment."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from financial_timeseries.data import build_feature_panel, generate_synthetic_prices  # noqa: E402
from financial_timeseries.experiment import run_experiment  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a leakage-safe financial time-series baseline.")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    panel = build_feature_panel(generate_synthetic_prices(seed=args.seed))
    metrics, predictions = run_experiment(panel)
    metrics.to_csv(args.output_dir / "metrics.csv", index=False)
    predictions.to_csv(args.output_dir / "test_predictions.csv", index=False)
    with (args.output_dir / "experiment_metadata.json").open("w", encoding="utf-8") as handle:
        json.dump(
            {
                "seed": args.seed,
                "data_source": "deterministic synthetic monthly panel",
                "rows_after_feature_warmup": len(panel),
                "feature_columns": ["return_1m", "return_3m", "volatility_6m", "volume_change_1m"],
                "target": "next-month close-to-close return",
                "split": {"train": 0.60, "validation": 0.20, "test": 0.20},
                "test_is_used_for_model_selection": False,
            },
            handle,
            indent=2,
        )

    test = predictions.set_index("date")
    wealth = (1.0 + test[["actual", "persistence", "ridge"]]).cumprod()
    ax = wealth.plot(figsize=(9, 5), title="Held-out synthetic test: growth of 1.0")
    ax.set_ylabel("Growth of 1.0")
    ax.grid(alpha=0.25)
    ax.figure.tight_layout()
    ax.figure.savefig(args.output_dir / "test_equity_curve.png", dpi=160)
    plt.close(ax.figure)
    print(metrics.to_string(index=False))
    print("\nSynthetic demonstration only; no live or historical-market claim is made.")


if __name__ == "__main__":
    main()

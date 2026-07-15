#!/usr/bin/env python3
"""Generate synthetic sample datasets for local demos and tests."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data.sample_data import generate_sample_finance_dataset, generate_sample_minute_dataset


def main():
    parser = argparse.ArgumentParser(description="Prepare sample financial datasets")
    parser.add_argument("--out-root", default="data/sample")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    out_root = Path(args.out_root)
    daily = generate_sample_finance_dataset(out_root / "finance_daily", seed=args.seed)
    minute = generate_sample_minute_dataset(out_root / "minute", seed=args.seed)
    print("Wrote daily finance sample:")
    for k, v in daily.items():
        print(f"  {k}: {v}")
    print("Wrote minute forecast sample:")
    for k, v in minute.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()

#!/usr/bin/env bash
# End-to-end smoke pipeline on sample data
set -euo pipefail
cd "$(dirname "$0")/.."

echo "[1/3] Preparing sample data..."
python3 scripts/prepare_sample_data.py

echo "[2/3] Training multi-modal encoder (daily event)..."
python3 src/train.py --config configs/default.yaml

echo "[3/3] Evaluating..."
python3 src/evaluate.py --config configs/default.yaml --split test

echo "Done. Metrics under results/metrics/"

# TimeCAP Financial Reimplementation

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-ee4c2c.svg)](https://pytorch.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Reimplementation of **[AAAI 2025] TimeCAP: Learning to Contextualize, Augment, and Predict Time Series Events with Large Language Model Agents** (Lee et al.), adapted to **public financial market data**.

- Paper: https://arxiv.org/abs/2502.11418
- Upstream datasets: https://github.com/geon0325/TimeCAP

**Extensions in this repo**

1. Cleaned, research-friendly layout for PhD / FE portfolio work
2. Original-style **daily multi-asset event prediction** (decrease / neutral / increase)
3. **S&P 500 / SPY minute-level forecasting** track (multi-step return regression)

---

## Repository structure

```text
├── configs/                 # Experiment YAML configs
│   ├── default.yaml         # Daily event classification
│   └── minute_forecast.yaml # Minute-level forecasting
├── data/
│   ├── raw/                 # Optional raw downloads
│   ├── processed/           # Real processed panels
│   └── sample/              # Synthetic demo data (generated)
├── docs/
│   └── architecture.md      # Method & module notes
├── notebooks/
│   └── 01_eda_finance_sample.ipynb
├── results/
│   ├── checkpoints/
│   ├── figures/
│   └── metrics/
├── scripts/
│   ├── prepare_sample_data.py
│   ├── download_data.py
│   ├── run_agents.py
│   └── run_pipeline.sh
├── src/
│   ├── agents/              # LLM contextualizer & predictor (A_C, A_P)
│   ├── data/                # Datasets & preprocessing
│   ├── models/              # Multi-modal encoder
│   ├── prompts/             # Finance / intraday prompts
│   ├── utils/
│   ├── train.py
│   └── evaluate.py
├── tests/
├── requirements.txt
└── README.md
```

---

## Quick start

```bash
git clone https://github.com/WenqiDing-CompFin/AAAI-Financial-TimeSeries.git
cd AAAI-Financial-TimeSeries

python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 1) Build synthetic sample data (no API / no Yahoo needed)
python scripts/prepare_sample_data.py

# 2) Train multi-modal encoder on daily event task
python src/train.py --config configs/default.yaml

# 3) Evaluate
python src/evaluate.py --config configs/default.yaml --split test
```

Or run the smoke pipeline:

```bash
bash scripts/run_pipeline.sh
```

### Minute-level track

```bash
python src/train.py --config configs/minute_forecast.yaml
python src/evaluate.py --config configs/minute_forecast.yaml --split test
```

### LLM agents (TimeCP / TimeCAP)

```bash
cp .env.example .env   # set OPENAI_API_KEY
python scripts/run_agents.py --mode both --index 0
```

Without an API key the agents run in **dry-run** mode so the rest of the stack stays usable.

### Real market data

```bash
# Daily multi-asset panel (~TimeCAP finance channels)
python scripts/download_data.py --mode daily --start 2019-01-01 --end 2023-12-31

# SPY 1-minute bars (Yahoo lookback is limited)
python scripts/download_data.py --mode minute --symbol SPY
```

Point configs at `data/processed/...` by setting `data.sample_root` / `data.root` in the YAML files.

---

## Method sketch

| Component | Role |
|-----------|------|
| **A_C** | LLM contextualizes a financial window into a short analyst-style summary |
| **Encoder** | Patch-TST-style time encoder + text embedding → event/forecast head + retrieval vector |
| **A_P** | LLM predicts from the summary; TimeCAP adds retrieved in-context examples |

See [`docs/architecture.md`](docs/architecture.md) for details.

---

## Preliminary results (synthetic sample smoke runs)

| Setup | Dataset | Metric | Value |
|-------|---------|--------|-------|
| Multi-modal encoder | Synthetic daily events | Acc / F1 | 0.60 / 0.25 |
| Multi-modal encoder | Synthetic SPY minutes | MSE / MAE | 0.016 / 0.101 |
| TimeCAP (paper) | Real S&P 500 daily events | F1 | see paper |

These sample numbers are only for pipeline sanity checks. Replace with real-data experiments under `data/processed/` and refresh `results/metrics/`.

---

## Tests

```bash
pytest -q
```

---

## Reference

```bibtex
@inproceedings{lee2025timecap,
  title={TimeCAP: Learning to Contextualize, Augment, and Predict Time Series Events with Large Language Model Agents},
  author={Lee, Geon and Yu, Wenchao and Shin, Kijung and Cheng, Wei and Chen, Haifeng},
  booktitle={AAAI},
  year={2025}
}
```

---

## Contact

- Name: Wenqi Ding
- Email: 1460441276@qq.com
- Affiliation: Undergraduate Researcher, Hubei Digital Finance Lab

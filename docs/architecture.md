# Architecture notes

## TimeCAP (paper) vs this repo

Original TimeCAP (AAAI 2025) uses two frozen LLM agents plus a trainable multi-modal encoder:

1. **A_C (Contextualizer)** — LLM summarizes the raw time series into domain-aware text.
2. **Multi-modal encoder E_φ** — fuses patched time series tokens with the text embedding; outputs a class logit and a retrieval embedding.
3. **A_P (Predictor)** — LLM predicts the event, optionally augmented with nearest-neighbor summaries retrieved via E_φ embeddings (TimeCAP), or using only the current summary (TimeCP).

## Financial adaptation in this repository

| Track | Task | Data | Target |
|-------|------|------|--------|
| `daily_event` | 3-class event prediction (paper setup) | Multi-asset daily panel | Next-day ±1% move of S&P 500 / Nikkei |
| `minute_forecast` | Multi-step return regression (extension) | SPY 1-minute OHLCV | Next-H minute close returns |

## Module map

- `src/agents` — A_C / A_P wrappers (OpenAI-compatible; dry-run without API key)
- `src/models` — multi-modal encoder reimplementation
- `src/data` — datasets, sample generators, preprocessing
- `src/prompts` — finance / intraday prompt templates
- `scripts/` — data prep, download, agent CLI, smoke pipeline

## Attribution

Paper: Lee et al., *TimeCAP*, AAAI 2025 — https://arxiv.org/abs/2502.11418  
Upstream datasets / notebooks: https://github.com/geon0325/TimeCAP

# TimeCAP: Learning to Contextualize, Augment, and Predict Time Series Events with Large Language Model Agents Reimplementation & Financial Adaptation

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-ee4c2c.svg)](https://pytorch.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

This repository contains my reimplementation of **[AAAI 2025] TimeCAP: Learning to Contextualize, Augment, and Predict Time Series Events with Large Language Model Agents** by Geon Lee, Wenchao Yu, Kijung Shin, Wei Cheng, Haifeng Chen.  
The original paper addresses time series event prediction by leveraging Large Language Model agents for contextualization and data augmentation.

**My extension**: Adapting the model to **public financial market data (e.g., S&P 500 minute-level prices)** for **forecasting** tasks.

This work is part of my preparation for PhD applications in Financial Engineering, with a focus on LLM applications in finance.

## Repository Structure

```
├── src/                # Source code
│   ├── model.py        # Core model architecture
│   ├── train.py        # Training loop
│   └── utils.py        # Data preprocessing
├── notebooks/          # Exploratory analysis
├── data/               # Sample data (anonymized)
├── results/            # Outputs and visualizations
└── README.md

```

## Setup & Usage

```bash
git clone https://github.com/WenqiDing-CompFin/AAAI-Financial-TimeSeries.git
cd AAAI-Financial-TimeSeries
pip install -r requirements.txt
python src/train.py
```

## Preliminary Results

| Model | Dataset | MSE | MAE |
|-------|---------|-----|-----|
| Original (reported) | ICEWS14 | [Value] | [Value] |
| My Implementation | S&P 500 minute-level | [Value] | [Value] |

## Demo Video

[Link to demo video - Coming Soon]

## Reference

- Original Paper: https://arxiv.org/abs/2502.11418
- Original Code: https://github.com/geon0325/TimeCAP

## Contact

- Name: Wenqi Ding
- Email: 1460441276@qq.com
- Affiliation: Undergraduate Researcher, Hubei Digital Finance Lab

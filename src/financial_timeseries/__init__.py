"""Reproducible financial time-series forecasting baseline."""

from .data import build_feature_panel, generate_synthetic_prices
from .experiment import run_experiment

__all__ = ["build_feature_panel", "generate_synthetic_prices", "run_experiment"]

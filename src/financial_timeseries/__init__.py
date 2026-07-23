"""Reproducible financial time-series forecasting baseline."""

from .data import build_feature_panel, generate_synthetic_prices
from .experiment import calendar_split, run_experiment
from .public_data import build_public_forecast_panel, load_public_factor_returns

__all__ = [
    "build_feature_panel",
    "build_public_forecast_panel",
    "calendar_split",
    "generate_synthetic_prices",
    "load_public_factor_returns",
    "run_experiment",
]

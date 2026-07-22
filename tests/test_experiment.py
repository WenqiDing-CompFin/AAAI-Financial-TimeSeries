from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from financial_timeseries.data import (  # noqa: E402
    FEATURE_COLUMNS,
    build_feature_panel,
    generate_synthetic_prices,
)
from financial_timeseries.experiment import chronological_split, run_experiment  # noqa: E402
from financial_timeseries.metrics import regression_metrics  # noqa: E402


def test_generator_is_deterministic_and_target_stays_within_ticker():
    first = build_feature_panel(generate_synthetic_prices(seed=11, assets=6, periods=36))
    second = build_feature_panel(generate_synthetic_prices(seed=11, assets=6, periods=36))
    pd.testing.assert_frame_equal(first, second)
    assert first.groupby("ticker").size().nunique() == 1


def test_feature_warmup_and_target_are_finite():
    panel = build_feature_panel(generate_synthetic_prices(seed=3, assets=6, periods=36))
    values = panel[list(FEATURE_COLUMNS) + ["target_return_1m"]]
    assert values.notna().all().all()
    assert np.isfinite(values).all().all()


def test_chronological_split_has_disjoint_ordered_dates():
    panel = build_feature_panel(generate_synthetic_prices(seed=4, assets=6, periods=48))
    split = chronological_split(panel)
    train_dates = set(split.train.date)
    validation_dates = set(split.validation.date)
    test_dates = set(split.test.date)
    assert not train_dates & validation_dates
    assert not train_dates & test_dates
    assert not validation_dates & test_dates
    assert max(train_dates) < min(validation_dates) < min(test_dates)


def test_experiment_selects_from_validation_and_reports_test():
    panel = build_feature_panel(generate_synthetic_prices(seed=5, assets=8, periods=60))
    metrics, predictions = run_experiment(panel)
    assert set(metrics["model"]) == {"persistence", "ridge"}
    assert set(metrics["split"]) == {"test"}
    assert predictions["date"].min() == pd.to_datetime(metrics["start_date"].iloc[0])
    assert metrics["n_observations"].gt(0).all()


def test_metrics_reject_shape_mismatch():
    with pytest.raises(ValueError):
        regression_metrics(np.ones(3), np.ones(2))

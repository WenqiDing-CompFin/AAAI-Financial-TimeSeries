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
from financial_timeseries.experiment import (  # noqa: E402
    calendar_split,
    chronological_split,
    run_experiment,
)
from financial_timeseries.metrics import regression_metrics  # noqa: E402
from financial_timeseries.public_data import (  # noqa: E402
    PUBLIC_FEATURE_COLUMNS,
    build_public_forecast_panel,
    parse_monthly_factor_csv,
)


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


def test_public_factor_parser_and_feature_timing():
    five_fixture = """Fixture
,Mkt-RF,SMB,HML,RMW,CMA,RF
201401,1.0,0.1,0.2,0.3,0.4,0.0
201402,2.0,0.1,0.2,0.3,0.4,0.0

Annual Factors
"""
    parsed = parse_monthly_factor_csv(
        five_fixture, ("Mkt-RF", "SMB", "HML", "RMW", "CMA", "RF")
    ).rename(
        columns={
            "Mkt-RF": "market_excess",
            "SMB": "size",
            "HML": "value",
            "RMW": "profitability",
            "CMA": "investment",
        }
    )
    assert parsed.loc[0, "market_excess"] == pytest.approx(0.01)

    dates = pd.date_range("2000-01-31", periods=24, freq="ME")
    returns = pd.DataFrame({"date": dates})
    for index, column in enumerate(
        ("market_excess", "size", "value", "profitability", "investment", "momentum")
    ):
        returns[column] = np.linspace(-0.02, 0.03, len(dates)) + index * 0.001
    panel = build_public_forecast_panel(returns)
    first_source_index = returns.index[returns["date"].eq(panel.loc[0, "date"])][0]
    assert panel.loc[0, "target_return_1m"] == pytest.approx(
        returns.loc[first_source_index + 1, "market_excess"]
    )
    assert panel.loc[:, PUBLIC_FEATURE_COLUMNS].notna().all().all()


def test_fixed_calendar_split_and_generic_feature_experiment():
    dates = pd.date_range("2000-01-31", "2020-12-31", freq="ME")
    panel = pd.DataFrame({"date": dates, "ticker": "MARKET"})
    base = np.sin(np.arange(len(dates)) / 7.0) * 0.01
    for index, column in enumerate(PUBLIC_FEATURE_COLUMNS):
        panel[column] = base + index * 0.0001
    panel["target_return_1m"] = np.roll(base, -1)
    panel = panel.iloc[:-1].copy()
    split = calendar_split(panel, train_end="2008-12-31", validation_end="2014-12-31")
    assert split.train["date"].max() <= pd.Timestamp("2008-12-31")
    assert split.validation["date"].min() > pd.Timestamp("2008-12-31")
    assert split.test["date"].min() > pd.Timestamp("2014-12-31")
    metrics, predictions = run_experiment(
        panel,
        feature_columns=PUBLIC_FEATURE_COLUMNS,
        persistence_column="market_excess",
        split=split,
    )
    assert set(metrics["model"]) == {"persistence", "ridge"}
    assert len(predictions) == len(split.test)

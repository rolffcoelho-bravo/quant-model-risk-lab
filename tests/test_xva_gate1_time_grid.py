from __future__ import annotations

from datetime import date

import pytest

from qmrl.xva import (
    TimeGridSpec,
    adjust_business_day,
    build_time_grid,
)


def test_weekend_adjustment_is_explicit() -> None:
    saturday = date(2026, 1, 3)

    assert adjust_business_day(
        saturday,
        "following",
    ) == date(2026, 1, 5)

    assert adjust_business_day(
        saturday,
        "preceding",
    ) == date(2026, 1, 2)


def test_time_grid_is_sorted_unique_and_contains_maturity() -> None:
    spec = TimeGridSpec(
        valuation_date=date(2026, 1, 2),
        maturity_date=date(2026, 2, 2),
        exposure_interval_days=7,
        margin_call_interval_days=2,
        settlement_lag_days=2,
        margin_period_of_risk_days=5,
    )

    grid = build_time_grid(spec)
    dates = [point.date for point in grid]

    assert dates == sorted(set(dates))
    assert grid[0].year_fraction == 0.0
    assert grid[-1].is_maturity_date
    assert any(
        point.is_settlement_date
        for point in grid
    )
    assert any(
        point.is_mpor_end_date
        for point in grid
    )


def test_time_grid_rejects_invalid_horizon() -> None:
    with pytest.raises(ValueError):
        TimeGridSpec(
            valuation_date=date(2026, 1, 2),
            maturity_date=date(2026, 1, 2),
        )

from __future__ import annotations

import math

import numpy as np
import pytest

from qmrl.xva import (
    FXForwardTrade,
    RandomControl,
    RiskFactorSet,
    RiskFactorSpec,
    ZeroCouponBondTrade,
    generate_scenario_cube,
    value_fx_forward,
    value_portfolio,
)


def _cube():
    factor_set = RiskFactorSet(
        factors=(
            RiskFactorSpec(
                name="SPOT",
                factor_type="fx_spot",
                model="deterministic",
                initial_value=1.2,
                drift=0.1,
            ),
            RiskFactorSpec(
                name="RD",
                factor_type="short_rate",
                model="deterministic",
                initial_value=0.04,
            ),
            RiskFactorSpec(
                name="RF",
                factor_type="short_rate",
                model="deterministic",
                initial_value=0.02,
            ),
        ),
        correlation=np.eye(3),
    )

    return generate_scenario_cube(
        factor_set,
        np.array(
            [0.0, 0.5, 1.0]
        ),
        num_paths=2,
        random_control=RandomControl(
            seed=19,
            antithetic=True,
        ),
    )


def _forward() -> FXForwardTrade:
    return FXForwardTrade(
        trade_id="FWD1",
        notional_foreign=100.0,
        strike=1.25,
        maturity_time=1.0,
        spot_factor="SPOT",
        domestic_rate_factor="RD",
        foreign_rate_factor="RF",
    )


def test_fx_forward_matches_discounted_cashflow_formula() -> None:
    values = value_fx_forward(
        _cube(),
        _forward(),
    )

    expected_at_zero = 100.0 * (
        1.2 * math.exp(-0.02)
        - 1.25 * math.exp(-0.04)
    )

    assert values[0, 0] == pytest.approx(
        expected_at_zero
    )
    assert values[0, -1] == pytest.approx(
        5.0
    )


def test_portfolio_cube_aggregates_trade_values() -> None:
    cube = _cube()

    bond = ZeroCouponBondTrade(
        trade_id="ZCB1",
        notional=1000.0,
        maturity_time=1.0,
        rate_factor="RD",
    )

    future_values = value_portfolio(
        cube,
        [
            _forward(),
            bond,
        ],
    )

    assert future_values.values.shape == (
        2,
        3,
        2,
    )

    assert np.allclose(
        future_values.portfolio_values,
        np.sum(
            future_values.values,
            axis=2,
        ),
    )


def test_duplicate_trade_ids_are_rejected() -> None:
    cube = _cube()
    first = _forward()
    second = FXForwardTrade(
        trade_id="FWD1",
        notional_foreign=1.0,
        strike=1.0,
        maturity_time=1.0,
        spot_factor="SPOT",
        domestic_rate_factor="RD",
        foreign_rate_factor="RF",
    )

    with pytest.raises(ValueError):
        value_portfolio(
            cube,
            [first, second],
        )


def test_trade_maturity_cannot_exceed_scenario_horizon() -> None:
    trade = FXForwardTrade(
        trade_id="LONG",
        notional_foreign=1.0,
        strike=1.0,
        maturity_time=2.0,
        spot_factor="SPOT",
        domestic_rate_factor="RD",
        foreign_rate_factor="RF",
    )

    with pytest.raises(ValueError):
        value_fx_forward(
            _cube(),
            trade,
        )

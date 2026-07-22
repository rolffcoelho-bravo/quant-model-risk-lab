"""Tests for the independent FX-option challenger controls."""

from __future__ import annotations

from qmrl.fx_option_challenger import (
    black76_fx_price,
    finite_difference_greeks,
    relative_error,
)
from qmrl.fx_options import (
    garman_kohlhagen_price,
)


INPUTS = {
    "spot_rate": 5.0,
    "strike_rate": 5.55,
    "domestic_rate": 0.15,
    "foreign_rate": 0.04,
    "volatility": 0.16,
    "maturity_years": 1.0,
    "notional_foreign": 1_000_000.0,
}


def gk_premium(**kwargs: float | str) -> float:
    return garman_kohlhagen_price(
        **kwargs
    ).premium_domestic


def test_gk_matches_black76_forward_form() -> None:
    for option_type in ("call", "put"):
        gk = garman_kohlhagen_price(
            option_type=option_type,
            **INPUTS,
        )

        challenger = black76_fx_price(
            option_type=option_type,
            **INPUTS,
        )

        assert relative_error(
            gk.premium_domestic,
            challenger,
        ) < 1.0e-10


def test_analytic_greeks_match_finite_differences() -> None:
    for option_type in ("call", "put"):
        analytic = garman_kohlhagen_price(
            option_type=option_type,
            **INPUTS,
        )

        numerical = finite_difference_greeks(
            gk_premium,
            option_type=option_type,
            **INPUTS,
        )

        assert relative_error(
            analytic.delta,
            numerical.delta,
        ) < 5.0e-5

        assert relative_error(
            analytic.gamma,
            numerical.gamma,
        ) < 5.0e-4

        assert relative_error(
            analytic.vega,
            numerical.vega,
        ) < 5.0e-4
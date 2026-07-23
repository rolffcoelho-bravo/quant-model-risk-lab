import math

import pytest

from qmrl.multicurrency import (
    CollateralProfile,
    CurrencyCurveSet,
    TermCurve,
    accrue_collateral,
    convert_collateral_profile,
    switch_collateral_currency,
)
from v1_4_gate2_helpers import TIMES, fx_market


def test_discount_curve_interpolates_linearly():
    curve = TermCurve("D", "USD", "discount", (0, 2), (1.0, 0.8))
    assert curve.value(1.0) == pytest.approx(0.9)


def test_flat_curve_extrapolation():
    curve = TermCurve("D", "USD", "discount", (0, 1), (1.0, 0.9))
    assert curve.value(2.0) == pytest.approx(0.9)


def test_forbidden_curve_extrapolation():
    curve = TermCurve(
        "D", "USD", "discount", (0, 1), (1.0, 0.9), "forbidden"
    )
    with pytest.raises(ValueError):
        curve.value(2.0)


def test_duplicate_currency_curve_is_blocked():
    curve = TermCurve("D", "USD", "discount", (0, 1), (1.0, 0.9))
    with pytest.raises(ValueError):
        CurrencyCurveSet((curve, curve))


def test_zero_rate_collateral_does_not_grow():
    assert accrue_collateral(100.0, TIMES, (0.0, 0.0)) == (100.0, 100.0)


def test_positive_rate_collateral_grows():
    result = accrue_collateral(100.0, TIMES, (0.05, 0.05))
    assert result[-1] == pytest.approx(100.0 * math.exp(0.05))


def test_collateral_conversion_uses_pathwise_fx():
    profile = CollateralProfile(
        "CS", "EUR", TIMES, ((10.0, 10.0), (20.0, 20.0))
    )
    converted = convert_collateral_profile(profile, "USD", fx_market())
    assert converted.balances[0] == pytest.approx((11.0, 12.0))
    assert converted.balances[1] == pytest.approx((22.0, 24.0))


def test_currency_switch_preserves_reporting_value():
    market = fx_market()
    profile = CollateralProfile(
        "CS", "GBP", TIMES, ((10.0, 10.0), (10.0, 10.0))
    )
    eur = switch_collateral_currency(profile, "EUR", market)
    usd_from_gbp = convert_collateral_profile(profile, "USD", market)
    usd_from_eur = convert_collateral_profile(eur, "USD", market)
    for observed, expected in zip(usd_from_gbp.balances, usd_from_eur.balances):
        assert observed == pytest.approx(expected)

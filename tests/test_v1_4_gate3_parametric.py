import math
from statistics import NormalDist

import pytest

from qmrl.margin import MarginPolicy, ParametricMarginInput, calculate_parametric_initial_margin


def risk_input(**overrides):
    values = {
        "netting_set_id": "NS-P",
        "currency": "USD",
        "times": (0.0, 1.0),
        "sensitivities": ((3.0, 4.0), (0.0, 0.0)),
        "covariance": ((1.0, 0.0), (0.0, 1.0)),
        "posted_multiplier": 1.0,
        "received_multiplier": 0.5,
        "volatility_scale": 1.0,
    }
    values.update(overrides)
    return ParametricMarginInput(**values)


def policy(**overrides):
    values = {
        "method": "parametric",
        "confidence_level": 0.99,
        "margin_period_days": 10,
        "base_margin_days": 10,
    }
    values.update(overrides)
    return MarginPolicy(**values)


def test_parametric_margin_matches_analytic_sigma():
    profile = calculate_parametric_initial_margin(risk_input(), policy())
    expected = NormalDist().inv_cdf(0.99) * 5.0
    assert math.isclose(profile.posted_margin[0], expected, rel_tol=1e-12)


def test_parametric_received_multiplier_is_applied():
    profile = calculate_parametric_initial_margin(risk_input(), policy())
    assert math.isclose(profile.received_margin[0], profile.posted_margin[0] * 0.5)


def test_longer_mpor_increases_parametric_margin():
    short = calculate_parametric_initial_margin(risk_input(), policy(margin_period_days=10))
    long = calculate_parametric_initial_margin(risk_input(), policy(margin_period_days=40))
    assert math.isclose(long.posted_margin[0], short.posted_margin[0] * 2.0)


def test_higher_volatility_scale_increases_margin_linearly():
    base = calculate_parametric_initial_margin(risk_input(), policy())
    stressed = calculate_parametric_initial_margin(
        risk_input(volatility_scale=1.5), policy()
    )
    assert math.isclose(stressed.posted_margin[0], base.posted_margin[0] * 1.5)


def test_parametric_addon_is_visible():
    base = calculate_parametric_initial_margin(risk_input(), policy())
    addon = calculate_parametric_initial_margin(risk_input(), policy(addon_rate=0.1))
    assert addon.posted_margin[0] > base.posted_margin[0]


def test_negative_portfolio_variance_is_blocked():
    bad = risk_input(covariance=((1.0, -2.0), (-2.0, 1.0)))
    with pytest.raises(ValueError):
        calculate_parametric_initial_margin(bad, policy())


def test_zero_sensitivity_produces_zero_margin_without_minimum():
    profile = calculate_parametric_initial_margin(
        risk_input(sensitivities=((0.0, 0.0), (0.0, 0.0))), policy()
    )
    assert profile.posted_margin == (0.0, 0.0)

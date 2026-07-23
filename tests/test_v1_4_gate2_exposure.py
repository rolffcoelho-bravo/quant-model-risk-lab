from dataclasses import replace

import pytest

from qmrl.multicurrency import (
    CollateralProfile,
    PathwiseSeries,
    calculate_multicurrency_exposure,
)
from v1_4_gate2_helpers import (
    TIMES,
    collateral,
    curves,
    fx_market,
    policy,
    reference_snapshot,
    trade_values,
)


def calculate(values=None, collateral_profiles=None, **kwargs):
    return calculate_multicurrency_exposure(
        reference_snapshot(),
        values or trade_values(),
        collateral_profiles if collateral_profiles is not None else {},
        fx_market(),
        curves(),
        policy(),
        **kwargs,
    )[0]


def test_single_currency_reproduces_direct_netting_result():
    values = trade_values(
        usd=((100.0, 80.0), (20.0, 10.0)),
        eur=((0.0, 0.0), (0.0, 0.0)),
    )
    result = calculate(values)
    assert result.expected_positive_exposure == pytest.approx((60.0, 45.0))


def test_currency_conversion_occurs_before_netting():
    result = calculate()
    assert result.net_values[0] == pytest.approx((111.0, 104.0))
    assert result.net_values[1] == pytest.approx((-9.0, -14.0))


def test_collateral_reduces_positive_exposure():
    uncollateralized = calculate()
    collateralized = calculate(collateral_profiles=collateral())
    assert collateralized.expected_positive_exposure[0] < (
        uncollateralized.expected_positive_exposure[0]
    )


def test_negative_exposure_is_positive_magnitude():
    result = calculate()
    assert result.expected_negative_exposure == pytest.approx((4.5, 7.0))


def test_reporting_discount_curve_is_applied():
    result = calculate()
    assert result.discounted_expected_positive_exposure[1] == pytest.approx(
        result.expected_positive_exposure[1] * 0.95
    )


def test_incomplete_trade_mapping_is_blocked():
    values = trade_values()
    values.pop("T-EUR")
    with pytest.raises(ValueError, match="incomplete"):
        calculate(values)


def test_trade_value_currency_mismatch_is_blocked():
    values = trade_values()
    values["T-EUR"] = PathwiseSeries(
        "GBP", TIMES, ((1.0, 1.0), (1.0, 1.0))
    )
    with pytest.raises(ValueError, match="does not match"):
        calculate(values)


def test_ineligible_collateral_currency_is_blocked():
    snapshot = reference_snapshot()
    blocked_set = replace(
        snapshot.collateral_sets[0],
        eligible_currencies=("USD",),
    )
    snapshot = replace(snapshot, collateral_sets=(blocked_set,))
    with pytest.raises(ValueError, match="not eligible"):
        calculate_multicurrency_exposure(
            snapshot,
            trade_values(),
            collateral(currency="EUR"),
            fx_market(),
            curves(),
            policy(),
        )


def test_collateral_remuneration_changes_exposure():
    profile = collateral(
        balances=((20.0, 20.0), (20.0, 20.0)),
        rates=(0.05, 0.05),
    )
    plain = calculate(collateral_profiles=profile)
    remunerated = calculate(
        collateral_profiles=profile,
        apply_collateral_remuneration=True,
    )
    assert remunerated.expected_positive_exposure[1] < (
        plain.expected_positive_exposure[1]
    )


def test_policy_hash_is_deterministic():
    first = calculate().policy_hash
    second = calculate().policy_hash
    assert first == second
    assert len(first) == 64

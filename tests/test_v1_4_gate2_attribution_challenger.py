from dataclasses import replace

import pytest

from qmrl.multicurrency import (
    aggregate_expected_profiles,
    build_currency_attribution,
    calculate_multicurrency_exposure,
    challenge_multicurrency_exposure,
    collateral_switch_impact,
)
from v1_4_gate2_helpers import (
    collateral,
    curves,
    fx_market,
    policy,
    reference_snapshot,
    trade_values,
)


def result(collateral_profiles=None):
    return calculate_multicurrency_exposure(
        reference_snapshot(),
        trade_values(),
        collateral_profiles or {},
        fx_market(),
        curves(),
        policy(),
    )[0]


def test_currency_attribution_reconciles():
    report = build_currency_attribution(result())
    assert report.reconciled
    assert report.maximum_absolute_residual <= report.tolerance


def test_currency_attribution_detects_residual():
    base = result()
    broken = replace(
        base,
        currency_contributions={
            "USD": (0.0, 0.0),
            "EUR": (0.0, 0.0),
        },
    )
    assert not build_currency_attribution(broken).reconciled


def test_portfolio_profile_aggregation():
    base = result()
    aggregated = aggregate_expected_profiles((base, base))
    assert aggregated["expected_positive_exposure"] == pytest.approx(
        tuple(2.0 * value for value in base.expected_positive_exposure)
    )


def test_independent_challenger_passes():
    snapshot = reference_snapshot()
    values = trade_values()
    profiles = collateral()
    engine = calculate_multicurrency_exposure(
        snapshot, values, profiles, fx_market(), curves(), policy()
    )
    report = challenge_multicurrency_exposure(
        snapshot,
        values,
        profiles,
        fx_market(),
        curves(),
        policy(),
        engine,
    )
    assert report.passed


def test_independent_challenger_detects_tampering():
    snapshot = reference_snapshot()
    values = trade_values()
    engine = calculate_multicurrency_exposure(
        snapshot, values, {}, fx_market(), curves(), policy()
    )
    tampered = (
        replace(
            engine[0],
            expected_positive_exposure=(
                engine[0].expected_positive_exposure[0] + 1.0,
                engine[0].expected_positive_exposure[1],
            ),
        ),
    )
    report = challenge_multicurrency_exposure(
        snapshot,
        values,
        {},
        fx_market(),
        curves(),
        policy(),
        tampered,
    )
    assert not report.passed


def test_collateral_switch_impact_is_zero_for_equivalent_value():
    base = result(collateral("USD"))
    same = result(collateral("USD"))
    impact = collateral_switch_impact(base, same)
    assert impact.maximum_absolute_change == pytest.approx(0.0)


def test_collateral_switch_impact_requires_alignment():
    base = result()
    with pytest.raises(ValueError):
        collateral_switch_impact(
            base,
            replace(base, netting_set_id="OTHER"),
        )

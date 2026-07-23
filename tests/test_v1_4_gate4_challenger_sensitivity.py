from __future__ import annotations

from dataclasses import replace

from qmrl.capital import (
    build_capital_profile,
    calculate_kva,
    challenger_kva,
    reconcile_challenger,
    standard_capital_sensitivities,
)
from v1_4_gate4_helpers import sample_hurdle, sample_input, sample_market, sample_policy


def test_independent_challenger_reconciles() -> None:
    profile = build_capital_profile(sample_input(), sample_policy())
    implementation = calculate_kva(profile, sample_market(), sample_hurdle())
    challenge = challenger_kva(profile, sample_market(), sample_hurdle())
    assert reconcile_challenger(implementation, challenge).status == "PASS"


def test_challenger_blocks_material_difference() -> None:
    profile = build_capital_profile(sample_input(), sample_policy())
    implementation = calculate_kva(profile, sample_market(), sample_hurdle())
    assert reconcile_challenger(implementation, implementation.total_kva + 1.0).status == "BLOCK"


def test_standard_sensitivity_inventory_is_complete() -> None:
    results = standard_capital_sensitivities(sample_input(), sample_policy(), sample_market(), sample_hurdle())
    assert len(results) == 7


def test_hurdle_sensitivity_is_positive() -> None:
    results = {item.scenario: item for item in standard_capital_sensitivities(sample_input(), sample_policy(), sample_market(), sample_hurdle())}
    assert results["hurdle_plus_100bp"].delta > 0.0


def test_ead_sensitivity_is_positive() -> None:
    results = {item.scenario: item for item in standard_capital_sensitivities(sample_input(), sample_policy(), sample_market(), sample_hurdle())}
    assert results["ead_plus_10pct"].delta > 0.0


def test_discount_rate_sensitivity_is_negative() -> None:
    results = {item.scenario: item for item in standard_capital_sensitivities(sample_input(), sample_policy(), sample_market(), sample_hurdle())}
    assert results["discount_rate_plus_100bp"].delta < 0.0


def test_stress_multiplier_increases_kva() -> None:
    base = calculate_kva(build_capital_profile(sample_input(), sample_policy()), sample_market(), sample_hurdle())
    stressed = calculate_kva(build_capital_profile(sample_input(), replace(sample_policy(), stress_multiplier=1.5)), sample_market(), sample_hurdle())
    assert stressed.total_kva > base.total_kva

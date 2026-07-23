from __future__ import annotations

from dataclasses import replace

import numpy as np

from qmrl.capital import IntegrationRule, SurvivalMode, build_capital_profile, calculate_kva
from v1_4_gate4_helpers import sample_hurdle, sample_input, sample_market, sample_policy


def test_zero_hurdle_rate_implies_zero_kva() -> None:
    result = calculate_kva(build_capital_profile(sample_input(), sample_policy()), sample_market(), sample_hurdle(0.0))
    assert result.total_kva == 0.0


def test_positive_capital_and_hurdle_produce_positive_kva() -> None:
    result = calculate_kva(build_capital_profile(sample_input(), sample_policy()), sample_market(), sample_hurdle())
    assert result.total_kva > 0.0


def test_netting_set_kva_reconciles_to_total() -> None:
    result = calculate_kva(build_capital_profile(sample_input(), sample_policy()), sample_market(), sample_hurdle())
    assert np.isclose(result.netting_set_kva.sum(), result.total_kva)


def test_interval_contributions_reconcile_to_total() -> None:
    result = calculate_kva(build_capital_profile(sample_input(), sample_policy()), sample_market(), sample_hurdle())
    assert np.isclose(result.interval_contributions.sum(), result.total_kva)


def test_endpoint_and_trapezoid_are_distinct() -> None:
    endpoint = calculate_kva(build_capital_profile(sample_input(), sample_policy(integration_rule=IntegrationRule.ENDPOINT)), sample_market(), sample_hurdle())
    trapezoid = calculate_kva(build_capital_profile(sample_input(), sample_policy(integration_rule=IntegrationRule.TRAPEZOID)), sample_market(), sample_hurdle())
    assert not np.isclose(endpoint.total_kva, trapezoid.total_kva)


def test_survival_weighting_reduces_kva() -> None:
    with_survival = calculate_kva(build_capital_profile(sample_input(), sample_policy()), sample_market(), sample_hurdle())
    no_survival = calculate_kva(build_capital_profile(sample_input(), sample_policy(survival_mode=SurvivalMode.NONE)), sample_market(), sample_hurdle())
    assert with_survival.total_kva < no_survival.total_kva


def test_higher_hurdle_rate_increases_kva() -> None:
    profile = build_capital_profile(sample_input(), sample_policy())
    low = calculate_kva(profile, sample_market(), sample_hurdle(500.0))
    high = calculate_kva(profile, sample_market(), sample_hurdle(1500.0))
    assert high.total_kva > low.total_kva

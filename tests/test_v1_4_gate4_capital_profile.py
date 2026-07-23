from __future__ import annotations

from dataclasses import replace

import numpy as np

from qmrl.capital import build_capital_profile
from v1_4_gate4_helpers import sample_input, sample_policy


def test_ead_profile_applies_multiplier() -> None:
    result = build_capital_profile(sample_input(), sample_policy())
    assert np.allclose(result.ead_profiles, sample_input().expected_exposure * 1.4)


def test_risk_weight_override_is_applied_per_set() -> None:
    result = build_capital_profile(sample_input(), sample_policy(risk_weight=0.1))
    assert np.allclose(result.effective_risk_weights, np.array([0.50, 0.75]))


def test_zero_exposure_produces_zero_capital() -> None:
    source = sample_input()
    zero = replace(source, expected_exposure=np.zeros_like(source.expected_exposure))
    result = build_capital_profile(zero, sample_policy())
    assert np.all(result.capital_profiles == 0.0)


def test_stress_multiplier_is_linear() -> None:
    base = build_capital_profile(sample_input(), sample_policy(stress_multiplier=1.0))
    stressed = build_capital_profile(sample_input(), sample_policy(stress_multiplier=1.5))
    assert np.allclose(stressed.capital_profiles, base.capital_profiles * 1.5)


def test_maturity_multiplier_is_linear() -> None:
    base = build_capital_profile(sample_input(), sample_policy(maturity_multiplier=1.0))
    longer = build_capital_profile(sample_input(), sample_policy(maturity_multiplier=1.2))
    assert np.allclose(longer.capital_profiles, base.capital_profiles * 1.2)


def test_peak_capital_matches_aggregate_profile() -> None:
    result = build_capital_profile(sample_input(), sample_policy())
    assert np.isclose(result.peak_capital, result.aggregate_capital_profile.max())


def test_aggregate_profile_reconciles_to_sets() -> None:
    result = build_capital_profile(sample_input(), sample_policy())
    assert np.allclose(result.aggregate_capital_profile, result.capital_profiles.sum(axis=0))

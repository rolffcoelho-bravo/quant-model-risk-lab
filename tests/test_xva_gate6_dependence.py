from __future__ import annotations

from datetime import date
import numpy as np
import pytest

from qmrl.xva.wrong_way_risk import (
    WWRDependenceSpec,
    gaussian_copula_conditional_cumulative_pd,
    gaussian_copula_default_uniforms,
    normal_ppf,
)


def test_normal_ppf_inverts_standard_normal_cdf_at_center() -> None:
    assert normal_ppf(0.5) == pytest.approx(0.0, abs=1e-12)


def test_zero_correlation_preserves_unconditional_pd() -> None:
    probabilities = np.array([0.05, 0.10, 0.20])
    scores = np.array([-2.0, 0.0, 2.0])
    conditional = gaussian_copula_conditional_cumulative_pd(
        probabilities,
        scores,
        correlation=0.0,
    )
    assert np.allclose(conditional, probabilities[None, :])


def test_positive_correlation_increases_pd_for_high_exposure_score() -> None:
    conditional = gaussian_copula_conditional_cumulative_pd(
        [0.10],
        [-2.0, 2.0],
        correlation=0.60,
    )
    assert conditional[1, 0] > conditional[0, 0]


def test_default_uniforms_move_toward_default_for_high_exposure() -> None:
    uniforms = gaussian_copula_default_uniforms(
        [-2.0, 2.0],
        [0.0, 0.0],
        correlation=0.75,
    )
    assert uniforms[1] < uniforms[0]


def test_independent_classification_rejects_nonzero_correlation() -> None:
    with pytest.raises(ValueError):
        WWRDependenceSpec(
            dependence_id="D1",
            netting_set_id="NS1",
            counterparty_id="CP1",
            market_factor_id="FX",
            classification="independent",
            channel="fx",
            correlation=0.1,
            as_of_date=date(2026, 1, 2),
            calibration_source="TEST",
            rationale="Expected rejection.",
        )

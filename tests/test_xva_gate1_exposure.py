from __future__ import annotations

import numpy as np
import pytest

from qmrl.xva import (
    collateralized_exposure,
    exposure_statistics,
    margin_period_of_risk_exposure,
)


def test_collateralized_exposure_separates_positive_and_negative() -> None:
    profile = collateralized_exposure(
        [100.0, -80.0],
        [20.0, -30.0],
    )

    assert profile.net_values.tolist() == [
        80.0,
        -50.0,
    ]
    assert profile.positive_exposure.tolist() == [
        80.0,
        0.0,
    ]
    assert profile.negative_exposure.tolist() == [
        0.0,
        50.0,
    ]


def test_mpor_uses_future_clean_value_against_current_collateral() -> None:
    profile = margin_period_of_risk_exposure(
        [0.0, 50.0, 100.0],
        [0.0, 50.0, 100.0],
        mpor_steps=1,
    )

    assert profile.positive_exposure.tolist() == [
        50.0,
        50.0,
        0.0,
    ]


def test_exposure_statistics_produce_epe_ene_and_pfe_profiles() -> None:
    clean_paths = np.array(
        [
            [0.0, 100.0, -20.0],
            [0.0, 50.0, -40.0],
        ]
    )

    statistics = exposure_statistics(
        clean_paths,
        quantile=0.95,
        times=[0.0, 0.5, 1.0],
        discount_factors=[1.0, 0.98, 0.95],
    )

    assert statistics.expected_positive_profile.tolist() == [
        0.0,
        75.0,
        0.0,
    ]

    assert statistics.expected_negative_profile.tolist() == [
        0.0,
        0.0,
        30.0,
    ]

    assert statistics.peak_pfe >= 75.0
    assert statistics.epe > 0.0
    assert statistics.ene > 0.0
    assert statistics.discounted_epe <= statistics.epe


def test_exposure_statistics_reject_invalid_quantile() -> None:
    with pytest.raises(ValueError):
        exposure_statistics(
            [1.0, 2.0],
            quantile=1.0,
        )

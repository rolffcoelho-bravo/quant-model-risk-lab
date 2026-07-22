"""Tests for governed FX-option volatility estimation and floors."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from scripts.run_fx_options_validation import (
    load_governed_usd_brl_levels,
)

from qmrl.fx_option_governance import (
    apply_volatility_floor,
    estimate_realised_volatility,
    load_fx_option_governance_contract,
)


def test_short_history_uses_documented_fallback() -> None:
    contract = load_fx_option_governance_contract()

    levels = [
        5.0 + index * 0.001
        for index in range(10)
    ]

    estimate = estimate_realised_volatility(
        levels,
        contract.volatility_estimation,
    )

    assert estimate.volatility == 0.15

    assert (
        estimate.estimation_status
        == "FALLBACK_INSUFFICIENT_OBSERVATIONS"
    )

    assert estimate.raw_volatility is None


def test_constant_series_activates_lower_bound() -> None:
    contract = load_fx_option_governance_contract()

    estimate = estimate_realised_volatility(
        [5.0] * 80,
        contract.volatility_estimation,
    )

    assert estimate.volatility == 0.05
    assert estimate.lower_bound_applied
    assert not estimate.upper_bound_applied


def test_extreme_series_activates_upper_bound() -> None:
    contract = load_fx_option_governance_contract()

    levels = [
        5.0 if index % 2 == 0 else 10.0
        for index in range(90)
    ]

    estimate = estimate_realised_volatility(
        levels,
        contract.volatility_estimation,
    )

    assert estimate.volatility == 0.60
    assert estimate.upper_bound_applied


def test_surface_floor_is_governed() -> None:
    assert apply_volatility_floor(-0.20) == 0.01
    assert apply_volatility_floor(0.005) == 0.01
    assert apply_volatility_floor(0.20) == 0.20


def test_surface_floor_rejects_non_finite_values() -> None:
    with pytest.raises(
        ValueError,
        match="finite",
    ):
        apply_volatility_floor(math.nan)

    with pytest.raises(
        ValueError,
        match="finite",
    ):
        apply_volatility_floor(np.inf)


def test_governed_bcb_spot_history_is_resolved() -> None:
    levels = load_governed_usd_brl_levels(
        pd.DataFrame(),
        "BCB_SGS_1",
    )

    assert len(levels) >= 20
    assert levels.notna().all()
    assert (levels > 0.0).all()


def test_unknown_source_identity_fails_closed() -> None:
    with pytest.raises(
        KeyError,
        match="not the governed BCB",
    ):
        load_governed_usd_brl_levels(
            pd.DataFrame(),
            "UNKNOWN_FX_SOURCE",
        )

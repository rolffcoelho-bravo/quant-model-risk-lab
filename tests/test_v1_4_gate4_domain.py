from __future__ import annotations

import numpy as np
import pytest

from qmrl.capital import CAPITAL_BOUNDARY, BpsCurve, CapitalExposureInput, CapitalMarketState, CapitalPolicy
from v1_4_gate4_helpers import sample_input


def test_capital_boundary_is_explicit() -> None:
    assert CAPITAL_BOUNDARY == "PUBLIC_CAPITAL_PROXY_NOT_REGULATORY_APPROVAL"


def test_policy_rejects_negative_parameter() -> None:
    with pytest.raises(ValueError):
        CapitalPolicy(risk_weight=-0.1)


def test_policy_rejects_boundary_override() -> None:
    with pytest.raises(ValueError):
        CapitalPolicy(boundary="REGULATORY_APPROVED")


def test_exposure_input_requires_zero_time_origin() -> None:
    base = sample_input()
    with pytest.raises(ValueError):
        CapitalExposureInput(
            times=np.array([0.5, 1.0]),
            expected_exposure=np.zeros((2, 2)),
            counterparty_ids=base.counterparty_ids,
            netting_set_ids=base.netting_set_ids,
            currencies=base.currencies,
        )


def test_trade_weights_must_reconcile_within_netting_set() -> None:
    with pytest.raises(ValueError):
        CapitalExposureInput(
            times=np.array([0.0, 1.0]),
            expected_exposure=np.zeros((1, 2)),
            counterparty_ids=("CP",),
            netting_set_ids=("NS",),
            currencies=("USD",),
            trade_ids=("T1", "T2"),
            trade_netting_set_indices=(0, 0),
            trade_weights=np.array([0.7, 0.2]),
        )


def test_market_state_rejects_increasing_discount_factor() -> None:
    with pytest.raises(ValueError):
        CapitalMarketState(np.array([0.0, 1.0]), np.array([1.0, 1.01]), np.array([1.0, 0.9]))


def test_bps_curve_supports_interpolation_and_shift() -> None:
    curve = BpsCurve(np.array([0.0, 2.0]), np.array([100.0, 300.0]))
    assert np.isclose(curve.values(np.array([1.0]))[0], 200.0)
    assert np.isclose(curve.shifted(50.0).rates_bps[0], 150.0)

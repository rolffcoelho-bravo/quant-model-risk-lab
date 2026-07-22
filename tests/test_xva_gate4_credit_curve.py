from __future__ import annotations

from datetime import date
import math

import numpy as np
import pytest

from qmrl.xva import (
    CreditCurve,
    build_flat_credit_curve,
    flat_hazard_from_spread,
)


AS_OF = date(2026, 1, 2)


def test_flat_hazard_matches_spread_over_lgd() -> None:
    assert flat_hazard_from_spread(120.0, 0.40) == pytest.approx(0.02)


def test_flat_curve_matches_analytic_survival() -> None:
    curve = build_flat_credit_curve(
        curve_id="CP1-FLAT",
        obligor_id="CP1",
        role="counterparty",
        probability_measure="risk_neutral",
        currency="USD",
        as_of_date=AS_OF,
        recovery_rate=0.40,
        spread_bps=120.0,
        node_times=[1.0, 3.0, 5.0],
    )

    assert curve.survival_probability(5.0) == pytest.approx(math.exp(-0.10))
    assert curve.cumulative_default_probability(5.0) == pytest.approx(
        1.0 - math.exp(-0.10)
    )


def test_marginal_probabilities_reconcile_to_terminal_pd() -> None:
    curve = build_flat_credit_curve(
        curve_id="CP1-PD",
        obligor_id="CP1",
        role="counterparty",
        probability_measure="risk_neutral",
        currency="USD",
        as_of_date=AS_OF,
        recovery_rate=0.40,
        spread_bps=100.0,
        node_times=[1.0, 2.0, 3.0, 5.0],
    )

    marginal = curve.marginal_default_probabilities()

    assert np.all(marginal >= 0.0)
    assert np.sum(marginal) == pytest.approx(
        curve.cumulative_default_probability(5.0)
    )


def test_forbidden_extrapolation_fails_closed() -> None:
    curve = build_flat_credit_curve(
        curve_id="CP1-NO-EXTRAP",
        obligor_id="CP1",
        role="counterparty",
        probability_measure="risk_neutral",
        currency="USD",
        as_of_date=AS_OF,
        recovery_rate=0.40,
        spread_bps=100.0,
        node_times=[1.0, 3.0],
        extrapolation_mode="forbidden",
    )

    with pytest.raises(ValueError):
        curve.survival_probability(5.0)


def test_curve_rejects_negative_hazard() -> None:
    with pytest.raises(ValueError):
        CreditCurve(
            curve_id="INVALID",
            obligor_id="CP1",
            role="counterparty",
            probability_measure="risk_neutral",
            currency="USD",
            as_of_date=AS_OF,
            recovery_rate=0.40,
            node_times=np.array([1.0, 3.0]),
            hazard_rates=np.array([0.01, -0.01]),
            source_quote_spreads_bps=np.array([60.0, 80.0]),
            source_quote_types=("cds", "cds"),
        )

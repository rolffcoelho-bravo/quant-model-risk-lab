from __future__ import annotations

from datetime import date
import numpy as np
import pytest

from qmrl.xva.credit_curve import CreditCurve
from qmrl.xva.xva_integration import DiscountCurve, FundingCurve, XVAExposureInput
from qmrl.xva.xva_stress import XVAStressScenario, evaluate_xva_stress


def _inputs():
    times = np.array([0.0, 0.5, 1.0, 2.0])
    exposure = XVAExposureInput(
        times=times,
        netting_set_ids=("NS1",),
        counterparty_ids=("CP1",),
        expected_positive=np.array([[0.0], [40.0], [70.0], [100.0]]),
        expected_negative=np.array([[0.0], [10.0], [15.0], [20.0]]),
        mpor_expected_positive=np.array([[0.0], [45.0], [75.0], [110.0]]),
        mpor_expected_negative=np.array([[0.0], [10.0], [15.0], [20.0]]),
    )
    def curve(obligor, role, hazard):
        return CreditCurve(
            curve_id=obligor,
            obligor_id=obligor,
            role=role,
            probability_measure="risk_neutral",
            currency="USD",
            as_of_date=date(2026, 1, 2),
            recovery_rate=0.4,
            node_times=np.array([0.5, 1.0, 2.0]),
            hazard_rates=np.array([hazard, hazard, hazard]),
            source_quote_spreads_bps=np.array([600.0, 600.0, 600.0]),
            source_quote_types=("cds", "cds", "cds"),
        )
    discount = DiscountCurve(
        curve_id="USD",
        currency="USD",
        as_of_date=date(2026, 1, 2),
        times=times,
        discount_factors=np.exp(-0.03 * times),
    )
    funding = FundingCurve(
        curve_id="FUNDING",
        currency="USD",
        as_of_date=date(2026, 1, 2),
        times=times,
        borrowing_spreads_bps=np.array([80.0, 80.0, 90.0, 100.0]),
        lending_spreads_bps=np.array([20.0, 20.0, 25.0, 30.0]),
    )
    return exposure, {"CP1": curve("CP1", "counterparty", 0.10)}, curve("BANK", "own", 0.04), discount, funding


def _scenario(**overrides):
    values = dict(
        scenario_id="S1",
        channel="systemic",
        severity="moderate",
        as_of_date=date(2026, 1, 2),
        calibration_source="TEST",
        rationale="Stress unit test.",
        approved=True,
    )
    values.update(overrides)
    return XVAStressScenario(**values)


def test_hazard_stress_increases_cva() -> None:
    exposure, cp, own, discount, funding = _inputs()
    result = evaluate_xva_stress(
        exposure,
        counterparty_curves=cp,
        own_curve=own,
        discount_curve=discount,
        funding_curve=funding,
        scenario=_scenario(counterparty_hazard_multiplier=1.5),
    )
    assert result.cva_delta > 0.0


def test_exposure_stress_increases_cva_and_fca() -> None:
    exposure, cp, own, discount, funding = _inputs()
    result = evaluate_xva_stress(
        exposure,
        counterparty_curves=cp,
        own_curve=own,
        discount_curve=discount,
        funding_curve=funding,
        scenario=_scenario(exposure_multiplier=1.4),
    )
    assert result.cva_delta > 0.0
    assert result.fca_delta > 0.0


def test_funding_stress_increases_fca() -> None:
    exposure, cp, own, discount, funding = _inputs()
    result = evaluate_xva_stress(
        exposure,
        counterparty_curves=cp,
        own_curve=own,
        discount_curve=discount,
        funding_curve=funding,
        scenario=_scenario(borrowing_spread_bump_bps=50.0),
    )
    assert result.fca_delta > 0.0


def test_positive_discount_rate_stress_reduces_cva() -> None:
    exposure, cp, own, discount, funding = _inputs()
    result = evaluate_xva_stress(
        exposure,
        counterparty_curves=cp,
        own_curve=own,
        discount_curve=discount,
        funding_curve=funding,
        scenario=_scenario(discount_rate_bump_bps=100.0),
    )
    assert result.cva_delta < 0.0


def test_severe_unapproved_scenario_is_rejected() -> None:
    with pytest.raises(ValueError):
        _scenario(severity="severe", approved=False)

from __future__ import annotations

from datetime import date
import numpy as np
import pytest

from qmrl.xva.credit_curve import CreditCurve
from qmrl.xva.xva_integration import DiscountCurve, FundingCurve, XVAExposureInput
from qmrl.xva.xva_stress import XVAStressScenario, evaluate_xva_stress, stress_manifest


def _setup():
    times = np.array([0.0, 1.0, 2.0])
    exposure = XVAExposureInput(
        times=times,
        netting_set_ids=("NS1", "NS2"),
        counterparty_ids=("CP1", "CP2"),
        expected_positive=np.array([[0.0, 0.0], [50.0, 30.0], [80.0, 40.0]]),
        expected_negative=np.array([[0.0, 0.0], [10.0, 5.0], [15.0, 8.0]]),
        mpor_expected_positive=np.array([[0.0, 0.0], [55.0, 35.0], [90.0, 45.0]]),
        mpor_expected_negative=np.array([[0.0, 0.0], [10.0, 5.0], [15.0, 8.0]]),
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
            node_times=np.array([1.0, 2.0]),
            hazard_rates=np.array([hazard, hazard]),
            source_quote_spreads_bps=np.array([600.0, 600.0]),
            source_quote_types=("cds", "cds"),
        )
    cp = {"CP1": curve("CP1", "counterparty", 0.10), "CP2": curve("CP2", "counterparty", 0.15)}
    own = curve("BANK", "own", 0.04)
    discount = DiscountCurve(
        curve_id="USD",
        currency="USD",
        as_of_date=date(2026, 1, 2),
        times=times,
        discount_factors=np.exp(-0.03 * times),
    )
    funding = FundingCurve(
        curve_id="F",
        currency="USD",
        as_of_date=date(2026, 1, 2),
        times=times,
        borrowing_spreads_bps=np.array([80.0, 90.0, 100.0]),
        lending_spreads_bps=np.array([20.0, 25.0, 30.0]),
    )
    scenario = XVAStressScenario(
        scenario_id="ATTR",
        channel="sector",
        severity="moderate",
        as_of_date=date(2026, 1, 2),
        calibration_source="TEST",
        rationale="Attribution test.",
        exposure_multiplier=1.2,
        counterparty_hazard_multiplier=1.3,
        borrowing_spread_bump_bps=25.0,
        approved=True,
    )
    return exposure, cp, own, discount, funding, scenario


def test_netting_set_cva_deltas_reconcile() -> None:
    exposure, cp, own, discount, funding, scenario = _setup()
    result = evaluate_xva_stress(
        exposure,
        counterparty_curves=cp,
        own_curve=own,
        discount_curve=discount,
        funding_curve=funding,
        scenario=scenario,
    )
    assert float(np.sum(result.cva_delta_by_netting_set)) == pytest.approx(result.cva_delta)


def test_total_adjustment_delta_reconciles() -> None:
    exposure, cp, own, discount, funding, scenario = _setup()
    result = evaluate_xva_stress(
        exposure,
        counterparty_curves=cp,
        own_curve=own,
        discount_curve=discount,
        funding_curve=funding,
        scenario=scenario,
    )
    identity = -result.cva_delta + result.dva_delta - result.fca_delta + result.fba_delta
    assert result.total_adjustment_delta == pytest.approx(identity)


def test_stress_manifest_is_deterministic() -> None:
    exposure, cp, own, discount, funding, scenario = _setup()
    result = evaluate_xva_stress(
        exposure,
        counterparty_curves=cp,
        own_curve=own,
        discount_curve=discount,
        funding_curve=funding,
        scenario=scenario,
    )
    assert stress_manifest(result, scenario)["sha256"] == stress_manifest(result, scenario)["sha256"]

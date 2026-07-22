from datetime import date
import pytest

from qmrl.xva.wrong_way_risk import WWRDependenceSpec
from qmrl.xva.xva_stress import XVAStressScenario


def test_specific_wwr_requires_human_review() -> None:
    with pytest.raises(ValueError):
        WWRDependenceSpec(
            dependence_id="SWWR",
            netting_set_id="NS1",
            counterparty_id="CP1",
            market_factor_id="COMMODITY",
            classification="specific_wrong_way",
            channel="commodity",
            correlation=0.7,
            as_of_date=date(2026, 1, 2),
            calibration_source="TEST",
            rationale="Expected rejection.",
            human_review_required=False,
        )


def test_correlation_outside_governed_boundary_is_rejected() -> None:
    with pytest.raises(ValueError):
        WWRDependenceSpec(
            dependence_id="D",
            netting_set_id="NS1",
            counterparty_id="CP1",
            market_factor_id="FX",
            classification="general_wrong_way",
            channel="fx",
            correlation=1.0,
            as_of_date=date(2026, 1, 2),
            calibration_source="TEST",
            rationale="Expected rejection.",
        )


def test_low_plausibility_requires_approval() -> None:
    with pytest.raises(ValueError):
        XVAStressScenario(
            scenario_id="LOW-P",
            channel="systemic",
            severity="moderate",
            as_of_date=date(2026, 1, 2),
            calibration_source="TEST",
            rationale="Expected rejection.",
            plausibility_score=0.25,
            approved=False,
        )


def test_governed_severe_scenario_can_be_constructed() -> None:
    scenario = XVAStressScenario(
        scenario_id="SEVERE",
        channel="sovereign",
        severity="severe",
        as_of_date=date(2026, 1, 2),
        calibration_source="APPROVED_STRESS_LIBRARY",
        rationale="Approved sovereign stress.",
        exposure_multiplier=1.5,
        counterparty_hazard_multiplier=2.0,
        correlation_shift=0.2,
        approved=True,
    )
    assert scenario.approved is True

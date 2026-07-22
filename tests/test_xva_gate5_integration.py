from datetime import date
import math
import numpy as np
import pytest

from qmrl.xva import (
    DiscountCurve, FundingCurve, XVAExposureInput, XVAIntegrationPolicy,
    build_flat_credit_curve, integrate_xva,
)

AS_OF = date(2026, 1, 2)

def environment(positive=100.0, negative=80.0, mode="bilateral"):
    exposure = XVAExposureInput(
        times=[0.0, 1.0], netting_set_ids=("NS1",), counterparty_ids=("CP1",),
        expected_positive=[[0.0], [positive]], expected_negative=[[0.0], [negative]],
        mpor_expected_positive=[[0.0], [positive]], mpor_expected_negative=[[0.0], [negative]],
    )
    cp = build_flat_credit_curve(curve_id="CP", obligor_id="CP1", role="counterparty", probability_measure="risk_neutral", currency="USD", as_of_date=AS_OF, recovery_rate=0.4, spread_bps=100.0, node_times=[1.0])
    own = build_flat_credit_curve(curve_id="OWN", obligor_id="BANK", role="own", probability_measure="risk_neutral", currency="USD", as_of_date=AS_OF, recovery_rate=0.4, spread_bps=120.0, node_times=[1.0])
    discount = DiscountCurve("OIS", "USD", AS_OF, [0.0, 1.0], [1.0, 1.0])
    funding = FundingCurve("F", "USD", AS_OF, [0.0, 1.0], [0.0, 0.0], [0.0, 0.0])
    policy = XVAIntegrationPolicy(valuation_mode=mode, funding_survival_mode="none")
    return exposure, {"CP1": cp}, own, discount, funding, policy

def test_unilateral_cva_matches_flat_hazard_formula() -> None:
    exposure, cp, own, discount, funding, policy = environment(mode="unilateral")
    result = integrate_xva(exposure, counterparty_curves=cp, own_curve=own, discount_curve=discount, funding_curve=funding, policy=policy)
    expected = 100.0 * 0.6 * (1.0 - math.exp(-(0.01 / 0.6)))
    assert result.cva == pytest.approx(expected)
    assert result.dva == 0.0

def test_bilateral_cva_includes_own_survival() -> None:
    exposure, cp, own, discount, funding, policy = environment()
    result = integrate_xva(exposure, counterparty_curves=cp, own_curve=own, discount_curve=discount, funding_curve=funding, policy=policy)
    unilateral = 100.0 * 0.6 * (1.0 - math.exp(-(0.01 / 0.6)))
    assert result.cva == pytest.approx(unilateral * own.survival_probability(1.0))

def test_dva_uses_negative_exposure_and_own_curve() -> None:
    exposure, cp, own, discount, funding, policy = environment()
    result = integrate_xva(exposure, counterparty_curves=cp, own_curve=own, discount_curve=discount, funding_curve=funding, policy=policy)
    expected = 80.0 * 0.6 * (1.0 - own.survival_probability(1.0)) * cp["CP1"].survival_probability(1.0)
    assert result.dva == pytest.approx(expected)

def test_total_adjustment_has_controlled_sign_identity() -> None:
    exposure, cp, own, discount, funding, policy = environment()
    result = integrate_xva(exposure, counterparty_curves=cp, own_curve=own, discount_curve=discount, funding_curve=funding, policy=policy)
    assert result.total_adjustment == pytest.approx(-result.cva + result.dva - result.fca + result.fba)

def test_missing_counterparty_curve_is_rejected() -> None:
    exposure, _, own, discount, funding, policy = environment()
    with pytest.raises(ValueError):
        integrate_xva(exposure, counterparty_curves={}, own_curve=own, discount_curve=discount, funding_curve=funding, policy=policy)

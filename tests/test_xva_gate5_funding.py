from datetime import date
import pytest

from qmrl.xva import (
    DiscountCurve, FundingCurve, XVAExposureInput, XVAIntegrationPolicy,
    build_flat_credit_curve, integrate_xva,
)

AS_OF = date(2026, 1, 2)

def build(positive, negative, basis="collateralized"):
    exposure = XVAExposureInput(
        [0.0, 1.0], ("NS1",), ("CP1",),
        [[0.0], [positive]], [[0.0], [negative]],
        [[0.0], [positive * 1.5]], [[0.0], [negative * 1.5]],
    )
    cp = build_flat_credit_curve(curve_id="CP", obligor_id="CP1", role="counterparty", probability_measure="risk_neutral", currency="USD", as_of_date=AS_OF, recovery_rate=0.4, spread_bps=0.0, node_times=[1.0])
    own = build_flat_credit_curve(curve_id="OWN", obligor_id="BANK", role="own", probability_measure="risk_neutral", currency="USD", as_of_date=AS_OF, recovery_rate=0.4, spread_bps=0.0, node_times=[1.0])
    result = integrate_xva(
        exposure, counterparty_curves={"CP1": cp}, own_curve=own,
        discount_curve=DiscountCurve("OIS", "USD", AS_OF, [0.0, 1.0], [1.0, 1.0]),
        funding_curve=FundingCurve("F", "USD", AS_OF, [0.0, 1.0], [200.0, 200.0], [100.0, 100.0]),
        policy=XVAIntegrationPolicy(valuation_mode="unilateral", fva_basis=basis, funding_survival_mode="none"),
    )
    return result

def test_fca_is_borrowing_spread_times_positive_funding_requirement() -> None:
    assert build(100.0, 0.0).fca == pytest.approx(2.0)

def test_fba_is_lending_spread_times_negative_funding_requirement() -> None:
    assert build(0.0, 80.0).fba == pytest.approx(0.8)

def test_fva_equals_fca_minus_fba() -> None:
    result = build(100.0, 80.0)
    assert result.fva == pytest.approx(1.2)

def test_mpor_basis_changes_funding_components() -> None:
    collateralized = build(100.0, 80.0, "collateralized")
    mpor = build(100.0, 80.0, "mpor")
    assert mpor.fca == pytest.approx(1.5 * collateralized.fca)
    assert mpor.fba == pytest.approx(1.5 * collateralized.fba)

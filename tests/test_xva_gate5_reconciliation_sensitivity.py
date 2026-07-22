from datetime import date

from qmrl.xva import (
    DiscountCurve, FundingCurve, XVAExposureInput, XVAIntegrationPolicy,
    build_flat_credit_curve, integrate_xva, reconcile_xva,
    run_standard_xva_sensitivities, xva_manifest,
)

AS_OF = date(2026, 1, 2)

def environment():
    exposure = XVAExposureInput([0.0, 1.0], ("NS1",), ("CP1",), [[0.0], [100.0]], [[0.0], [80.0]], [[0.0], [120.0]], [[0.0], [90.0]])
    cp = build_flat_credit_curve(curve_id="CP", obligor_id="CP1", role="counterparty", probability_measure="risk_neutral", currency="USD", as_of_date=AS_OF, recovery_rate=0.4, spread_bps=100.0, node_times=[1.0])
    own = build_flat_credit_curve(curve_id="OWN", obligor_id="BANK", role="own", probability_measure="risk_neutral", currency="USD", as_of_date=AS_OF, recovery_rate=0.4, spread_bps=120.0, node_times=[1.0])
    discount = DiscountCurve("OIS", "USD", AS_OF, [0.0, 1.0], [1.0, 0.98])
    funding = FundingCurve("F", "USD", AS_OF, [0.0, 1.0], [200.0, 200.0], [100.0, 100.0])
    policy = XVAIntegrationPolicy(funding_survival_mode="first_to_default")
    return exposure, {"CP1": cp}, own, discount, funding, policy

def test_independent_challenger_reconciles() -> None:
    exposure, cp, own, discount, funding, policy = environment()
    result = integrate_xva(exposure, counterparty_curves=cp, own_curve=own, discount_curve=discount, funding_curve=funding, policy=policy)
    reconciliation = reconcile_xva(exposure, result, counterparty_curves=cp, own_curve=own, discount_curve=discount, funding_curve=funding, policy=policy)
    assert reconciliation.status == "PASS"

def test_spread_sensitivities_have_expected_direction() -> None:
    exposure, cp, own, discount, funding, policy = environment()
    report = run_standard_xva_sensitivities(exposure, counterparty_curves=cp, own_curve=own, discount_curve=discount, funding_curve=funding, policy=policy)
    assert report.counterparty_spread_cva_delta > 0.0
    assert report.own_spread_dva_delta > 0.0

def test_funding_cost_bump_increases_fca() -> None:
    exposure, cp, own, discount, funding, policy = environment()
    report = run_standard_xva_sensitivities(exposure, counterparty_curves=cp, own_curve=own, discount_curve=discount, funding_curve=funding, policy=policy)
    assert report.funding_cost_fca_delta > 0.0

def test_manifest_is_deterministic_sha256() -> None:
    exposure, cp, own, discount, funding, policy = environment()
    result = integrate_xva(exposure, counterparty_curves=cp, own_curve=own, discount_curve=discount, funding_curve=funding, policy=policy)
    first = xva_manifest(exposure, result, policy)
    second = xva_manifest(exposure, result, policy)
    assert first == second
    assert len(first["calculation_sha256"]) == 64

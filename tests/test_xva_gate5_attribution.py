from datetime import date
import numpy as np
import pytest

from qmrl.xva import (
    DiscountCurve, FundingCurve, TradeAllocationWeights, XVAExposureInput,
    XVAIntegrationPolicy, allocate_xva_to_trades, build_flat_credit_curve,
    equal_trade_weights, integrate_xva,
)

AS_OF = date(2026, 1, 2)

def result():
    exposure = XVAExposureInput(
        [0.0, 1.0], ("NS1", "NS2"), ("CP1", "CP1"),
        [[0.0, 0.0], [40.0, 60.0]], [[0.0, 0.0], [20.0, 30.0]],
        [[0.0, 0.0], [40.0, 60.0]], [[0.0, 0.0], [20.0, 30.0]],
    )
    cp = build_flat_credit_curve(curve_id="CP", obligor_id="CP1", role="counterparty", probability_measure="risk_neutral", currency="USD", as_of_date=AS_OF, recovery_rate=0.4, spread_bps=100.0, node_times=[1.0])
    own = build_flat_credit_curve(curve_id="OWN", obligor_id="BANK", role="own", probability_measure="risk_neutral", currency="USD", as_of_date=AS_OF, recovery_rate=0.4, spread_bps=120.0, node_times=[1.0])
    return integrate_xva(
        exposure, counterparty_curves={"CP1": cp}, own_curve=own,
        discount_curve=DiscountCurve("OIS", "USD", AS_OF, [0.0, 1.0], [1.0, 1.0]),
        funding_curve=FundingCurve("F", "USD", AS_OF, [0.0, 1.0], [100.0, 100.0], [50.0, 50.0]),
        policy=XVAIntegrationPolicy(funding_survival_mode="none"),
    )

def test_netting_set_totals_reconcile_to_portfolio() -> None:
    value = result()
    assert np.sum(value.cva_by_netting_set) == pytest.approx(value.cva)
    assert np.sum(value.fca_by_netting_set) == pytest.approx(value.fca)

def test_counterparty_totals_preserve_legal_sets() -> None:
    value = result()
    assert len(value.cva_by_counterparty) == 1
    assert value.cva_by_counterparty[0] == pytest.approx(value.cva)

def test_equal_trade_allocation_reconciles() -> None:
    value = result()
    weights = equal_trade_weights({"T1": "NS1", "T2": "NS1", "T3": "NS2"})
    allocation = allocate_xva_to_trades(value, weights)
    assert np.sum(allocation.cva) == pytest.approx(value.cva)
    assert np.sum(allocation.total_adjustment) == pytest.approx(value.total_adjustment)

def test_invalid_trade_weights_are_rejected() -> None:
    with pytest.raises(ValueError):
        TradeAllocationWeights(("T1", "T2"), ("NS1", "NS1"), [0.8, 0.8], [0.5, 0.5], [0.5, 0.5], [0.5, 0.5])

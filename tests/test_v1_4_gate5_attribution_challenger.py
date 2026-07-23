import pytest

from qmrl.allocation import (
    AllocationStatus,
    build_attribution,
    challenge_leave_one_out,
    euler_allocation,
    independent_leave_one_out,
    leave_one_out_allocation,
    rank_vectors,
)
from tests.v1_4_gate5_helpers import additive_portfolio, evaluator, nonlinear_portfolio


def test_attribution_contains_all_dimensions():
    portfolio = additive_portfolio()
    attribution = build_attribution(portfolio, euler_allocation(portfolio, evaluator()))
    assert set(attribution.by_trade) == {"T1", "T2", "T3"}
    assert set(attribution.by_counterparty) == {"CP1", "CP2", "CP3"}
    assert set(attribution.by_currency) == {"USD", "EUR"}
    assert set(attribution.by_product_family) == {"IR_SWAP", "OPTION"}


def test_trade_ranking_is_deterministic():
    portfolio = additive_portfolio()
    allocation = euler_allocation(portfolio, evaluator())
    first = rank_vectors(dict(allocation.by_trade))
    second = rank_vectors(dict(allocation.by_trade))
    assert first == second
    assert [row.rank for row in first] == [1, 2, 3]


def test_attribution_concentration_is_bounded():
    portfolio = nonlinear_portfolio()
    attribution = build_attribution(portfolio, leave_one_out_allocation(portfolio, evaluator()))
    assert 0.0 <= attribution.concentration_hhi <= 1.0


def test_independent_challenger_covers_all_trades():
    result = independent_leave_one_out(additive_portfolio(), evaluator())
    assert set(result) == {"T1", "T2", "T3"}


def test_challenger_reconciles():
    result = challenge_leave_one_out(additive_portfolio(), evaluator())
    assert result.status == AllocationStatus.PASS
    assert result.absolute_difference <= result.tolerance


def test_residual_is_exposed_in_attribution():
    portfolio = nonlinear_portfolio()
    allocation = leave_one_out_allocation(portfolio, evaluator())
    attribution = build_attribution(portfolio, allocation)
    assert attribution.residual_total_adjustment == pytest.approx(
        allocation.residual.total_adjustment
    )

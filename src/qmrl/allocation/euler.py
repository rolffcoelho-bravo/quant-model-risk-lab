"""Euler-style and leave-one-out allocation with residual reconciliation."""

from __future__ import annotations

from .diagnostics import detect_nonlinearity
from .domain import (
    AdjustmentVector,
    AllocationResult,
    AllocationStatus,
    PortfolioAllocationState,
    SignedAdjustmentVector,
)
from .evaluator import PortfolioEvaluator
from .incremental import leave_one_out
from .marginal import finite_difference_marginal


_COMPONENTS = (
    "cva",
    "dva",
    "fca",
    "fba",
    "mva",
    "kva",
    "wwr_uplift",
    "stress_adjustment",
)


def _residual(
    portfolio_value: AdjustmentVector,
    by_trade: dict[str, SignedAdjustmentVector],
) -> SignedAdjustmentVector:
    combined = SignedAdjustmentVector()
    for vector in by_trade.values():
        combined = combined.add(vector)
    target = SignedAdjustmentVector(**{
        name: float(getattr(portfolio_value, name))
        for name in _COMPONENTS
    })
    return target.subtract(combined)


def euler_allocation(
    portfolio: PortfolioAllocationState,
    evaluator: PortfolioEvaluator,
    *,
    bump_fraction: float = 1e-4,
    force_monitoring: bool = False,
) -> AllocationResult:
    nonlinearity = detect_nonlinearity(portfolio, evaluator)
    portfolio_value = evaluator.evaluate(portfolio)

    by_trade: dict[str, SignedAdjustmentVector] = {}
    statuses = []
    for trade in portfolio.trades:
        marginal = finite_difference_marginal(
            portfolio,
            trade.trade_id,
            evaluator,
            bump_fraction=bump_fraction,
            compare_full_revaluation=False,
        )
        by_trade[trade.trade_id] = marginal.derivative.scaled(trade.scale)
        statuses.append(marginal.status)

    residual = _residual(portfolio_value, by_trade)

    if not nonlinearity.euler_valid:
        status = AllocationStatus.INVALID
    elif any(status == AllocationStatus.REMEDIATE for status in statuses):
        status = AllocationStatus.REMEDIATE
    elif force_monitoring or abs(residual.total_adjustment) > 1e-6:
        status = AllocationStatus.PASS_WITH_MONITORING
    else:
        status = AllocationStatus.PASS

    return AllocationResult(
        portfolio=portfolio_value,
        by_trade=by_trade,
        residual=residual,
        method="euler",
        status=status,
        nonlinearity=nonlinearity,
    )


def leave_one_out_allocation(
    portfolio: PortfolioAllocationState,
    evaluator: PortfolioEvaluator,
) -> AllocationResult:
    portfolio_value = evaluator.evaluate(portfolio)
    removals = leave_one_out(portfolio, evaluator)
    by_trade = {
        trade_id: result.increment.scaled(-1.0)
        for trade_id, result in removals.items()
    }
    residual = _residual(portfolio_value, by_trade)
    nonlinearity = detect_nonlinearity(portfolio, evaluator)
    status = (
        AllocationStatus.PASS
        if abs(residual.total_adjustment) <= 1e-6
        else AllocationStatus.PASS_WITH_MONITORING
    )
    return AllocationResult(
        portfolio=portfolio_value,
        by_trade=by_trade,
        residual=residual,
        method="leave_one_out",
        status=status,
        nonlinearity=nonlinearity,
    )

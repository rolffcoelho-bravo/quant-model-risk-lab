"""Independent challenger calculations and reconciliation."""

from __future__ import annotations

from .domain import (
    AllocationChallenge,
    AllocationStatus,
    PortfolioAllocationState,
    SignedAdjustmentVector,
)
from .evaluator import PortfolioEvaluator
from .incremental import remove_trade


def independent_leave_one_out(
    portfolio: PortfolioAllocationState,
    evaluator: PortfolioEvaluator,
) -> dict[str, SignedAdjustmentVector]:
    """Loop-based challenger deliberately independent of allocation helpers."""
    base = evaluator.evaluate(portfolio)
    result: dict[str, SignedAdjustmentVector] = {}
    for trade in portfolio.trades:
        reduced_trades = tuple(
            candidate
            for candidate in portfolio.trades
            if candidate.trade_id != trade.trade_id
        )
        if not reduced_trades:
            continue
        reduced = PortfolioAllocationState(
            portfolio_id=portfolio.portfolio_id,
            trades=reduced_trades,
            reporting_currency=portfolio.reporting_currency,
            collateral_regime_switch=portfolio.collateral_regime_switch,
            concentration_addon_rate=portfolio.concentration_addon_rate,
        )
        changed = evaluator.evaluate(reduced)
        result[trade.trade_id] = base.subtract(changed)
    return result


def challenge_leave_one_out(
    portfolio: PortfolioAllocationState,
    evaluator: PortfolioEvaluator,
    *,
    tolerance: float = 1e-10,
) -> AllocationChallenge:
    primary = {
        trade.trade_id: remove_trade(portfolio, trade.trade_id, evaluator).increment.scaled(-1.0)
        for trade in portfolio.trades
        if len(portfolio.trades) > 1
    }
    challenger = independent_leave_one_out(portfolio, evaluator)
    primary_total = sum(vector.total_adjustment for vector in primary.values())
    challenger_total = sum(vector.total_adjustment for vector in challenger.values())
    difference = abs(primary_total - challenger_total)
    return AllocationChallenge(
        status=AllocationStatus.PASS if difference <= tolerance else AllocationStatus.REMEDIATE,
        primary_total=primary_total,
        challenger_total=challenger_total,
        absolute_difference=difference,
        tolerance=tolerance,
        details={
            trade_id: abs(
                primary[trade_id].total_adjustment
                - challenger[trade_id].total_adjustment
            )
            for trade_id in primary
        },
    )

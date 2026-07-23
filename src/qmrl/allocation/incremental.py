"""Full-revaluation incremental analytics."""

from __future__ import annotations

from .domain import IncrementalResult, PortfolioAllocationState, TradeAllocationInput
from .evaluator import PortfolioEvaluator


def insert_trade(
    portfolio: PortfolioAllocationState,
    trade: TradeAllocationInput,
    evaluator: PortfolioEvaluator,
) -> IncrementalResult:
    base = evaluator.evaluate(portfolio)
    changed = evaluator.evaluate(portfolio.with_trade(trade))
    return IncrementalResult(
        operation="insert",
        trade_id=trade.trade_id,
        base=base,
        changed=changed,
        increment=changed.subtract(base),
    )


def remove_trade(
    portfolio: PortfolioAllocationState,
    trade_id: str,
    evaluator: PortfolioEvaluator,
) -> IncrementalResult:
    base = evaluator.evaluate(portfolio)
    changed = evaluator.evaluate(portfolio.without(trade_id))
    return IncrementalResult(
        operation="remove",
        trade_id=trade_id,
        base=base,
        changed=changed,
        increment=changed.subtract(base),
    )


def replace_trade(
    portfolio: PortfolioAllocationState,
    trade_id: str,
    replacement: TradeAllocationInput,
    evaluator: PortfolioEvaluator,
) -> IncrementalResult:
    base = evaluator.evaluate(portfolio)
    changed = evaluator.evaluate(portfolio.replace(trade_id, replacement))
    return IncrementalResult(
        operation="replace",
        trade_id=trade_id,
        base=base,
        changed=changed,
        increment=changed.subtract(base),
    )


def leave_one_out(
    portfolio: PortfolioAllocationState,
    evaluator: PortfolioEvaluator,
) -> dict[str, IncrementalResult]:
    return {
        trade.trade_id: remove_trade(portfolio, trade.trade_id, evaluator)
        for trade in portfolio.trades
        if len(portfolio.trades) > 1
    }

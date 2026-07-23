"""Nonlinearity, approximation, concentration, and ranking diagnostics."""

from __future__ import annotations

import math
from collections import defaultdict

from .domain import (
    NonlinearityReport,
    PortfolioAllocationState,
    RankingRow,
    SignedAdjustmentVector,
)
from .evaluator import PortfolioEvaluator


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


def detect_nonlinearity(
    portfolio: PortfolioAllocationState,
    evaluator: PortfolioEvaluator,
    *,
    homogeneity_scale: float = 2.0,
    tolerance: float = 1e-8,
) -> NonlinearityReport:
    threshold = any(trade.threshold > 0.0 for trade in portfolio.trades)
    mta = any(trade.minimum_transfer_amount > 0.0 for trade in portfolio.trades)
    concentration = portfolio.concentration_addon_rate > 0.0
    switch = portfolio.collateral_regime_switch

    base = evaluator.evaluate(portfolio)
    scaled_portfolio = PortfolioAllocationState(
        portfolio_id=portfolio.portfolio_id,
        trades=tuple(
            trade.rescaled(trade.scale * homogeneity_scale)
            for trade in portfolio.trades
        ),
        reporting_currency=portfolio.reporting_currency,
        collateral_regime_switch=portfolio.collateral_regime_switch,
        concentration_addon_rate=portfolio.concentration_addon_rate,
    )
    scaled = evaluator.evaluate(scaled_portfolio)
    expected = base.scaled(homogeneity_scale)

    numerator = max(
        abs(float(getattr(scaled, name)) - float(getattr(expected, name)))
        for name in _COMPONENTS
    )
    denominator = max(
        1.0,
        max(abs(float(getattr(expected, name))) for name in _COMPONENTS),
    )
    homogeneity_error = numerator / denominator

    reasons = []
    if threshold:
        reasons.append("threshold")
    if mta:
        reasons.append("minimum_transfer_amount")
    if concentration:
        reasons.append("concentration_addon")
    if switch:
        reasons.append("collateral_regime_switch")
    if homogeneity_error > tolerance:
        reasons.append("failed_positive_homogeneity")

    return NonlinearityReport(
        threshold_present=threshold,
        mta_present=mta,
        concentration_addon_present=concentration,
        collateral_regime_switch=switch,
        homogeneity_error=homogeneity_error,
        euler_valid=not reasons,
        reasons=tuple(reasons),
    )


def concentration_hhi(values: dict[str, float]) -> float:
    magnitudes = [abs(float(value)) for value in values.values()]
    total = sum(magnitudes)
    if total == 0.0:
        return 0.0
    return sum((value / total) ** 2 for value in magnitudes)


def rank_vectors(
    vectors: dict[str, SignedAdjustmentVector],
) -> tuple[RankingRow, ...]:
    totals = {
        key: vector.total_adjustment
        for key, vector in vectors.items()
    }
    absolute_total = sum(abs(value) for value in totals.values())
    ordered = sorted(
        totals.items(),
        key=lambda item: (-abs(item[1]), item[0]),
    )
    return tuple(
        RankingRow(
            key=key,
            total_adjustment=value,
            absolute_share=0.0 if absolute_total == 0.0 else abs(value) / absolute_total,
            rank=index,
        )
        for index, (key, value) in enumerate(ordered, start=1)
    )


def group_vectors(
    portfolio: PortfolioAllocationState,
    by_trade: dict[str, SignedAdjustmentVector],
    dimension: str,
) -> dict[str, SignedAdjustmentVector]:
    if dimension not in {
        "counterparty",
        "netting_set",
        "currency",
        "product_family",
    }:
        raise ValueError("Unsupported allocation grouping dimension.")

    result: dict[str, SignedAdjustmentVector] = defaultdict(SignedAdjustmentVector)
    for trade in portfolio.trades:
        key = {
            "counterparty": trade.counterparty_id,
            "netting_set": trade.netting_set_id,
            "currency": trade.currency,
            "product_family": trade.product_family,
        }[dimension]
        result[key] = result[key].add(by_trade[trade.trade_id])
    return dict(result)

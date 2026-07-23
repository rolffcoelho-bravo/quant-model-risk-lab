"""Attribution views for Gate 5 allocation results."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .diagnostics import concentration_hhi, group_vectors, rank_vectors
from .domain import AllocationResult, PortfolioAllocationState, RankingRow, SignedAdjustmentVector


@dataclass(frozen=True)
class AllocationAttribution:
    by_trade: Mapping[str, SignedAdjustmentVector]
    by_counterparty: Mapping[str, SignedAdjustmentVector]
    by_netting_set: Mapping[str, SignedAdjustmentVector]
    by_currency: Mapping[str, SignedAdjustmentVector]
    by_product_family: Mapping[str, SignedAdjustmentVector]
    trade_ranking: tuple[RankingRow, ...]
    concentration_hhi: float
    residual_total_adjustment: float


def build_attribution(
    portfolio: PortfolioAllocationState,
    allocation: AllocationResult,
) -> AllocationAttribution:
    by_trade = dict(allocation.by_trade)
    totals = {
        trade_id: vector.total_adjustment
        for trade_id, vector in by_trade.items()
    }
    return AllocationAttribution(
        by_trade=by_trade,
        by_counterparty=group_vectors(portfolio, by_trade, "counterparty"),
        by_netting_set=group_vectors(portfolio, by_trade, "netting_set"),
        by_currency=group_vectors(portfolio, by_trade, "currency"),
        by_product_family=group_vectors(portfolio, by_trade, "product_family"),
        trade_ranking=rank_vectors(by_trade),
        concentration_hhi=concentration_hhi(totals),
        residual_total_adjustment=allocation.residual.total_adjustment,
    )

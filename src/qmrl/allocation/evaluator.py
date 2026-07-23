"""Evaluation protocol and deterministic public benchmark evaluator."""

from __future__ import annotations

from typing import Protocol
import math

from .domain import AdjustmentVector, PortfolioAllocationState


class PortfolioEvaluator(Protocol):
    def evaluate(self, portfolio: PortfolioAllocationState) -> AdjustmentVector:
        ...


class TransparentPortfolioEvaluator:
    """Deterministic evaluator for allocation validation.

    It composes standalone trade vectors and applies explicitly visible
    netting, collateral-threshold, MTA, concentration, regime-switch, and
    stress effects. It is not a production pricing engine.
    """

    def evaluate(self, portfolio: PortfolioAllocationState) -> AdjustmentVector:
        total = AdjustmentVector()
        for trade in portfolio.trades:
            scaled = trade.standalone.scaled(trade.scale)
            stressed = AdjustmentVector(
                cva=scaled.cva,
                dva=scaled.dva,
                fca=scaled.fca,
                fba=scaled.fba,
                mva=scaled.mva,
                kva=scaled.kva,
                wwr_uplift=scaled.wwr_uplift,
                stress_adjustment=scaled.stress_adjustment * trade.stress_multiplier,
            )
            total = total.add(stressed)

        # Transparent netting benefit by netting set.
        by_set: dict[str, list] = {}
        for trade in portfolio.trades:
            by_set.setdefault(trade.netting_set_id, []).append(trade)

        cva = total.cva
        fca = total.fca
        mva = total.mva

        for trades in by_set.values():
            if len(trades) > 1:
                gross_scale = sum(item.scale for item in trades)
                diversification = min(0.20, 0.025 * (len(trades) - 1))
                cva -= total.cva * diversification * gross_scale / max(
                    sum(item.scale for item in portfolio.trades), 1e-12
                )
                fca -= total.fca * diversification * 0.5 * gross_scale / max(
                    sum(item.scale for item in portfolio.trades), 1e-12
                )

            threshold = max(item.threshold for item in trades)
            mta = max(item.minimum_transfer_amount for item in trades)
            scale = sum(item.scale for item in trades)
            if threshold > 0.0:
                cva += 0.0025 * threshold * math.sqrt(scale)
            if mta > 0.0:
                fca += 0.0015 * mta * math.sqrt(scale)

        # Concentration add-on by explicit group.
        groups: dict[str, float] = {}
        for trade in portfolio.trades:
            key = trade.concentration_group or trade.counterparty_id
            groups[key] = groups.get(key, 0.0) + trade.scale
        total_scale = sum(groups.values())
        concentration = 0.0
        if total_scale > 0.0:
            concentration = sum((value / total_scale) ** 2 for value in groups.values())
        kva = total.kva * (1.0 + portfolio.concentration_addon_rate * concentration)

        if portfolio.collateral_regime_switch:
            mva *= 1.08
            cva *= 0.97

        return AdjustmentVector(
            cva=max(cva, 0.0),
            dva=total.dva,
            fca=max(fca, 0.0),
            fba=total.fba,
            mva=max(mva, 0.0),
            kva=max(kva, 0.0),
            wwr_uplift=total.wwr_uplift,
            stress_adjustment=total.stress_adjustment,
        )

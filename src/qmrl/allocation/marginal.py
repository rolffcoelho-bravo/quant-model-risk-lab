"""Finite-difference marginal valuation-adjustment analytics."""

from __future__ import annotations

import math

from .domain import (
    AllocationStatus,
    MarginalResult,
    PortfolioAllocationState,
    SignedAdjustmentVector,
)
from .evaluator import PortfolioEvaluator
from .incremental import remove_trade


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


def _central_derivative(
    portfolio: PortfolioAllocationState,
    trade_id: str,
    evaluator: PortfolioEvaluator,
    bump_fraction: float,
) -> SignedAdjustmentVector:
    trade = portfolio.trade(trade_id)
    bump = trade.scale * bump_fraction
    if bump <= 0.0:
        raise ValueError("Finite-difference bump must be positive.")
    lower_scale = trade.scale - bump
    if lower_scale <= 0.0:
        raise ValueError("Bump is too large for a central difference.")

    up = evaluator.evaluate(
        portfolio.replace(trade_id, trade.rescaled(trade.scale + bump))
    )
    down = evaluator.evaluate(
        portfolio.replace(trade_id, trade.rescaled(lower_scale))
    )
    difference = up.subtract(down)
    return difference.scaled(1.0 / (2.0 * bump))


def _relative_vector_error(
    left: SignedAdjustmentVector,
    right: SignedAdjustmentVector,
) -> float:
    numerator = max(
        abs(float(getattr(left, name)) - float(getattr(right, name)))
        for name in _COMPONENTS
    )
    denominator = max(
        1.0,
        max(abs(float(getattr(right, name))) for name in _COMPONENTS),
    )
    return numerator / denominator


def finite_difference_marginal(
    portfolio: PortfolioAllocationState,
    trade_id: str,
    evaluator: PortfolioEvaluator,
    *,
    bump_fraction: float = 1e-4,
    convergence_tolerance: float = 1e-4,
    approximation_tolerance: float = 0.20,
    compare_full_revaluation: bool = True,
) -> MarginalResult:
    bump_fraction = float(bump_fraction)
    if not math.isfinite(bump_fraction) or not 0.0 < bump_fraction < 0.5:
        raise ValueError("bump_fraction must lie between zero and 0.5.")

    primary = _central_derivative(
        portfolio,
        trade_id,
        evaluator,
        bump_fraction,
    )
    refined = _central_derivative(
        portfolio,
        trade_id,
        evaluator,
        bump_fraction / 2.0,
    )
    convergence_error = _relative_vector_error(primary, refined)

    full_reference = None
    approximation_error = None
    status = (
        AllocationStatus.PASS
        if convergence_error <= convergence_tolerance
        else AllocationStatus.PASS_WITH_MONITORING
    )

    if compare_full_revaluation:
        trade = portfolio.trade(trade_id)
        removal = remove_trade(portfolio, trade_id, evaluator)
        # Removal is changed - base. The contribution retained in the original
        # portfolio is therefore the negative removal increment, divided by scale.
        full_reference = removal.increment.scaled(-1.0 / trade.scale)
        approximation_error = _relative_vector_error(refined, full_reference)
        if approximation_error > approximation_tolerance:
            status = AllocationStatus.REMEDIATE

    return MarginalResult(
        trade_id=trade_id,
        bump_fraction=bump_fraction / 2.0,
        derivative=refined,
        convergence_error=convergence_error,
        full_revaluation_reference=full_reference,
        approximation_error=approximation_error,
        status=status,
    )

"""v1.4 Gate 5 incremental, marginal, and allocation analytics."""

from .attribution import AllocationAttribution, build_attribution
from .benchmark import additive_portfolio, nonlinear_portfolio, run_gate5_benchmarks
from .challenger import challenge_leave_one_out, independent_leave_one_out
from .diagnostics import concentration_hhi, detect_nonlinearity, group_vectors, rank_vectors
from .domain import (
    ALLOCATION_BOUNDARY,
    AdjustmentVector,
    AllocationChallenge,
    AllocationResult,
    AllocationStatus,
    IncrementalResult,
    MarginalResult,
    NonlinearityReport,
    PortfolioAllocationState,
    RankingRow,
    SignedAdjustmentVector,
    TradeAllocationInput,
)
from .euler import euler_allocation, leave_one_out_allocation
from .evaluator import PortfolioEvaluator, TransparentPortfolioEvaluator
from .incremental import insert_trade, leave_one_out, remove_trade, replace_trade
from .marginal import finite_difference_marginal

__all__ = [
    "ALLOCATION_BOUNDARY",
    "AdjustmentVector",
    "AllocationAttribution",
    "AllocationChallenge",
    "AllocationResult",
    "AllocationStatus",
    "IncrementalResult",
    "MarginalResult",
    "NonlinearityReport",
    "PortfolioAllocationState",
    "PortfolioEvaluator",
    "RankingRow",
    "SignedAdjustmentVector",
    "TradeAllocationInput",
    "TransparentPortfolioEvaluator",
    "additive_portfolio",
    "build_attribution",
    "challenge_leave_one_out",
    "concentration_hhi",
    "detect_nonlinearity",
    "euler_allocation",
    "finite_difference_marginal",
    "group_vectors",
    "independent_leave_one_out",
    "insert_trade",
    "leave_one_out",
    "leave_one_out_allocation",
    "nonlinear_portfolio",
    "rank_vectors",
    "remove_trade",
    "replace_trade",
    "run_gate5_benchmarks",
]

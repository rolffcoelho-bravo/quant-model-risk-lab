"""Initial margin, MVA, attribution, sensitivities, and challenge controls."""

from .domain import (
    PROXY_LABEL,
    InitialMarginProfile,
    MarginPolicy,
    MVAAggregation,
    MVABucket,
    MVAChallengeReport,
    MVAResult,
    ParametricMarginInput,
    PathwiseMarginInput,
    SurvivalProfile,
)
from .initial_margin import (
    calculate_historical_initial_margin,
    calculate_parametric_initial_margin,
    empirical_quantile,
    policy_hash,
    scale_margin_profile,
)
from .mva import calculate_mva
from .attribution import aggregate_mva
from .challenger import challenge_mva, independent_mva
from .sensitivity import build_standard_mva_sensitivities
from .benchmark import (
    MarginBenchmarkResult,
    load_margin_benchmark_contract,
    run_margin_benchmark_suite,
)

__all__ = [
    "PROXY_LABEL",
    "InitialMarginProfile",
    "MarginBenchmarkResult",
    "MarginPolicy",
    "MVAAggregation",
    "MVABucket",
    "MVAChallengeReport",
    "MVAResult",
    "ParametricMarginInput",
    "PathwiseMarginInput",
    "SurvivalProfile",
    "aggregate_mva",
    "build_standard_mva_sensitivities",
    "calculate_historical_initial_margin",
    "calculate_mva",
    "calculate_parametric_initial_margin",
    "challenge_mva",
    "empirical_quantile",
    "independent_mva",
    "load_margin_benchmark_contract",
    "policy_hash",
    "run_margin_benchmark_suite",
    "scale_margin_profile",
]

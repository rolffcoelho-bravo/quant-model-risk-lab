"""XVA validation and exposure-simulation controls.

The package preserves the public v0.9 static XVA API while adding the v1.3
Gate 1 foundations for time grids, netting sets, collateral state, exposure
measurement, and deterministic benchmarks.
"""

from .legacy import (
    XVAAssumptions,
    compute_xva_from_clean_values,
    cumulative_default_probability,
    hazard_rate_from_spread,
    scenario_exposures,
    spread_bps_to_decimal,
    validate_recovery_rate,
)
from .time_grid import (
    TimeGridPoint,
    TimeGridSpec,
    adjust_business_day,
    build_time_grid,
    year_fraction_act_365,
)
from .netting import (
    NettingResult,
    NettingSet,
    Trade,
    aggregate_netting_set,
    validate_trade_membership,
)
from .collateral import (
    CollateralAgreement,
    CollateralPoint,
    effective_collateral,
    required_effective_collateral,
    simulate_collateral_path,
)
from .exposure import (
    ExposureProfile,
    ExposureStatistics,
    collateralized_exposure,
    exposure_statistics,
    margin_period_of_risk_exposure,
)
from .benchmark import (
    BenchmarkResult,
    evaluate_reference_case,
    load_benchmark_contract,
    run_benchmark_suite,
)

__all__ = [
    "XVAAssumptions",
    "compute_xva_from_clean_values",
    "cumulative_default_probability",
    "hazard_rate_from_spread",
    "scenario_exposures",
    "spread_bps_to_decimal",
    "validate_recovery_rate",
    "TimeGridPoint",
    "TimeGridSpec",
    "adjust_business_day",
    "build_time_grid",
    "year_fraction_act_365",
    "NettingResult",
    "NettingSet",
    "Trade",
    "aggregate_netting_set",
    "validate_trade_membership",
    "CollateralAgreement",
    "CollateralPoint",
    "effective_collateral",
    "required_effective_collateral",
    "simulate_collateral_path",
    "ExposureProfile",
    "ExposureStatistics",
    "collateralized_exposure",
    "exposure_statistics",
    "margin_period_of_risk_exposure",
    "BenchmarkResult",
    "evaluate_reference_case",
    "load_benchmark_contract",
    "run_benchmark_suite",
]

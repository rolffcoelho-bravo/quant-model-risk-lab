"""XVA validation and exposure-simulation controls.

The package preserves the public v0.9 static XVA API while adding the v1.3
Gate 1 foundations for time grids, netting sets, collateral state, exposure
measurement, and deterministic benchmarks, plus Gate 2 scenario paths,
future clean values, convergence diagnostics, and analytical challengers.
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

from .random_control import (
    RandomControl,
    generate_standard_normal,
)
from .risk_factors import (
    RiskFactorSet,
    RiskFactorSpec,
    validate_correlation_matrix,
)
from .scenario_paths import (
    ScenarioCube,
    generate_scenario_cube,
    scenario_manifest,
)
from .future_value import (
    FXForwardTrade,
    FutureValueCube,
    ZeroCouponBondTrade,
    value_fx_forward,
    value_portfolio,
    value_zero_coupon_bond,
)
from .convergence import (
    ConvergenceDiagnostics,
    convergence_diagnostics,
)
from .scenario_challenger import (
    AnalyticalMomentCheck,
    compare_terminal_moments,
    gbm_moments,
    vasicek_moments,
)
from .scenario_benchmark import (
    ScenarioBenchmarkResult,
    evaluate_scenario_benchmark,
    load_scenario_benchmark_contract,
    run_scenario_benchmark_suite,
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
    "RandomControl",
    "generate_standard_normal",
    "RiskFactorSet",
    "RiskFactorSpec",
    "validate_correlation_matrix",
    "ScenarioCube",
    "generate_scenario_cube",
    "scenario_manifest",
    "FXForwardTrade",
    "FutureValueCube",
    "ZeroCouponBondTrade",
    "value_fx_forward",
    "value_portfolio",
    "value_zero_coupon_bond",
    "ConvergenceDiagnostics",
    "convergence_diagnostics",
    "AnalyticalMomentCheck",
    "compare_terminal_moments",
    "gbm_moments",
    "vasicek_moments",
    "ScenarioBenchmarkResult",
    "evaluate_scenario_benchmark",
    "load_scenario_benchmark_contract",
    "run_scenario_benchmark_suite",
]

# v1.3 Gate 3 pathwise exposure integration
from .pathwise_exposure import (
    PathwiseNettingCube,
    CollateralStateCube,
    PathwiseExposureCube,
    ExposureAggregation,
    ExposureReconciliation,
    allocate_future_values,
    simulate_pathwise_collateral,
    build_pathwise_exposure_cube,
    aggregate_pathwise_exposure,
    reconcile_pathwise_exposure,
    exposure_manifest,
)
from .exposure_benchmark import (
    ExposureIntegrationBenchmarkResult,
    evaluate_exposure_integration_benchmark,
    load_exposure_integration_benchmark_contract,
    run_exposure_integration_benchmark_suite,
)

__all__.extend([
    "PathwiseNettingCube",
    "CollateralStateCube",
    "PathwiseExposureCube",
    "ExposureAggregation",
    "ExposureReconciliation",
    "allocate_future_values",
    "simulate_pathwise_collateral",
    "build_pathwise_exposure_cube",
    "aggregate_pathwise_exposure",
    "reconcile_pathwise_exposure",
    "exposure_manifest",
    "ExposureIntegrationBenchmarkResult",
    "evaluate_exposure_integration_benchmark",
    "load_exposure_integration_benchmark_contract",
    "run_exposure_integration_benchmark_suite",
])

# v1.3 Gate 4 counterparty credit calibration
from .credit_curve import (
    CreditCurve,
    CreditCurveRepricing,
    CreditCurveSensitivity,
    CreditQuote,
    RecoveryAssumption,
    build_flat_credit_curve,
    calibrate_piecewise_credit_curve,
    cds_legs,
    credit_curve_manifest,
    credit_curve_sensitivity,
    flat_hazard_from_spread,
    par_spread_bps,
    reprice_credit_quotes,
    validate_credit_quotes,
    validate_recovery_assumption,
)
from .credit_proxy import (
    CreditProxyCandidate,
    CreditProxySelection,
    proxy_selection_to_quote,
    select_credit_proxy,
)
from .credit_benchmark import (
    CreditCalibrationBenchmarkResult,
    evaluate_credit_benchmark,
    load_credit_benchmark_contract,
    run_credit_benchmark_suite,
)

__all__.extend([
    "CreditCurve",
    "CreditCurveRepricing",
    "CreditCurveSensitivity",
    "CreditQuote",
    "RecoveryAssumption",
    "build_flat_credit_curve",
    "calibrate_piecewise_credit_curve",
    "cds_legs",
    "credit_curve_manifest",
    "credit_curve_sensitivity",
    "flat_hazard_from_spread",
    "par_spread_bps",
    "reprice_credit_quotes",
    "validate_credit_quotes",
    "validate_recovery_assumption",
    "CreditProxyCandidate",
    "CreditProxySelection",
    "proxy_selection_to_quote",
    "select_credit_proxy",
    "CreditCalibrationBenchmarkResult",
    "evaluate_credit_benchmark",
    "load_credit_benchmark_contract",
    "run_credit_benchmark_suite",
])

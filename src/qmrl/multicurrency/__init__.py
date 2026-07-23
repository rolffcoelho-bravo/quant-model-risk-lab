"""Multi-currency exposure, collateral, attribution, and challenge controls."""

from .domain import (
    CollateralProfile,
    FXQuote,
    MultiCurrencyExposureResult,
    MultiCurrencyPolicy,
    PathwiseSeries,
)
from .fx import (
    FXScenarioMarket,
    FXTriangulationReport,
)
from .curves import (
    CurrencyCurveSet,
    TermCurve,
)
from .collateral import (
    accrue_collateral,
    collateral_as_series,
    convert_collateral_profile,
    remunerate_collateral_profile,
    switch_collateral_currency,
)
from .exposure import calculate_multicurrency_exposure
from .attribution import (
    CollateralSwitchImpact,
    CurrencyAttribution,
    aggregate_expected_profiles,
    build_currency_attribution,
    collateral_switch_impact,
)
from .challenger import (
    MultiCurrencyChallengeReport,
    challenge_multicurrency_exposure,
    independent_multicurrency_profiles,
)
from .benchmark import (
    MultiCurrencyBenchmarkResult,
    load_multicurrency_benchmark_contract,
    run_multicurrency_benchmark_suite,
)

__all__ = [
    "CollateralProfile",
    "CollateralSwitchImpact",
    "CurrencyAttribution",
    "CurrencyCurveSet",
    "FXQuote",
    "FXScenarioMarket",
    "FXTriangulationReport",
    "MultiCurrencyBenchmarkResult",
    "MultiCurrencyChallengeReport",
    "MultiCurrencyExposureResult",
    "MultiCurrencyPolicy",
    "PathwiseSeries",
    "TermCurve",
    "accrue_collateral",
    "aggregate_expected_profiles",
    "build_currency_attribution",
    "calculate_multicurrency_exposure",
    "challenge_multicurrency_exposure",
    "collateral_as_series",
    "collateral_switch_impact",
    "convert_collateral_profile",
    "independent_multicurrency_profiles",
    "load_multicurrency_benchmark_contract",
    "remunerate_collateral_profile",
    "run_multicurrency_benchmark_suite",
    "switch_collateral_currency",
]

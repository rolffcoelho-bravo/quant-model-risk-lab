from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np

from .attribution import build_capital_attribution
from .capital_profile import build_capital_profile
from .domain import BpsCurve, CapitalExposureInput, CapitalMarketState, CapitalPolicy, IntegrationRule
from .kva import calculate_kva


@dataclass(frozen=True)
class CapitalBenchmark:
    name: str
    observed: float


def _input(exposure: np.ndarray, *, risk_weights: np.ndarray | None = None) -> CapitalExposureInput:
    rows = exposure.shape[0]
    return CapitalExposureInput(
        times=np.array([0.0, 1.0, 2.0]),
        expected_exposure=exposure,
        counterparty_ids=tuple(f"CP{index + 1}" for index in range(rows)),
        netting_set_ids=tuple(f"NS{index + 1}" for index in range(rows)),
        currencies=tuple("USD" if index % 2 == 0 else "EUR" for index in range(rows)),
        risk_weights=risk_weights,
    )


def _market(survival: np.ndarray | None = None) -> CapitalMarketState:
    return CapitalMarketState(
        times=np.array([0.0, 1.0, 2.0]),
        discount_factors=np.array([1.0, 0.98, 0.95]),
        counterparty_survival=np.array([1.0, 0.97, 0.93]) if survival is None else survival,
    )


def _hurdle(level: float = 1000.0) -> BpsCurve:
    return BpsCurve(np.array([0.0, 2.0]), np.array([level, level]))


def _kva(exposure: np.ndarray, policy: CapitalPolicy | None = None, *, market: CapitalMarketState | None = None, hurdle: BpsCurve | None = None, risk_weights: np.ndarray | None = None) -> float:
    profile = build_capital_profile(_input(exposure, risk_weights=risk_weights), policy or CapitalPolicy())
    return calculate_kva(profile, market or _market(), hurdle or _hurdle()).total_kva


def run_capital_benchmarks() -> tuple[CapitalBenchmark, ...]:
    base_exposure = np.array([[0.0, 100.0, 60.0]])
    base_policy = CapitalPolicy(integration_rule=IntegrationRule.TRAPEZOID)
    zero = _kva(np.zeros((1, 3)), base_policy)
    zero_hurdle = _kva(base_exposure, base_policy, hurdle=_hurdle(0.0))
    base = _kva(base_exposure, base_policy)
    stressed = _kva(base_exposure, replace(base_policy, stress_multiplier=1.5))
    high_risk_weight = _kva(base_exposure, replace(base_policy, risk_weight=0.75))
    two_set = _kva(np.array([[0.0, 100.0, 60.0], [0.0, 40.0, 20.0]]), base_policy)
    discounted = _kva(base_exposure, base_policy, market=_market().shifted_discount_rate(200.0))
    lower_survival = _kva(base_exposure, base_policy, market=_market(np.array([1.0, 0.80, 0.60])))
    return (
        CapitalBenchmark("zero_exposure_zero_kva", zero),
        CapitalBenchmark("zero_hurdle_zero_kva", zero_hurdle),
        CapitalBenchmark("base_trapezoid_kva", base),
        CapitalBenchmark("stress_multiplier_monotonic", stressed),
        CapitalBenchmark("risk_weight_monotonic", high_risk_weight),
        CapitalBenchmark("two_set_portfolio_kva", two_set),
        CapitalBenchmark("discount_shock_reduces_kva", discounted),
        CapitalBenchmark("survival_decay_reduces_kva", lower_survival),
    )

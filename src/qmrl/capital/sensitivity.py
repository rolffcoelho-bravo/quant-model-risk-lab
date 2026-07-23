from __future__ import annotations

from dataclasses import dataclass, replace

from .capital_profile import build_capital_profile
from .domain import BpsCurve, CapitalExposureInput, CapitalMarketState, CapitalPolicy
from .kva import calculate_kva


@dataclass(frozen=True)
class CapitalSensitivity:
    scenario: str
    kva: float
    delta: float


def standard_capital_sensitivities(
    exposure_input: CapitalExposureInput,
    policy: CapitalPolicy,
    market_state: CapitalMarketState,
    hurdle_curve: BpsCurve,
) -> tuple[CapitalSensitivity, ...]:
    base_profile = build_capital_profile(exposure_input, policy)
    base = calculate_kva(base_profile, market_state, hurdle_curve).total_kva

    scenarios: list[tuple[str, CapitalPolicy, CapitalMarketState, BpsCurve]] = [
        ("hurdle_plus_100bp", policy, market_state, hurdle_curve.shifted(100.0)),
        ("ead_plus_10pct", replace(policy, ead_multiplier=policy.ead_multiplier * 1.10), market_state, hurdle_curve),
        ("risk_weight_plus_10pct", replace(policy, risk_weight=policy.risk_weight * 1.10), market_state, hurdle_curve),
        ("capital_ratio_plus_1pp", replace(policy, capital_ratio=policy.capital_ratio + 0.01), market_state, hurdle_curve),
        ("maturity_plus_10pct", replace(policy, maturity_multiplier=policy.maturity_multiplier * 1.10), market_state, hurdle_curve),
        ("stress_plus_10pct", replace(policy, stress_multiplier=policy.stress_multiplier * 1.10), market_state, hurdle_curve),
        ("discount_rate_plus_100bp", policy, market_state.shifted_discount_rate(100.0), hurdle_curve),
    ]

    results: list[CapitalSensitivity] = []
    for name, scenario_policy, scenario_market, scenario_hurdle in scenarios:
        profile = build_capital_profile(exposure_input, scenario_policy)
        value = calculate_kva(profile, scenario_market, scenario_hurdle).total_kva
        results.append(CapitalSensitivity(name, float(value), float(value - base)))
    return tuple(results)

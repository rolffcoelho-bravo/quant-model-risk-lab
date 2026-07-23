from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .capital_profile import CapitalProfileResult
from .domain import BpsCurve, CapitalMarketState, IntegrationRule, SurvivalMode
from .kva import KVAResult


@dataclass(frozen=True)
class ChallengerReconciliation:
    challenger_total: float
    implementation_total: float
    absolute_difference: float
    relative_difference: float
    status: str


def challenger_kva(
    profile: CapitalProfileResult,
    market_state: CapitalMarketState,
    hurdle_curve: BpsCurve,
) -> float:
    times = profile.exposure_input.times
    hurdle = hurdle_curve.values(times) / 10000.0
    total = 0.0
    for set_index in range(profile.exposure_input.netting_set_count):
        values: list[float] = []
        for time_index in range(len(times)):
            survival = (
                float(market_state.counterparty_survival[time_index])
                if profile.policy.survival_mode == SurvivalMode.COUNTERPARTY
                else 1.0
            )
            values.append(
                float(profile.capital_profiles[set_index, time_index])
                * float(market_state.discount_factors[time_index])
                * survival
                * float(hurdle[time_index])
            )
        for interval_index, dt in enumerate(np.diff(times)):
            if profile.policy.integration_rule == IntegrationRule.ENDPOINT:
                total += values[interval_index + 1] * float(dt)
            else:
                total += 0.5 * (values[interval_index] + values[interval_index + 1]) * float(dt)
    return float(total)


def reconcile_challenger(
    implementation: KVAResult,
    challenger_total: float,
    *,
    soft_tolerance: float = 1e-10,
    hard_tolerance: float = 1e-8,
) -> ChallengerReconciliation:
    absolute = abs(implementation.total_kva - challenger_total)
    scale = max(abs(implementation.total_kva), abs(challenger_total), 1.0)
    relative = absolute / scale
    if absolute <= soft_tolerance:
        status = "PASS"
    elif absolute <= hard_tolerance:
        status = "PASS_WITH_MONITORING"
    else:
        status = "BLOCK"
    return ChallengerReconciliation(
        challenger_total=float(challenger_total),
        implementation_total=float(implementation.total_kva),
        absolute_difference=float(absolute),
        relative_difference=float(relative),
        status=status,
    )

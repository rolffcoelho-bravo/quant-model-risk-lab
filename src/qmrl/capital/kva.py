from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .capital_profile import CapitalProfileResult
from .domain import BpsCurve, CapitalMarketState, IntegrationRule, SurvivalMode


@dataclass(frozen=True)
class KVAResult:
    total_kva: float
    netting_set_kva: np.ndarray
    interval_contributions: np.ndarray
    integrand_profiles: np.ndarray
    hurdle_rates: np.ndarray
    survival_weights: np.ndarray


def _interval_contributions(values: np.ndarray, times: np.ndarray, rule: IntegrationRule) -> np.ndarray:
    dt = np.diff(times)
    if rule == IntegrationRule.ENDPOINT:
        return values[:, 1:] * dt[None, :]
    if rule == IntegrationRule.TRAPEZOID:
        return 0.5 * (values[:, :-1] + values[:, 1:]) * dt[None, :]
    raise ValueError(f"Unsupported integration rule: {rule}")


def calculate_kva(
    profile: CapitalProfileResult,
    market_state: CapitalMarketState,
    hurdle_curve: BpsCurve,
) -> KVAResult:
    times = profile.exposure_input.times
    if not np.array_equal(times, market_state.times):
        raise ValueError("Capital profile and market state must use the same time grid.")
    hurdle = hurdle_curve.values(times) / 10000.0
    survival = (
        market_state.counterparty_survival
        if profile.policy.survival_mode == SurvivalMode.COUNTERPARTY
        else np.ones_like(times)
    )
    integrand = (
        profile.capital_profiles
        * market_state.discount_factors[None, :]
        * survival[None, :]
        * hurdle[None, :]
    )
    interval = _interval_contributions(integrand, times, profile.policy.integration_rule)
    by_set = interval.sum(axis=1)
    total = float(by_set.sum())
    for value in (hurdle, survival, integrand, interval, by_set):
        value.setflags(write=False)
    return KVAResult(
        total_kva=total,
        netting_set_kva=by_set,
        interval_contributions=interval,
        integrand_profiles=integrand,
        hurdle_rates=hurdle,
        survival_weights=survival,
    )

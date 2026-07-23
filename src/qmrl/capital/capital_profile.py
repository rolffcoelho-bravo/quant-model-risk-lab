from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .domain import CapitalExposureInput, CapitalPolicy


@dataclass(frozen=True)
class CapitalProfileResult:
    exposure_input: CapitalExposureInput
    policy: CapitalPolicy
    effective_risk_weights: np.ndarray
    ead_profiles: np.ndarray
    capital_profiles: np.ndarray
    aggregate_ead_profile: np.ndarray
    aggregate_capital_profile: np.ndarray

    @property
    def peak_capital(self) -> float:
        return float(np.max(self.aggregate_capital_profile))

    @property
    def terminal_capital(self) -> float:
        return float(self.aggregate_capital_profile[-1])


def build_capital_profile(
    exposure_input: CapitalExposureInput,
    policy: CapitalPolicy,
) -> CapitalProfileResult:
    overrides = exposure_input.risk_weights
    effective = np.where(np.isnan(overrides), policy.risk_weight, overrides)
    ead = exposure_input.expected_exposure * policy.ead_multiplier
    capital = (
        ead
        * effective[:, None]
        * policy.capital_ratio
        * policy.maturity_multiplier
        * policy.stress_multiplier
    )
    aggregate_ead = ead.sum(axis=0)
    aggregate_capital = capital.sum(axis=0)
    for value in (effective, ead, capital, aggregate_ead, aggregate_capital):
        value.setflags(write=False)
    return CapitalProfileResult(
        exposure_input=exposure_input,
        policy=policy,
        effective_risk_weights=effective,
        ead_profiles=ead,
        capital_profiles=capital,
        aggregate_ead_profile=aggregate_ead,
        aggregate_capital_profile=aggregate_capital,
    )

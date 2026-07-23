"""Governed initial-margin and MVA domain objects for v1.4 Gate 3."""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Mapping


PROXY_LABEL = "PUBLIC_PROXY_NOT_SIMM_OR_CCP"


def _currency(code: str) -> str:
    value = code.strip().upper()
    if len(value) != 3 or not value.isalpha():
        raise ValueError(f"Invalid ISO-style currency code: {code!r}.")
    return value


def _times(values: tuple[float, ...]) -> tuple[float, ...]:
    result = tuple(float(value) for value in values)
    if len(result) < 2:
        raise ValueError("At least two time points are required.")
    if result[0] < 0.0 or any(not math.isfinite(value) for value in result):
        raise ValueError("Time points must be finite and non-negative.")
    if any(right <= left for left, right in zip(result, result[1:])):
        raise ValueError("Time grid must be strictly increasing.")
    return result


def _profile(values: tuple[float, ...], width: int) -> tuple[float, ...]:
    result = tuple(float(value) for value in values)
    if len(result) != width:
        raise ValueError("Profile length must match the time grid.")
    if any(not math.isfinite(value) or value < 0.0 for value in result):
        raise ValueError("Margin profiles must be finite and non-negative.")
    return result


@dataclass(frozen=True)
class MarginPolicy:
    method: str
    confidence_level: float = 0.99
    margin_period_days: int = 10
    base_margin_days: int = 10
    addon_rate: float = 0.0
    minimum_margin: float = 0.0
    received_margin_reusable: bool = False
    posted_margin_segregated: bool = True
    integration_rule: str = "trapezoid"
    survival_treatment: str = "joint"
    proxy_label: str = PROXY_LABEL

    def __post_init__(self) -> None:
        if self.method not in {"historical_simulation", "parametric"}:
            raise ValueError("Unsupported initial-margin proxy method.")
        if not 0.5 < float(self.confidence_level) < 1.0:
            raise ValueError("confidence_level must lie strictly between 0.5 and 1.")
        if int(self.margin_period_days) <= 0 or int(self.base_margin_days) <= 0:
            raise ValueError("Margin periods must be positive integers.")
        if float(self.addon_rate) < 0.0 or float(self.minimum_margin) < 0.0:
            raise ValueError("Margin add-ons and minimums cannot be negative.")
        if self.integration_rule not in {"trapezoid", "endpoint"}:
            raise ValueError("Unsupported MVA integration rule.")
        if self.survival_treatment not in {
            "joint", "own", "counterparty", "none"
        }:
            raise ValueError("Unsupported survival treatment.")
        if not self.posted_margin_segregated:
            raise ValueError("Gate 3 approves segregated posted initial margin only.")
        if self.proxy_label != PROXY_LABEL:
            raise ValueError("Public margin outputs must retain the proxy boundary label.")


@dataclass(frozen=True)
class PathwiseMarginInput:
    netting_set_id: str
    currency: str
    times: tuple[float, ...]
    values: tuple[tuple[float, ...], ...]

    def __post_init__(self) -> None:
        if not self.netting_set_id.strip():
            raise ValueError("netting_set_id cannot be empty.")
        times = _times(self.times)
        if not self.values:
            raise ValueError("At least one value path is required.")
        matrix: list[tuple[float, ...]] = []
        for row in self.values:
            converted = tuple(float(value) for value in row)
            if len(converted) != len(times):
                raise ValueError("Every path must match the time grid.")
            if any(not math.isfinite(value) for value in converted):
                raise ValueError("Pathwise values must be finite.")
            matrix.append(converted)
        object.__setattr__(self, "currency", _currency(self.currency))
        object.__setattr__(self, "times", times)
        object.__setattr__(self, "values", tuple(matrix))

    @property
    def path_count(self) -> int:
        return len(self.values)


@dataclass(frozen=True)
class ParametricMarginInput:
    netting_set_id: str
    currency: str
    times: tuple[float, ...]
    sensitivities: tuple[tuple[float, ...], ...]
    covariance: tuple[tuple[float, ...], ...]
    posted_multiplier: float = 1.0
    received_multiplier: float = 1.0
    volatility_scale: float = 1.0

    def __post_init__(self) -> None:
        if not self.netting_set_id.strip():
            raise ValueError("netting_set_id cannot be empty.")
        times = _times(self.times)
        if len(self.sensitivities) != len(times) or not self.sensitivities:
            raise ValueError("Sensitivity rows must match the time grid.")
        width = len(self.sensitivities[0])
        if width == 0 or any(len(row) != width for row in self.sensitivities):
            raise ValueError("Sensitivity rows must be non-empty and aligned.")
        covariance = tuple(tuple(float(value) for value in row) for row in self.covariance)
        if len(covariance) != width or any(len(row) != width for row in covariance):
            raise ValueError("Covariance dimensions must match the sensitivity factors.")
        for i in range(width):
            if covariance[i][i] < 0.0:
                raise ValueError("Covariance diagonal cannot be negative.")
            for j in range(width):
                if not math.isfinite(covariance[i][j]):
                    raise ValueError("Covariance values must be finite.")
                if abs(covariance[i][j] - covariance[j][i]) > 1e-12:
                    raise ValueError("Covariance matrix must be symmetric.")
        for row in self.sensitivities:
            if any(not math.isfinite(float(value)) for value in row):
                raise ValueError("Sensitivities must be finite.")
        if self.posted_multiplier < 0.0 or self.received_multiplier < 0.0:
            raise ValueError("Directional margin multipliers cannot be negative.")
        if self.volatility_scale <= 0.0 or not math.isfinite(self.volatility_scale):
            raise ValueError("volatility_scale must be finite and positive.")
        object.__setattr__(self, "currency", _currency(self.currency))
        object.__setattr__(self, "times", times)
        object.__setattr__(
            self,
            "sensitivities",
            tuple(tuple(float(value) for value in row) for row in self.sensitivities),
        )
        object.__setattr__(self, "covariance", covariance)


@dataclass(frozen=True)
class InitialMarginProfile:
    netting_set_id: str
    currency: str
    times: tuple[float, ...]
    posted_margin: tuple[float, ...]
    received_margin: tuple[float, ...]
    method: str
    policy_hash: str
    received_margin_reusable: bool
    proxy_label: str = PROXY_LABEL

    def __post_init__(self) -> None:
        if not self.netting_set_id.strip():
            raise ValueError("netting_set_id cannot be empty.")
        times = _times(self.times)
        if self.method not in {"historical_simulation", "parametric"}:
            raise ValueError("Unsupported margin method.")
        if not self.policy_hash.strip():
            raise ValueError("policy_hash cannot be empty.")
        if self.proxy_label != PROXY_LABEL:
            raise ValueError("Initial margin must retain the public proxy label.")
        object.__setattr__(self, "currency", _currency(self.currency))
        object.__setattr__(self, "times", times)
        object.__setattr__(self, "posted_margin", _profile(self.posted_margin, len(times)))
        object.__setattr__(self, "received_margin", _profile(self.received_margin, len(times)))


@dataclass(frozen=True)
class SurvivalProfile:
    times: tuple[float, ...]
    own_survival: tuple[float, ...]
    counterparty_survival: tuple[float, ...]

    def __post_init__(self) -> None:
        times = _times(self.times)
        own = tuple(float(value) for value in self.own_survival)
        cp = tuple(float(value) for value in self.counterparty_survival)
        if len(own) != len(times) or len(cp) != len(times):
            raise ValueError("Survival profiles must match the time grid.")
        for profile in (own, cp):
            if any(value < 0.0 or value > 1.0 for value in profile):
                raise ValueError("Survival probabilities must lie in [0, 1].")
            if any(right > left + 1e-12 for left, right in zip(profile, profile[1:])):
                raise ValueError("Survival probabilities must be non-increasing.")
        object.__setattr__(self, "times", times)
        object.__setattr__(self, "own_survival", own)
        object.__setattr__(self, "counterparty_survival", cp)


@dataclass(frozen=True)
class MVABucket:
    start_time: float
    end_time: float
    posted_cost: float
    received_benefit: float
    net_mva: float


@dataclass(frozen=True)
class MVAResult:
    netting_set_id: str
    currency: str
    posted_mva: float
    received_margin_benefit: float
    net_mva: float
    buckets: tuple[MVABucket, ...]
    policy_hash: str
    fva_embedded: bool = False
    proxy_label: str = PROXY_LABEL

    def __post_init__(self) -> None:
        if self.fva_embedded:
            raise ValueError("MVA must not be embedded in FVA.")
        if abs(self.net_mva - (self.posted_mva - self.received_margin_benefit)) > 1e-10:
            raise ValueError("MVA components do not reconcile.")
        if self.posted_mva < -1e-12 or self.received_margin_benefit < -1e-12:
            raise ValueError("MVA component magnitudes cannot be negative.")
        object.__setattr__(self, "currency", _currency(self.currency))


@dataclass(frozen=True)
class MVAAggregation:
    posted_mva: float
    received_margin_benefit: float
    net_mva: float
    by_netting_set: Mapping[str, float] = field(default_factory=dict)
    by_currency: Mapping[str, float] = field(default_factory=dict)
    bucket_net_mva: tuple[float, ...] = ()
    concentration_hhi: float = 0.0
    maximum_share: float = 0.0


@dataclass(frozen=True)
class MVAChallengeReport:
    status: str
    primary_net_mva: float
    challenger_net_mva: float
    absolute_difference: float
    relative_difference: float
    tolerance: float

    def __post_init__(self) -> None:
        if self.status not in {"PASS", "REMEDIATE"}:
            raise ValueError("Unsupported challenger status.")

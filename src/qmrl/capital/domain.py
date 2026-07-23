from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Sequence

import numpy as np


CAPITAL_BOUNDARY = "PUBLIC_CAPITAL_PROXY_NOT_REGULATORY_APPROVAL"


class IntegrationRule(str, Enum):
    ENDPOINT = "endpoint"
    TRAPEZOID = "trapezoid"


class SurvivalMode(str, Enum):
    COUNTERPARTY = "counterparty"
    NONE = "none"


@dataclass(frozen=True)
class BpsCurve:
    times: np.ndarray
    rates_bps: np.ndarray
    flat_extrapolation: bool = True

    def __post_init__(self) -> None:
        times = np.asarray(self.times, dtype=float)
        rates = np.asarray(self.rates_bps, dtype=float)
        if times.ndim != 1 or rates.ndim != 1 or len(times) != len(rates):
            raise ValueError("Curve times and rates must be one-dimensional and aligned.")
        if len(times) == 0 or np.any(~np.isfinite(times)) or np.any(~np.isfinite(rates)):
            raise ValueError("Curve values must be finite and non-empty.")
        if times[0] < 0.0 or np.any(np.diff(times) <= 0.0):
            raise ValueError("Curve times must be non-negative and strictly increasing.")
        if np.any(rates < 0.0):
            raise ValueError("Basis-point rates cannot be negative.")
        times = times.copy()
        rates = rates.copy()
        times.setflags(write=False)
        rates.setflags(write=False)
        object.__setattr__(self, "times", times)
        object.__setattr__(self, "rates_bps", rates)

    def values(self, query_times: Sequence[float] | np.ndarray) -> np.ndarray:
        query = np.asarray(query_times, dtype=float)
        if np.any(~np.isfinite(query)) or np.any(query < 0.0):
            raise ValueError("Curve query times must be finite and non-negative.")
        if not self.flat_extrapolation and (
            np.any(query < self.times[0]) or np.any(query > self.times[-1])
        ):
            raise ValueError("Curve extrapolation is forbidden by contract.")
        return np.interp(query, self.times, self.rates_bps)

    def shifted(self, delta_bps: float) -> "BpsCurve":
        shifted = self.rates_bps + float(delta_bps)
        if np.any(shifted < 0.0):
            raise ValueError("Shifted basis-point curve cannot be negative.")
        return BpsCurve(self.times, shifted, self.flat_extrapolation)


@dataclass(frozen=True)
class CapitalPolicy:
    ead_multiplier: float = 1.4
    risk_weight: float = 0.50
    capital_ratio: float = 0.08
    maturity_multiplier: float = 1.0
    stress_multiplier: float = 1.0
    integration_rule: IntegrationRule = IntegrationRule.TRAPEZOID
    survival_mode: SurvivalMode = SurvivalMode.COUNTERPARTY
    method: str = "transparent_public_capital_proxy"
    boundary: str = CAPITAL_BOUNDARY

    def __post_init__(self) -> None:
        numeric = {
            "ead_multiplier": self.ead_multiplier,
            "risk_weight": self.risk_weight,
            "capital_ratio": self.capital_ratio,
            "maturity_multiplier": self.maturity_multiplier,
            "stress_multiplier": self.stress_multiplier,
        }
        for name, value in numeric.items():
            if not np.isfinite(value) or value < 0.0:
                raise ValueError(f"{name} must be finite and non-negative.")
        if not self.method.strip():
            raise ValueError("Capital method must be named.")
        if self.boundary != CAPITAL_BOUNDARY:
            raise ValueError("Capital outputs must retain the public non-regulatory boundary.")


@dataclass(frozen=True)
class CapitalExposureInput:
    times: np.ndarray
    expected_exposure: np.ndarray
    counterparty_ids: tuple[str, ...]
    netting_set_ids: tuple[str, ...]
    currencies: tuple[str, ...]
    risk_weights: np.ndarray | None = None
    trade_ids: tuple[str, ...] = ()
    trade_netting_set_indices: tuple[int, ...] = ()
    trade_weights: np.ndarray = field(default_factory=lambda: np.empty(0, dtype=float))

    def __post_init__(self) -> None:
        times = np.asarray(self.times, dtype=float)
        exposure = np.asarray(self.expected_exposure, dtype=float)
        if times.ndim != 1 or len(times) < 2 or times[0] != 0.0 or np.any(np.diff(times) <= 0.0):
            raise ValueError("Capital times must start at zero and be strictly increasing.")
        if exposure.ndim != 2 or exposure.shape[1] != len(times):
            raise ValueError("Expected exposure must be netting-set by time.")
        if np.any(~np.isfinite(exposure)) or np.any(exposure < 0.0):
            raise ValueError("Expected exposure must be finite and non-negative.")
        n_sets = exposure.shape[0]
        if not (
            len(self.counterparty_ids) == len(self.netting_set_ids) == len(self.currencies) == n_sets
        ):
            raise ValueError("Netting-set metadata must align with exposure rows.")
        if len(set(self.netting_set_ids)) != n_sets:
            raise ValueError("Netting-set identifiers must be unique.")
        if any(not value.strip() for value in (*self.counterparty_ids, *self.netting_set_ids, *self.currencies)):
            raise ValueError("Capital metadata identifiers cannot be blank.")

        if self.risk_weights is None:
            risk_weights = np.full(n_sets, np.nan, dtype=float)
        else:
            risk_weights = np.asarray(self.risk_weights, dtype=float)
            if risk_weights.shape != (n_sets,) or np.any(~np.isfinite(risk_weights)) or np.any(risk_weights < 0.0):
                raise ValueError("Risk-weight overrides must be non-negative and align with netting sets.")

        trade_weights = np.asarray(self.trade_weights, dtype=float)
        if self.trade_ids:
            if not (
                len(self.trade_ids)
                == len(self.trade_netting_set_indices)
                == len(trade_weights)
            ):
                raise ValueError("Trade allocation metadata must align.")
            if len(set(self.trade_ids)) != len(self.trade_ids):
                raise ValueError("Trade identifiers must be unique.")
            if np.any(~np.isfinite(trade_weights)) or np.any(trade_weights < 0.0):
                raise ValueError("Trade allocation weights must be finite and non-negative.")
            indices = np.asarray(self.trade_netting_set_indices, dtype=int)
            if np.any(indices < 0) or np.any(indices >= n_sets):
                raise ValueError("Trade netting-set indices are out of range.")
            for set_index in range(n_sets):
                mask = indices == set_index
                if np.any(mask) and not np.isclose(float(trade_weights[mask].sum()), 1.0, atol=1e-12):
                    raise ValueError("Trade weights must sum to one within each represented netting set.")
        elif len(self.trade_netting_set_indices) or len(trade_weights):
            raise ValueError("Trade mappings cannot exist without trade identifiers.")

        times = times.copy()
        exposure = exposure.copy()
        risk_weights = risk_weights.copy()
        trade_weights = trade_weights.copy()
        for value in (times, exposure, risk_weights, trade_weights):
            value.setflags(write=False)
        object.__setattr__(self, "times", times)
        object.__setattr__(self, "expected_exposure", exposure)
        object.__setattr__(self, "risk_weights", risk_weights)
        object.__setattr__(self, "trade_weights", trade_weights)

    @property
    def netting_set_count(self) -> int:
        return self.expected_exposure.shape[0]


@dataclass(frozen=True)
class CapitalMarketState:
    times: np.ndarray
    discount_factors: np.ndarray
    counterparty_survival: np.ndarray

    def __post_init__(self) -> None:
        times = np.asarray(self.times, dtype=float)
        discount = np.asarray(self.discount_factors, dtype=float)
        survival = np.asarray(self.counterparty_survival, dtype=float)
        if times.ndim != 1 or discount.shape != times.shape or survival.shape != times.shape:
            raise ValueError("Market-state vectors must be one-dimensional and aligned.")
        if times[0] != 0.0 or np.any(np.diff(times) <= 0.0):
            raise ValueError("Market-state times must start at zero and increase.")
        if np.any(~np.isfinite(discount)) or np.any(discount <= 0.0) or np.any(np.diff(discount) > 1e-12):
            raise ValueError("Discount factors must be positive and non-increasing.")
        if np.any(~np.isfinite(survival)) or np.any((survival < 0.0) | (survival > 1.0)) or np.any(np.diff(survival) > 1e-12):
            raise ValueError("Survival probabilities must be in [0,1] and non-increasing.")
        if not np.isclose(discount[0], 1.0, atol=1e-12) or not np.isclose(survival[0], 1.0, atol=1e-12):
            raise ValueError("Discount and survival curves must equal one at time zero.")
        times = times.copy(); discount = discount.copy(); survival = survival.copy()
        for value in (times, discount, survival):
            value.setflags(write=False)
        object.__setattr__(self, "times", times)
        object.__setattr__(self, "discount_factors", discount)
        object.__setattr__(self, "counterparty_survival", survival)

    def shifted_discount_rate(self, delta_bps: float) -> "CapitalMarketState":
        shifted = self.discount_factors * np.exp(-float(delta_bps) / 10000.0 * self.times)
        shifted[0] = 1.0
        return CapitalMarketState(self.times, shifted, self.counterparty_survival)

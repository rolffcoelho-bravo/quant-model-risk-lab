"""Governed volatility and monitoring contracts for the FX option layer."""

from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_CONTRACT_PATH = (
    REPO_ROOT
    / "configs"
    / "fx_option_governance_contract.json"
)


@dataclass(frozen=True)
class VolatilityEstimationPolicy:
    annualisation_observations: int
    lookback_observations: int
    minimum_return_observations: int
    fallback_volatility: float
    lower_bound: float
    upper_bound: float


@dataclass(frozen=True)
class VolatilitySurfacePolicy:
    absolute_floor: float
    floor_status: str


@dataclass(frozen=True)
class MonitoringPolicy:
    spot_move_relative_threshold: float
    realised_volatility_change_absolute_threshold: float
    domestic_rate_change_absolute_threshold: float
    foreign_rate_change_absolute_threshold: float
    parity_relative_gap_threshold: float
    monitor_delta_sign_change: bool
    monitor_vega_sign_change: bool
    model_owner: str
    validation_owner: str
    escalation_owner: str
    review_frequency: str
    alert_artifact: str
    revalidation_status_on_breach: str


@dataclass(frozen=True)
class ModelBoundaries:
    production_approval: bool
    market_quote_benchmark: str
    threshold_scope: str
    external_alert_delivery: str


@dataclass(frozen=True)
class FXOptionGovernanceContract:
    contract_id: str
    contract_status: str
    volatility_estimation: VolatilityEstimationPolicy
    volatility_surface: VolatilitySurfacePolicy
    monitoring: MonitoringPolicy
    model_boundaries: ModelBoundaries


@dataclass(frozen=True)
class VolatilityEstimate:
    volatility: float
    raw_volatility: float | None
    return_observations: int
    observations_used: int
    estimation_status: str
    lower_bound_applied: bool
    upper_bound_applied: bool


def load_fx_option_governance_contract(
    path: str | Path | None = None,
) -> FXOptionGovernanceContract:
    """Load and validate the governed FX-option contract."""
    contract_path = (
        Path(path)
        if path is not None
        else DEFAULT_CONTRACT_PATH
    )

    payload = json.loads(
        contract_path.read_text(
            encoding="utf-8-sig"
        )
    )

    volatility = payload["volatility_estimation"]
    surface = payload["volatility_surface"]
    monitoring = payload["monitoring"]
    boundaries = payload["model_boundaries"]

    contract = FXOptionGovernanceContract(
        contract_id=str(payload["contract_id"]),
        contract_status=str(
            payload["contract_status"]
        ),
        volatility_estimation=VolatilityEstimationPolicy(
            annualisation_observations=int(
                volatility[
                    "annualisation_observations"
                ]
            ),
            lookback_observations=int(
                volatility["lookback_observations"]
            ),
            minimum_return_observations=int(
                volatility[
                    "minimum_return_observations"
                ]
            ),
            fallback_volatility=float(
                volatility["fallback_volatility"]
            ),
            lower_bound=float(
                volatility["lower_bound"]
            ),
            upper_bound=float(
                volatility["upper_bound"]
            ),
        ),
        volatility_surface=VolatilitySurfacePolicy(
            absolute_floor=float(
                surface["absolute_floor"]
            ),
            floor_status=str(
                surface["floor_status"]
            ),
        ),
        monitoring=MonitoringPolicy(
            spot_move_relative_threshold=float(
                monitoring[
                    "spot_move_relative_threshold"
                ]
            ),
            realised_volatility_change_absolute_threshold=float(
                monitoring[
                    "realised_volatility_change_absolute_threshold"
                ]
            ),
            domestic_rate_change_absolute_threshold=float(
                monitoring[
                    "domestic_rate_change_absolute_threshold"
                ]
            ),
            foreign_rate_change_absolute_threshold=float(
                monitoring[
                    "foreign_rate_change_absolute_threshold"
                ]
            ),
            parity_relative_gap_threshold=float(
                monitoring[
                    "parity_relative_gap_threshold"
                ]
            ),
            monitor_delta_sign_change=bool(
                monitoring[
                    "monitor_delta_sign_change"
                ]
            ),
            monitor_vega_sign_change=bool(
                monitoring[
                    "monitor_vega_sign_change"
                ]
            ),
            model_owner=str(
                monitoring["model_owner"]
            ),
            validation_owner=str(
                monitoring["validation_owner"]
            ),
            escalation_owner=str(
                monitoring["escalation_owner"]
            ),
            review_frequency=str(
                monitoring["review_frequency"]
            ),
            alert_artifact=str(
                monitoring["alert_artifact"]
            ),
            revalidation_status_on_breach=str(
                monitoring[
                    "revalidation_status_on_breach"
                ]
            ),
        ),
        model_boundaries=ModelBoundaries(
            production_approval=bool(
                boundaries["production_approval"]
            ),
            market_quote_benchmark=str(
                boundaries[
                    "market_quote_benchmark"
                ]
            ),
            threshold_scope=str(
                boundaries["threshold_scope"]
            ),
            external_alert_delivery=str(
                boundaries[
                    "external_alert_delivery"
                ]
            ),
        ),
    )

    validate_contract(contract)
    return contract


def validate_contract(
    contract: FXOptionGovernanceContract,
) -> None:
    """Fail closed for invalid or internally inconsistent controls."""
    policy = contract.volatility_estimation

    if policy.annualisation_observations <= 0:
        raise ValueError(
            "Annualisation observations must be positive."
        )

    if policy.lookback_observations <= 1:
        raise ValueError(
            "The volatility lookback must exceed one observation."
        )

    if policy.minimum_return_observations <= 1:
        raise ValueError(
            "Minimum return observations must exceed one."
        )

    if (
        policy.minimum_return_observations
        > policy.lookback_observations
    ):
        raise ValueError(
            "Minimum observations cannot exceed the lookback."
        )

    if not (
        0.0
        < policy.lower_bound
        <= policy.fallback_volatility
        <= policy.upper_bound
        < 2.0
    ):
        raise ValueError(
            "The volatility fallback and bounds are inconsistent."
        )

    floor = contract.volatility_surface.absolute_floor

    if not 0.0 < floor <= policy.lower_bound:
        raise ValueError(
            "The surface floor must be positive and no greater "
            "than the estimator lower bound."
        )

    monitoring = contract.monitoring

    thresholds = [
        monitoring.spot_move_relative_threshold,
        monitoring.realised_volatility_change_absolute_threshold,
        monitoring.domestic_rate_change_absolute_threshold,
        monitoring.foreign_rate_change_absolute_threshold,
        monitoring.parity_relative_gap_threshold,
    ]

    if any(value <= 0.0 for value in thresholds):
        raise ValueError(
            "Every monitoring threshold must be positive."
        )

    if contract.model_boundaries.production_approval:
        raise ValueError(
            "This public validation contract cannot grant "
            "production approval."
        )


def estimate_realised_volatility(
    levels: Iterable[float] | pd.Series,
    policy: VolatilityEstimationPolicy,
) -> VolatilityEstimate:
    """Estimate annualised volatility under the governed policy."""
    series = pd.to_numeric(
        pd.Series(levels, dtype="float64"),
        errors="coerce",
    )

    series = series[
        np.isfinite(series)
        & (series > 0.0)
    ]

    log_returns = np.log(series).diff().dropna()
    return_count = int(len(log_returns))

    if return_count < policy.minimum_return_observations:
        return VolatilityEstimate(
            volatility=policy.fallback_volatility,
            raw_volatility=None,
            return_observations=return_count,
            observations_used=return_count,
            estimation_status=(
                "FALLBACK_INSUFFICIENT_OBSERVATIONS"
            ),
            lower_bound_applied=False,
            upper_bound_applied=False,
        )

    selected = log_returns.tail(
        policy.lookback_observations
    )

    raw = float(
        selected.std(ddof=1)
        * math.sqrt(
            policy.annualisation_observations
        )
    )

    if not math.isfinite(raw):
        raise ValueError(
            "The realised-volatility estimate is not finite."
        )

    bounded = min(
        max(raw, policy.lower_bound),
        policy.upper_bound,
    )

    return VolatilityEstimate(
        volatility=float(bounded),
        raw_volatility=raw,
        return_observations=return_count,
        observations_used=int(len(selected)),
        estimation_status="ESTIMATED_AND_BOUNDED",
        lower_bound_applied=raw < policy.lower_bound,
        upper_bound_applied=raw > policy.upper_bound,
    )


def governed_realised_volatility(
    levels: Iterable[float] | pd.Series,
    contract: FXOptionGovernanceContract | None = None,
) -> float:
    """Return the governed annualised volatility value."""
    effective_contract = (
        contract
        if contract is not None
        else load_fx_option_governance_contract()
    )

    return estimate_realised_volatility(
        levels,
        effective_contract.volatility_estimation,
    ).volatility


def apply_volatility_floor(
    volatility: float,
    contract: FXOptionGovernanceContract | None = None,
) -> float:
    """Apply the governed numerical floor to a volatility input."""
    effective_contract = (
        contract
        if contract is not None
        else load_fx_option_governance_contract()
    )

    value = float(volatility)

    if not math.isfinite(value):
        raise ValueError(
            "Volatility must be finite."
        )

    return max(
        value,
        effective_contract.volatility_surface.absolute_floor,
    )
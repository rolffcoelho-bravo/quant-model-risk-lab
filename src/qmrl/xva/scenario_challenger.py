"""Analytical moment challengers for simulated market factors."""

from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np

from .risk_factors import (
    RiskFactorSet,
)
from .scenario_paths import (
    ScenarioCube,
)


@dataclass(frozen=True)
class AnalyticalMomentCheck:
    """Terminal simulated moments compared with analytical moments."""

    factor_name: str
    model: str
    horizon: float
    sample_mean: float
    analytical_mean: float
    sample_variance: float
    analytical_variance: float
    mean_relative_error: float
    variance_relative_error: float


def gbm_moments(
    *,
    initial_value: float,
    drift: float,
    volatility: float,
    horizon: float,
) -> tuple[float, float]:
    """Return exact GBM mean and variance."""

    if initial_value <= 0.0:
        raise ValueError(
            "initial_value must be positive."
        )

    if volatility < 0.0:
        raise ValueError(
            "volatility must be non-negative."
        )

    if horizon < 0.0:
        raise ValueError(
            "horizon must be non-negative."
        )

    mean = (
        initial_value
        * math.exp(drift * horizon)
    )

    variance = (
        initial_value
        * initial_value
        * math.exp(2.0 * drift * horizon)
        * (
            math.exp(
                volatility
                * volatility
                * horizon
            )
            - 1.0
        )
    )

    return float(mean), float(variance)


def vasicek_moments(
    *,
    initial_value: float,
    mean_reversion: float,
    long_run_mean: float,
    volatility: float,
    horizon: float,
    drift_when_zero_reversion: float = 0.0,
) -> tuple[float, float]:
    """Return exact Vasicek moments or additive-normal limiting moments."""

    if mean_reversion < 0.0:
        raise ValueError(
            "mean_reversion must be non-negative."
        )

    if volatility < 0.0:
        raise ValueError(
            "volatility must be non-negative."
        )

    if horizon < 0.0:
        raise ValueError(
            "horizon must be non-negative."
        )

    if mean_reversion > 1e-14:
        decay = math.exp(
            -mean_reversion * horizon
        )
        mean = (
            long_run_mean
            + (
                initial_value
                - long_run_mean
            )
            * decay
        )
        variance = (
            volatility
            * volatility
            * (
                1.0
                - math.exp(
                    -2.0
                    * mean_reversion
                    * horizon
                )
            )
            / (2.0 * mean_reversion)
        )
    else:
        mean = (
            initial_value
            + drift_when_zero_reversion
            * horizon
        )
        variance = (
            volatility
            * volatility
            * horizon
        )

    return float(mean), float(variance)


def _relative_error(
    actual: float,
    expected: float,
) -> float:
    scale = max(
        abs(expected),
        1e-12,
    )
    return abs(actual - expected) / scale


def compare_terminal_moments(
    cube: ScenarioCube,
    factor_set: RiskFactorSet,
    factor_name: str,
) -> AnalyticalMomentCheck:
    """Compare terminal path moments with the model's analytical moments."""

    factor_map = {
        factor.name: factor
        for factor in factor_set.factors
    }

    if factor_name not in factor_map:
        raise KeyError(
            f"Unknown risk factor: {factor_name}"
        )

    factor = factor_map[factor_name]
    terminal = cube.factor_values(
        factor_name
    )[:, -1]
    horizon = float(cube.times[-1])

    if factor.model == "gbm_fx":
        analytical_mean, analytical_variance = (
            gbm_moments(
                initial_value=factor.initial_value,
                drift=factor.drift,
                volatility=factor.volatility,
                horizon=horizon,
            )
        )
    elif factor.model == "vasicek_rate":
        analytical_mean, analytical_variance = (
            vasicek_moments(
                initial_value=factor.initial_value,
                mean_reversion=factor.mean_reversion,
                long_run_mean=factor.long_run_mean,
                volatility=factor.volatility,
                horizon=horizon,
                drift_when_zero_reversion=(
                    factor.drift
                ),
            )
        )
    elif factor.model == "deterministic":
        analytical_mean = (
            factor.initial_value
            + factor.drift
            * horizon
        )
        analytical_variance = 0.0
    else:
        raise ValueError(
            f"No challenger for model {factor.model}"
        )

    sample_mean = float(
        np.mean(terminal)
    )
    sample_variance = float(
        np.var(
            terminal,
            ddof=0,
        )
    )

    return AnalyticalMomentCheck(
        factor_name=factor.name,
        model=factor.model,
        horizon=horizon,
        sample_mean=sample_mean,
        analytical_mean=analytical_mean,
        sample_variance=sample_variance,
        analytical_variance=analytical_variance,
        mean_relative_error=_relative_error(
            sample_mean,
            analytical_mean,
        ),
        variance_relative_error=(
            0.0
            if analytical_variance == 0.0
            and sample_variance == 0.0
            else _relative_error(
                sample_variance,
                analytical_variance,
            )
        ),
    )

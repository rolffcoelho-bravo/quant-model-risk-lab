"""Governed market-risk-factor definitions and dependence controls."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


_SUPPORTED_MODELS = {
    "gbm_fx",
    "vasicek_rate",
    "deterministic",
}


@dataclass(frozen=True)
class RiskFactorSpec:
    """One market factor used by the Gate 2 scenario engine."""

    name: str
    factor_type: str
    model: str
    initial_value: float
    drift: float = 0.0
    volatility: float = 0.0
    mean_reversion: float = 0.0
    long_run_mean: float = 0.0
    currency: str | None = None

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("name must not be empty.")

        if not self.factor_type.strip():
            raise ValueError(
                "factor_type must not be empty."
            )

        if self.model not in _SUPPORTED_MODELS:
            raise ValueError(
                f"Unsupported factor model: {self.model}"
            )

        values = (
            self.initial_value,
            self.drift,
            self.volatility,
            self.mean_reversion,
            self.long_run_mean,
        )

        if not np.isfinite(values).all():
            raise ValueError(
                "Risk-factor parameters must be finite."
            )

        if self.volatility < 0.0:
            raise ValueError(
                "volatility must be non-negative."
            )

        if self.mean_reversion < 0.0:
            raise ValueError(
                "mean_reversion must be non-negative."
            )

        if (
            self.model == "gbm_fx"
            and self.initial_value <= 0.0
        ):
            raise ValueError(
                "gbm_fx initial_value must be positive."
            )

        if (
            self.currency is not None
            and len(self.currency.strip()) != 3
        ):
            raise ValueError(
                "currency must be a three-letter code."
            )


def validate_correlation_matrix(
    matrix: np.ndarray,
    *,
    tolerance: float = 1e-10,
) -> np.ndarray:
    """Validate and return an immutable correlation matrix."""

    correlation = np.asarray(
        matrix,
        dtype=float,
    )

    if correlation.ndim != 2:
        raise ValueError(
            "correlation matrix must be two-dimensional."
        )

    rows, columns = correlation.shape

    if rows == 0 or rows != columns:
        raise ValueError(
            "correlation matrix must be non-empty and square."
        )

    if not np.isfinite(correlation).all():
        raise ValueError(
            "correlation matrix must be finite."
        )

    if not np.allclose(
        correlation,
        correlation.T,
        atol=tolerance,
        rtol=0.0,
    ):
        raise ValueError(
            "correlation matrix must be symmetric."
        )

    if not np.allclose(
        np.diag(correlation),
        np.ones(rows),
        atol=tolerance,
        rtol=0.0,
    ):
        raise ValueError(
            "correlation matrix diagonal must equal one."
        )

    if np.any(
        correlation < -1.0 - tolerance
    ) or np.any(
        correlation > 1.0 + tolerance
    ):
        raise ValueError(
            "correlations must lie in [-1, 1]."
        )

    minimum_eigenvalue = float(
        np.min(
            np.linalg.eigvalsh(correlation)
        )
    )

    if minimum_eigenvalue < -tolerance:
        raise ValueError(
            "correlation matrix must be positive semidefinite."
        )

    result = correlation.copy()
    result.setflags(write=False)
    return result


@dataclass(frozen=True)
class RiskFactorSet:
    """Ordered risk factors and their governed correlation matrix."""

    factors: tuple[RiskFactorSpec, ...]
    correlation: np.ndarray
    calibration_source: str = "public_validation_parameters"
    calibration_as_of: str | None = None

    def __post_init__(self) -> None:
        if not self.factors:
            raise ValueError(
                "At least one risk factor is required."
            )

        names = tuple(
            factor.name
            for factor in self.factors
        )

        if len(names) != len(set(names)):
            raise ValueError(
                "Risk-factor names must be unique."
            )

        correlation = validate_correlation_matrix(
            self.correlation
        )

        if correlation.shape != (
            len(self.factors),
            len(self.factors),
        ):
            raise ValueError(
                "Correlation dimension must match factors."
            )

        if not self.calibration_source.strip():
            raise ValueError(
                "calibration_source must not be empty."
            )

        object.__setattr__(
            self,
            "correlation",
            correlation,
        )

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(
            factor.name
            for factor in self.factors
        )

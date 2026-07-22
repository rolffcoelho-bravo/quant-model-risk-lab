"""Exposure profiles and deterministic Gate 1 aggregation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class ExposureProfile:
    """Clean, collateral, and resulting signed exposure arrays."""

    clean_values: np.ndarray
    collateral_values: np.ndarray
    net_values: np.ndarray
    positive_exposure: np.ndarray
    negative_exposure: np.ndarray


@dataclass(frozen=True)
class ExposureStatistics:
    """Time-profile and portfolio-level exposure statistics."""

    expected_positive_profile: np.ndarray
    expected_negative_profile: np.ndarray
    pfe_profile: np.ndarray
    effective_epe_profile: np.ndarray
    epe: float
    ene: float
    peak_pfe: float
    discounted_epe: float
    quantile: float


def _finite_array(
    values: Sequence[float] | np.ndarray,
    name: str,
) -> np.ndarray:
    array = np.asarray(values, dtype=float)

    if not np.isfinite(array).all():
        raise ValueError(f"{name} must contain finite values.")

    return array


def collateralized_exposure(
    clean_values: Sequence[float] | np.ndarray,
    collateral_values: Sequence[float] | np.ndarray,
) -> ExposureProfile:
    """Compute positive and negative exposure after collateral."""

    clean = _finite_array(
        clean_values,
        "clean_values",
    )

    collateral = _finite_array(
        collateral_values,
        "collateral_values",
    )

    if clean.shape != collateral.shape:
        raise ValueError(
            "clean_values and collateral_values "
            "must have the same shape."
        )

    net = clean - collateral

    return ExposureProfile(
        clean_values=clean,
        collateral_values=collateral,
        net_values=net,
        positive_exposure=np.maximum(net, 0.0),
        negative_exposure=np.maximum(-net, 0.0),
    )


def margin_period_of_risk_exposure(
    clean_values: Sequence[float] | np.ndarray,
    collateral_values: Sequence[float] | np.ndarray,
    *,
    mpor_steps: int,
) -> ExposureProfile:
    """Apply a discrete future-value MPOR view against current collateral."""

    if mpor_steps < 0:
        raise ValueError(
            "mpor_steps must be non-negative."
        )

    clean = _finite_array(
        clean_values,
        "clean_values",
    )

    collateral = _finite_array(
        collateral_values,
        "collateral_values",
    )

    if clean.ndim != 1 or collateral.ndim != 1:
        raise ValueError(
            "MPOR exposure requires one-dimensional paths."
        )

    if clean.shape != collateral.shape:
        raise ValueError(
            "clean_values and collateral_values "
            "must have the same shape."
        )

    future_clean = np.empty_like(clean)

    for index in range(clean.size):
        future_index = min(
            index + mpor_steps,
            clean.size - 1,
        )
        future_clean[index] = clean[future_index]

    return collateralized_exposure(
        future_clean,
        collateral,
    )


def _as_path_matrix(
    values: Sequence[float] | np.ndarray,
    name: str,
) -> np.ndarray:
    array = _finite_array(values, name)

    if array.ndim == 1:
        return array.reshape(1, -1)

    if array.ndim != 2:
        raise ValueError(
            f"{name} must be one- or two-dimensional."
        )

    return array


def _time_average(
    profile: np.ndarray,
    times: np.ndarray,
) -> float:
    if profile.size == 1:
        return float(profile[0])

    horizon = float(times[-1] - times[0])

    if horizon <= 0.0:
        raise ValueError(
            "times must be strictly increasing."
        )

    increments = np.diff(times)

    if np.any(increments <= 0.0):
        raise ValueError(
            "times must be strictly increasing."
        )

    area = np.sum(
        0.5
        * (
            profile[:-1]
            + profile[1:]
        )
        * increments
    )

    return float(area / horizon)


def exposure_statistics(
    clean_value_paths: Sequence[float] | np.ndarray,
    *,
    collateral_paths: (
        Sequence[float]
        | np.ndarray
        | None
    ) = None,
    quantile: float = 0.95,
    times: Sequence[float] | np.ndarray | None = None,
    discount_factors: (
        Sequence[float]
        | np.ndarray
        | None
    ) = None,
) -> ExposureStatistics:
    """Aggregate EPE, ENE, PFE, effective EPE, and discounted EPE."""

    if not 0.0 < quantile < 1.0:
        raise ValueError(
            "quantile must be strictly between 0 and 1."
        )

    clean = _as_path_matrix(
        clean_value_paths,
        "clean_value_paths",
    )

    if collateral_paths is None:
        collateral = np.zeros_like(clean)
    else:
        collateral = _as_path_matrix(
            collateral_paths,
            "collateral_paths",
        )

        if collateral.shape != clean.shape:
            raise ValueError(
                "collateral_paths must match "
                "clean_value_paths."
            )

    net = clean - collateral
    positive = np.maximum(net, 0.0)
    negative = np.maximum(-net, 0.0)

    expected_positive = np.mean(
        positive,
        axis=0,
    )

    expected_negative = np.mean(
        negative,
        axis=0,
    )

    pfe = np.quantile(
        positive,
        quantile,
        axis=0,
    )

    effective_epe = np.maximum.accumulate(
        expected_positive
    )

    if times is None:
        time_array = np.arange(
            clean.shape[1],
            dtype=float,
        )
    else:
        time_array = _finite_array(
            times,
            "times",
        )

        if time_array.ndim != 1:
            raise ValueError(
                "times must be one-dimensional."
            )

        if time_array.size != clean.shape[1]:
            raise ValueError(
                "times must match the path time dimension."
            )

    epe = _time_average(
        expected_positive,
        time_array,
    )

    ene = _time_average(
        expected_negative,
        time_array,
    )

    if discount_factors is None:
        discount = np.ones(
            clean.shape[1],
            dtype=float,
        )
    else:
        discount = _finite_array(
            discount_factors,
            "discount_factors",
        )

        if discount.ndim != 1:
            raise ValueError(
                "discount_factors must be one-dimensional."
            )

        if discount.size != clean.shape[1]:
            raise ValueError(
                "discount_factors must match "
                "the path time dimension."
            )

        if np.any(discount < 0.0):
            raise ValueError(
                "discount_factors must be non-negative."
            )

    discounted_epe = _time_average(
        expected_positive * discount,
        time_array,
    )

    return ExposureStatistics(
        expected_positive_profile=expected_positive,
        expected_negative_profile=expected_negative,
        pfe_profile=pfe,
        effective_epe_profile=effective_epe,
        epe=epe,
        ene=ene,
        peak_pfe=float(np.max(pfe)),
        discounted_epe=discounted_epe,
        quantile=float(quantile),
    )

"""Monte Carlo convergence diagnostics for future-value simulation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class ConvergenceDiagnostics:
    """Running means, errors, and a transparent stability decision."""

    sample_sizes: np.ndarray
    estimates: np.ndarray
    standard_errors: np.ndarray
    confidence_half_widths: np.ndarray
    final_estimate: float
    final_standard_error: float
    stable: bool
    relative_tolerance: float
    absolute_tolerance: float
    confidence_z: float


def convergence_diagnostics(
    samples: Sequence[float] | np.ndarray,
    *,
    sample_sizes: Sequence[int] | None = None,
    relative_tolerance: float = 0.02,
    absolute_tolerance: float = 1e-8,
    confidence_z: float = 1.96,
) -> ConvergenceDiagnostics:
    """Evaluate estimator uncertainty across governed sample sizes."""

    values = np.asarray(
        samples,
        dtype=float,
    )

    if values.ndim != 1 or values.size < 2:
        raise ValueError(
            "samples must contain at least two observations."
        )

    if not np.isfinite(values).all():
        raise ValueError(
            "samples must be finite."
        )

    if relative_tolerance < 0.0:
        raise ValueError(
            "relative_tolerance must be non-negative."
        )

    if absolute_tolerance < 0.0:
        raise ValueError(
            "absolute_tolerance must be non-negative."
        )

    if confidence_z <= 0.0:
        raise ValueError(
            "confidence_z must be positive."
        )

    if sample_sizes is None:
        proposed = {
            2,
            min(10, values.size),
            min(100, values.size),
            min(1000, values.size),
            values.size,
        }
        sizes = np.array(
            sorted(proposed),
            dtype=int,
        )
    else:
        sizes = np.asarray(
            sample_sizes,
            dtype=int,
        )

        if sizes.ndim != 1 or sizes.size == 0:
            raise ValueError(
                "sample_sizes must be one-dimensional."
            )

        if np.any(sizes < 2):
            raise ValueError(
                "sample_sizes must be at least two."
            )

        if np.any(np.diff(sizes) <= 0):
            raise ValueError(
                "sample_sizes must be strictly increasing."
            )

        if sizes[-1] > values.size:
            raise ValueError(
                "sample_sizes cannot exceed samples."
            )

    estimates = np.empty(
        sizes.size,
        dtype=float,
    )
    standard_errors = np.empty_like(
        estimates
    )

    for index, size in enumerate(sizes):
        subset = values[: int(size)]
        estimates[index] = np.mean(subset)
        standard_errors[index] = (
            np.std(
                subset,
                ddof=1,
            )
            / np.sqrt(size)
        )

    half_widths = (
        confidence_z
        * standard_errors
    )

    final_estimate = float(
        estimates[-1]
    )
    final_standard_error = float(
        standard_errors[-1]
    )

    allowed = (
        absolute_tolerance
        + relative_tolerance
        * abs(final_estimate)
    )

    stable = bool(
        half_widths[-1] <= allowed
    )

    for array in (
        sizes,
        estimates,
        standard_errors,
        half_widths,
    ):
        array.setflags(write=False)

    return ConvergenceDiagnostics(
        sample_sizes=sizes,
        estimates=estimates,
        standard_errors=standard_errors,
        confidence_half_widths=half_widths,
        final_estimate=final_estimate,
        final_standard_error=final_standard_error,
        stable=stable,
        relative_tolerance=float(
            relative_tolerance
        ),
        absolute_tolerance=float(
            absolute_tolerance
        ),
        confidence_z=float(confidence_z),
    )

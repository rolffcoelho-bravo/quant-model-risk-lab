"""Convergence, stability, and model-risk diagnostics for XVA Gate 7."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping, Sequence

import numpy as np


_STATUSES = {
    "PASS",
    "PASS_WITH_MONITORING",
    "REMEDIATE",
    "BLOCK",
}


def _array(values: Sequence[float] | np.ndarray, name: str) -> np.ndarray:
    result = np.asarray(values, dtype=float)
    if result.ndim != 1 or result.size == 0:
        raise ValueError(f"{name} must be a non-empty one-dimensional sequence.")
    if not np.isfinite(result).all():
        raise ValueError(f"{name} must contain finite values.")
    return result


@dataclass(frozen=True)
class StabilityThresholds:
    """Soft and hard stability thresholds."""

    soft_relative_change: float
    hard_relative_change: float
    soft_coefficient_of_variation: float
    hard_coefficient_of_variation: float
    minimum_observations: int = 3

    def __post_init__(self) -> None:
        for name in (
            "soft_relative_change",
            "hard_relative_change",
            "soft_coefficient_of_variation",
            "hard_coefficient_of_variation",
        ):
            value = float(getattr(self, name))
            if not math.isfinite(value) or value < 0.0:
                raise ValueError(f"{name} must be finite and non-negative.")
            object.__setattr__(self, name, value)
        if self.soft_relative_change > self.hard_relative_change:
            raise ValueError("soft_relative_change must not exceed hard_relative_change.")
        if self.soft_coefficient_of_variation > self.hard_coefficient_of_variation:
            raise ValueError("soft coefficient-of-variation threshold must not exceed hard threshold.")
        if self.minimum_observations < 2:
            raise ValueError("minimum_observations must be at least two.")


@dataclass(frozen=True)
class StabilityAssessment:
    """One convergence or stability assessment."""

    diagnostic: str
    baseline: float
    final_value: float
    worst_relative_change: float
    coefficient_of_variation: float
    monotonicity_violations: int
    observations: int
    status: str
    reason: str

    def __post_init__(self) -> None:
        if not self.diagnostic.strip():
            raise ValueError("diagnostic must not be empty.")
        if self.status not in _STATUSES:
            raise ValueError("Unsupported stability status.")
        if not self.reason.strip():
            raise ValueError("reason must not be empty.")


def assess_stability(
    diagnostic: str,
    estimates: Sequence[float] | np.ndarray,
    thresholds: StabilityThresholds,
    *,
    expect_monotone_error_reduction: bool = False,
) -> StabilityAssessment:
    """Assess seed, path-count, grid, or parameter stability."""

    values = _array(estimates, "estimates")
    if values.size < thresholds.minimum_observations:
        return StabilityAssessment(
            diagnostic=diagnostic,
            baseline=float(values[0]),
            final_value=float(values[-1]),
            worst_relative_change=float("inf"),
            coefficient_of_variation=float("inf"),
            monotonicity_violations=0,
            observations=int(values.size),
            status="BLOCK",
            reason="Insufficient observations for the governed stability assessment.",
        )

    scale = max(abs(float(values[-1])), float(np.mean(np.abs(values))), 1e-15)
    relative_changes = np.abs(np.diff(values)) / np.maximum(np.abs(values[1:]), scale * 1e-12)
    worst_relative = float(np.max(relative_changes)) if relative_changes.size else 0.0
    mean_abs = max(abs(float(np.mean(values))), 1e-15)
    coefficient = float(np.std(values, ddof=0) / mean_abs)

    violations = 0
    if expect_monotone_error_reduction and values.size >= 3:
        terminal = float(values[-1])
        errors = np.abs(values - terminal)
        violations = int(np.sum(np.diff(errors[:-1]) > 1e-15))

    if worst_relative <= thresholds.soft_relative_change and coefficient <= thresholds.soft_coefficient_of_variation and violations == 0:
        status = "PASS"
        reason = "The diagnostic remains within soft stability thresholds."
    elif worst_relative <= thresholds.hard_relative_change and coefficient <= thresholds.hard_coefficient_of_variation and violations <= 1:
        status = "PASS_WITH_MONITORING"
        reason = "The diagnostic remains inside hard limits but requires monitoring."
    elif worst_relative <= thresholds.hard_relative_change * 2.0 and coefficient <= thresholds.hard_coefficient_of_variation * 2.0:
        status = "REMEDIATE"
        reason = "The diagnostic is unstable relative to the governed hard target and requires remediation evidence."
    else:
        status = "BLOCK"
        reason = "The diagnostic breaches the maximum stability boundary."

    return StabilityAssessment(
        diagnostic=diagnostic,
        baseline=float(values[0]),
        final_value=float(values[-1]),
        worst_relative_change=worst_relative,
        coefficient_of_variation=coefficient,
        monotonicity_violations=violations,
        observations=int(values.size),
        status=status,
        reason=reason,
    )


def path_count_convergence(
    path_counts: Sequence[int],
    estimates: Sequence[float] | np.ndarray,
    thresholds: StabilityThresholds,
) -> StabilityAssessment:
    """Assess path-count convergence using increasing simulation sizes."""

    counts = np.asarray(path_counts, dtype=int)
    if counts.ndim != 1 or counts.size == 0 or np.any(counts <= 0):
        raise ValueError("path_counts must be a non-empty positive sequence.")
    if np.any(np.diff(counts) <= 0):
        raise ValueError("path_counts must be strictly increasing.")
    if counts.size != len(estimates):
        raise ValueError("path_counts and estimates must align.")
    return assess_stability(
        "path_count_convergence",
        estimates,
        thresholds,
        expect_monotone_error_reduction=True,
    )


def seed_stability(
    estimates: Sequence[float] | np.ndarray,
    thresholds: StabilityThresholds,
) -> StabilityAssessment:
    """Assess repeated estimates across governed random seeds."""

    return assess_stability("seed_stability", estimates, thresholds)


def time_grid_refinement(
    grid_steps: Sequence[float],
    estimates: Sequence[float] | np.ndarray,
    thresholds: StabilityThresholds,
) -> StabilityAssessment:
    """Assess estimates as the time-grid step is refined."""

    steps = _array(grid_steps, "grid_steps")
    if np.any(steps <= 0.0) or np.any(np.diff(steps) >= 0.0):
        raise ValueError("grid_steps must be positive and strictly decreasing.")
    if steps.size != len(estimates):
        raise ValueError("grid_steps and estimates must align.")
    return assess_stability(
        "time_grid_refinement",
        estimates,
        thresholds,
        expect_monotone_error_reduction=True,
    )


def antithetic_comparison(
    standard_estimates: Sequence[float],
    antithetic_estimates: Sequence[float],
) -> dict[str, float | str]:
    """Compare standard and antithetic estimator dispersion."""

    standard = _array(standard_estimates, "standard_estimates")
    antithetic = _array(antithetic_estimates, "antithetic_estimates")
    if standard.size != antithetic.size:
        raise ValueError("Estimator samples must have equal length.")
    standard_variance = float(np.var(standard, ddof=1)) if standard.size > 1 else 0.0
    antithetic_variance = float(np.var(antithetic, ddof=1)) if antithetic.size > 1 else 0.0
    ratio = antithetic_variance / max(standard_variance, 1e-15)
    status = "PASS" if ratio <= 1.0 else "PASS_WITH_MONITORING" if ratio <= 1.25 else "REMEDIATE"
    return {
        "standard_variance": standard_variance,
        "antithetic_variance": antithetic_variance,
        "variance_ratio": float(ratio),
        "status": status,
    }


def rank_sensitivity_drivers(sensitivities: Mapping[str, float]) -> tuple[tuple[str, float], ...]:
    """Rank absolute XVA sensitivities from largest to smallest."""

    cleaned: list[tuple[str, float]] = []
    for name, value in sensitivities.items():
        if not str(name).strip():
            raise ValueError("Sensitivity names must not be empty.")
        number = float(value)
        if not math.isfinite(number):
            raise ValueError("Sensitivities must be finite.")
        cleaned.append((str(name), number))
    return tuple(sorted(cleaned, key=lambda item: (-abs(item[1]), item[0])))


def detect_threshold_discontinuity(
    parameter_values: Sequence[float],
    xva_values: Sequence[float],
    *,
    jump_ratio_threshold: float,
) -> tuple[int, ...]:
    """Flag unusually large adjacent jumps around CSA thresholds or MTA."""

    parameters = _array(parameter_values, "parameter_values")
    values = _array(xva_values, "xva_values")
    if parameters.size != values.size or parameters.size < 3:
        raise ValueError("At least three aligned parameter and XVA observations are required.")
    if np.any(np.diff(parameters) <= 0.0):
        raise ValueError("parameter_values must be strictly increasing.")
    threshold = float(jump_ratio_threshold)
    if not math.isfinite(threshold) or threshold <= 1.0:
        raise ValueError("jump_ratio_threshold must exceed one.")

    jumps = np.abs(np.diff(values))
    typical = float(np.median(jumps))
    if typical <= 1e-15:
        return tuple(int(index) for index, jump in enumerate(jumps) if jump > 1e-15)
    return tuple(int(index) for index, jump in enumerate(jumps) if jump / typical > threshold)


def benchmark_drift_score(
    current: Sequence[float],
    locked: Sequence[float],
    *,
    absolute_tolerance: float,
) -> dict[str, float | int | str]:
    """Measure drift against locked deterministic benchmark evidence."""

    current_array = _array(current, "current")
    locked_array = _array(locked, "locked")
    if current_array.shape != locked_array.shape:
        raise ValueError("Benchmark arrays must align.")
    tolerance = float(absolute_tolerance)
    if tolerance < 0.0 or not math.isfinite(tolerance):
        raise ValueError("absolute_tolerance must be finite and non-negative.")
    differences = np.abs(current_array - locked_array)
    breaches = int(np.sum(differences > tolerance))
    maximum = float(np.max(differences)) if differences.size else 0.0
    return {
        "max_abs_drift": maximum,
        "breach_count": breaches,
        "status": "PASS" if breaches == 0 else "BLOCK",
    }

"""Independent challenger calculations and discrepancy controls for Gate 7."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Mapping, Sequence

import numpy as np


_STATUSES = {
    "PASS",
    "PASS_WITH_MONITORING",
    "REMEDIATE",
    "BLOCK",
}


def _finite(value: float, name: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{name} must be finite.")
    return number


def _array(values: Sequence[float] | np.ndarray, name: str) -> np.ndarray:
    result = np.asarray(values, dtype=float)
    if not np.isfinite(result).all():
        raise ValueError(f"{name} must contain finite values.")
    return result


@dataclass(frozen=True)
class ToleranceBand:
    """Soft and hard tolerances used to classify challenger differences."""

    absolute: float
    relative: float
    hard_multiplier: float = 5.0
    materiality: float = 0.0

    def __post_init__(self) -> None:
        for name in ("absolute", "relative", "materiality"):
            value = _finite(getattr(self, name), name)
            if value < 0.0:
                raise ValueError(f"{name} must be non-negative.")
            object.__setattr__(self, name, value)

        multiplier = _finite(self.hard_multiplier, "hard_multiplier")
        if multiplier < 1.0:
            raise ValueError("hard_multiplier must be at least one.")
        object.__setattr__(self, "hard_multiplier", multiplier)


@dataclass(frozen=True)
class ChallengerComparison:
    """One primary-versus-challenger reconciliation result."""

    component: str
    primary_value: float
    challenger_value: float
    absolute_difference: float
    relative_difference: float
    normalized_difference: float
    material: bool
    status: str
    reason: str

    def __post_init__(self) -> None:
        if not self.component.strip():
            raise ValueError("component must not be empty.")
        if self.status not in _STATUSES:
            raise ValueError("Unsupported challenger status.")
        if not self.reason.strip():
            raise ValueError("reason must not be empty.")


def compare_component(
    component: str,
    primary_value: float,
    challenger_value: float,
    tolerance: ToleranceBand,
) -> ChallengerComparison:
    """Classify a scalar discrepancy using soft, hard, and materiality gates."""

    primary = _finite(primary_value, "primary_value")
    challenger = _finite(challenger_value, "challenger_value")
    absolute = abs(primary - challenger)
    scale = max(abs(primary), abs(challenger), tolerance.absolute, 1e-15)
    relative = absolute / scale
    normalized = max(
        absolute / max(tolerance.absolute, 1e-15),
        relative / max(tolerance.relative, 1e-15),
    )
    material = max(abs(primary), abs(challenger), absolute) >= tolerance.materiality

    soft_pass = absolute <= tolerance.absolute or relative <= tolerance.relative
    hard_absolute = tolerance.absolute * tolerance.hard_multiplier
    hard_relative = tolerance.relative * tolerance.hard_multiplier
    hard_pass = absolute <= hard_absolute or relative <= hard_relative

    if soft_pass:
        status = "PASS"
        reason = "Primary and challenger values reconcile within soft tolerance."
    elif hard_pass and not material:
        status = "PASS_WITH_MONITORING"
        reason = "Difference exceeds soft tolerance but remains immaterial and within the hard boundary."
    elif hard_pass:
        status = "REMEDIATE"
        reason = "Material challenger difference exceeds soft tolerance and requires root-cause evidence."
    else:
        status = "BLOCK"
        reason = "Challenger difference exceeds the hard validation boundary."

    return ChallengerComparison(
        component=component,
        primary_value=primary,
        challenger_value=challenger,
        absolute_difference=absolute,
        relative_difference=relative,
        normalized_difference=normalized,
        material=material,
        status=status,
        reason=reason,
    )


def compare_component_vectors(
    component: str,
    primary_values: Sequence[float] | np.ndarray,
    challenger_values: Sequence[float] | np.ndarray,
    tolerance: ToleranceBand,
) -> tuple[ChallengerComparison, ...]:
    """Compare aligned vectors and return one result per index."""

    primary = _array(primary_values, "primary_values")
    challenger = _array(challenger_values, "challenger_values")
    if primary.shape != challenger.shape:
        raise ValueError("Primary and challenger shapes must match.")
    if primary.ndim != 1:
        raise ValueError("Vector reconciliation requires one-dimensional inputs.")

    return tuple(
        compare_component(
            f"{component}[{index}]",
            float(primary_value),
            float(challenger_value),
            tolerance,
        )
        for index, (primary_value, challenger_value) in enumerate(
            zip(primary, challenger, strict=True)
        )
    )


def independent_cva_challenger(
    expected_positive_exposure: Sequence[float] | np.ndarray,
    discount_factors: Sequence[float] | np.ndarray,
    marginal_default_probabilities: Sequence[float] | np.ndarray,
    recovery_rate: float,
) -> float:
    """Loop-based CVA challenger independent of the vectorized Gate 5 path."""

    exposure = _array(expected_positive_exposure, "expected_positive_exposure")
    discount = _array(discount_factors, "discount_factors")
    marginal_pd = _array(marginal_default_probabilities, "marginal_default_probabilities")
    if exposure.ndim != 1 or exposure.shape != discount.shape or exposure.shape != marginal_pd.shape:
        raise ValueError("CVA inputs must be aligned one-dimensional arrays.")
    if np.any(exposure < 0.0) or np.any(discount < 0.0) or np.any(marginal_pd < 0.0):
        raise ValueError("CVA inputs must be non-negative.")
    recovery = _finite(recovery_rate, "recovery_rate")
    if not 0.0 <= recovery < 1.0:
        raise ValueError("recovery_rate must be in [0, 1).")

    total = 0.0
    lgd = 1.0 - recovery
    for ee, df, dp in zip(exposure, discount, marginal_pd, strict=True):
        total += float(ee) * float(df) * float(dp) * lgd
    return float(total)


def independent_dva_challenger(
    expected_negative_exposure: Sequence[float] | np.ndarray,
    discount_factors: Sequence[float] | np.ndarray,
    own_marginal_default_probabilities: Sequence[float] | np.ndarray,
    own_recovery_rate: float,
) -> float:
    """Loop-based DVA challenger using expected negative exposure."""

    return independent_cva_challenger(
        expected_negative_exposure,
        discount_factors,
        own_marginal_default_probabilities,
        own_recovery_rate,
    )


def independent_funding_challenger(
    positive_funding_requirement: Sequence[float] | np.ndarray,
    negative_funding_requirement: Sequence[float] | np.ndarray,
    discount_factors: Sequence[float] | np.ndarray,
    year_fractions: Sequence[float] | np.ndarray,
    borrowing_spreads: Sequence[float] | np.ndarray,
    lending_spreads: Sequence[float] | np.ndarray,
) -> tuple[float, float, float]:
    """Independent FCA, FBA, and net-FVA challenger."""

    positive = _array(positive_funding_requirement, "positive_funding_requirement")
    negative = _array(negative_funding_requirement, "negative_funding_requirement")
    discount = _array(discount_factors, "discount_factors")
    times = _array(year_fractions, "year_fractions")
    borrowing = _array(borrowing_spreads, "borrowing_spreads")
    lending = _array(lending_spreads, "lending_spreads")
    shapes = {value.shape for value in (positive, negative, discount, times, borrowing, lending)}
    if len(shapes) != 1 or positive.ndim != 1:
        raise ValueError("Funding challenger inputs must be aligned one-dimensional arrays.")
    if positive.size < 2 or np.any(np.diff(times) <= 0.0):
        raise ValueError("year_fractions must contain at least two increasing values.")
    if np.any(positive < 0.0) or np.any(negative < 0.0) or np.any(discount < 0.0):
        raise ValueError("Funding requirements and discount factors must be non-negative.")

    fca = 0.0
    fba = 0.0
    for index in range(1, positive.size):
        dt = float(times[index] - times[index - 1])
        fca += float(positive[index]) * float(discount[index]) * float(borrowing[index]) * dt
        fba += float(negative[index]) * float(discount[index]) * float(lending[index]) * dt
    return float(fca), float(fba), float(fca - fba)


def challenger_evidence_hash(
    comparisons: Sequence[ChallengerComparison],
    metadata: Mapping[str, object] | None = None,
) -> str:
    """Return deterministic SHA-256 evidence for challenger results."""

    payload = {
        "comparisons": [
            {
                "component": item.component,
                "primary_value": item.primary_value,
                "challenger_value": item.challenger_value,
                "absolute_difference": item.absolute_difference,
                "relative_difference": item.relative_difference,
                "normalized_difference": item.normalized_difference,
                "material": item.material,
                "status": item.status,
                "reason": item.reason,
            }
            for item in comparisons
        ],
        "metadata": dict(metadata or {}),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()

"""Lifecycle drift metrics and status aggregation."""

from __future__ import annotations

import math
from typing import Sequence

from .domain import DriftObservation, GovernanceStatus, STATUS_ORDER


def _classify(value: float, warning: float, block: float) -> GovernanceStatus:
    if warning < 0.0 or block < warning:
        raise ValueError("Invalid drift thresholds.")
    if value <= warning:
        return GovernanceStatus.PASS
    if value <= block:
        return GovernanceStatus.PASS_WITH_MONITORING
    return GovernanceStatus.BLOCK


def scalar_drift(
    metric_name: str,
    reference_value: float,
    current_value: float,
    warning_threshold: float = 0.05,
    block_threshold: float = 0.20,
) -> DriftObservation:
    reference = float(reference_value)
    current = float(current_value)
    if not math.isfinite(reference) or not math.isfinite(current):
        raise ValueError("Drift values must be finite.")
    absolute = abs(current - reference)
    relative = absolute / max(abs(reference), abs(current), 1.0e-15)
    return DriftObservation(
        metric_name=metric_name,
        reference_value=reference,
        current_value=current,
        absolute_shift=absolute,
        relative_shift=relative,
        warning_threshold=warning_threshold,
        block_threshold=block_threshold,
        status=_classify(relative, warning_threshold, block_threshold),
    )


def population_stability_index(
    reference: Sequence[float],
    current: Sequence[float],
    warning_threshold: float = 0.10,
    block_threshold: float = 0.25,
    epsilon: float = 1.0e-12,
) -> DriftObservation:
    first = tuple(float(value) for value in reference)
    second = tuple(float(value) for value in current)
    if len(first) != len(second) or len(first) < 2:
        raise ValueError("PSI vectors must be aligned and contain at least two buckets.")
    if any(value < 0.0 or not math.isfinite(value) for value in (*first, *second)):
        raise ValueError("PSI proportions must be finite and non-negative.")
    sum_first = sum(first)
    sum_second = sum(second)
    if sum_first <= 0.0 or sum_second <= 0.0:
        raise ValueError("PSI vectors must have positive mass.")
    first = tuple(max(value / sum_first, epsilon) for value in first)
    second = tuple(max(value / sum_second, epsilon) for value in second)
    psi = sum((b - a) * math.log(b / a) for a, b in zip(first, second))
    psi = max(0.0, psi)
    return DriftObservation(
        metric_name="population_stability_index",
        reference_value=0.0,
        current_value=psi,
        absolute_shift=psi,
        relative_shift=psi,
        warning_threshold=warning_threshold,
        block_threshold=block_threshold,
        status=_classify(psi, warning_threshold, block_threshold),
    )


def aggregate_drift(observations: Sequence[DriftObservation]) -> dict[str, object]:
    values = tuple(observations)
    if not values:
        raise ValueError("At least one drift observation is required.")
    worst = max((item.status for item in values), key=lambda status: STATUS_ORDER[status])
    return {
        "status": worst.value,
        "metric_count": len(values),
        "block_count": sum(item.status == GovernanceStatus.BLOCK for item in values),
        "monitoring_count": sum(
            item.status == GovernanceStatus.PASS_WITH_MONITORING for item in values
        ),
        "metrics": tuple(item.metric_name for item in values),
    }


def consecutive_monitoring_breach(
    observations: Sequence[DriftObservation],
    required_consecutive: int = 2,
) -> bool:
    if required_consecutive <= 0:
        raise ValueError("required_consecutive must be positive.")
    streak = 0
    for item in observations:
        if item.status in {GovernanceStatus.PASS_WITH_MONITORING, GovernanceStatus.BLOCK}:
            streak += 1
            if streak >= required_consecutive:
                return True
        else:
            streak = 0
    return False

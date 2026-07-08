"""Model monitoring helpers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MonitoringResult:
    model_id: str
    metric_name: str
    metric_value: float
    threshold: float
    status: str


def threshold_monitor(model_id: str, metric_name: str, metric_value: float, threshold: float) -> MonitoringResult:
    """Flag a metric as pass or review based on a threshold."""
    status = "pass" if metric_value <= threshold else "review"
    return MonitoringResult(
        model_id=model_id,
        metric_name=metric_name,
        metric_value=metric_value,
        threshold=threshold,
        status=status,
    )

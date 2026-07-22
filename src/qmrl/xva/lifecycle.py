"""Lifecycle monitoring rules and release-level status aggregation."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Iterable


VALID_STATUSES = (
    "PASS",
    "PASS_WITH_MONITORING",
    "REMEDIATE",
    "BLOCK",
)
_STATUS_RANK = {status: index for index, status in enumerate(VALID_STATUSES)}


@dataclass(frozen=True)
class MonitoringRule:
    """Three-threshold monitoring rule with explicit directionality."""

    metric: str
    warning_threshold: float
    remediate_threshold: float
    block_threshold: float
    direction: str = "higher_is_worse"
    owner: str = "Model Risk"

    def __post_init__(self) -> None:
        if not self.metric.strip():
            raise ValueError("metric must not be empty.")
        if self.direction not in {"higher_is_worse", "lower_is_worse"}:
            raise ValueError("direction must be higher_is_worse or lower_is_worse.")
        if self.direction == "higher_is_worse":
            if not (
                self.warning_threshold
                <= self.remediate_threshold
                <= self.block_threshold
            ):
                raise ValueError("Higher-is-worse thresholds must be increasing.")
        else:
            if not (
                self.warning_threshold
                >= self.remediate_threshold
                >= self.block_threshold
            ):
                raise ValueError("Lower-is-worse thresholds must be decreasing.")


@dataclass(frozen=True)
class MonitoringObservation:
    """One observed monitoring metric and its governed status."""

    metric: str
    value: float
    status: str
    owner: str
    rationale: str

    def __post_init__(self) -> None:
        if self.status not in VALID_STATUSES:
            raise ValueError(f"Unsupported monitoring status: {self.status}")


@dataclass(frozen=True)
class LifecycleAssessment:
    """Aggregated lifecycle status with complete component traceability."""

    observations: tuple[MonitoringObservation, ...]

    @property
    def overall_status(self) -> str:
        if not self.observations:
            return "BLOCK"
        return max(
            (item.status for item in self.observations),
            key=lambda status: _STATUS_RANK[status],
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "overall_status": self.overall_status,
            "observations": [
                {
                    "metric": item.metric,
                    "value": item.value,
                    "status": item.status,
                    "owner": item.owner,
                    "rationale": item.rationale,
                }
                for item in self.observations
            ],
        }


def evaluate_monitoring_metric(
    value: float,
    rule: MonitoringRule,
) -> MonitoringObservation:
    """Evaluate one metric using the four-state promotion vocabulary."""

    if rule.direction == "higher_is_worse":
        if value < rule.warning_threshold:
            status = "PASS"
        elif value < rule.remediate_threshold:
            status = "PASS_WITH_MONITORING"
        elif value < rule.block_threshold:
            status = "REMEDIATE"
        else:
            status = "BLOCK"
    else:
        if value > rule.warning_threshold:
            status = "PASS"
        elif value > rule.remediate_threshold:
            status = "PASS_WITH_MONITORING"
        elif value > rule.block_threshold:
            status = "REMEDIATE"
        else:
            status = "BLOCK"

    rationale = (
        f"{rule.metric}={value:g}; direction={rule.direction}; "
        f"warning={rule.warning_threshold:g}; "
        f"remediate={rule.remediate_threshold:g}; "
        f"block={rule.block_threshold:g}."
    )

    return MonitoringObservation(
        metric=rule.metric,
        value=float(value),
        status=status,
        owner=rule.owner,
        rationale=rationale,
    )


def assess_lifecycle(
    observations: Iterable[MonitoringObservation],
) -> LifecycleAssessment:
    """Aggregate monitored components using the worst-status rule."""

    return LifecycleAssessment(tuple(observations))


def lifecycle_manifest_hash(assessment: LifecycleAssessment) -> str:
    """Return a deterministic lifecycle evidence hash."""

    payload = json.dumps(
        assessment.to_dict(),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()

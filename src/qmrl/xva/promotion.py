"""Component and portfolio promotion governance for XVA Gate 7."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Mapping, Sequence


STATUSES = (
    "PASS",
    "PASS_WITH_MONITORING",
    "REMEDIATE",
    "BLOCK",
)
_RANK = {status: index for index, status in enumerate(STATUSES)}


@dataclass(frozen=True)
class ComponentDecision:
    """Promotion decision for one material XVA component."""

    component: str
    status: str
    material: bool
    reasons: tuple[str, ...]
    metrics: Mapping[str, float | int | str | bool]
    unresolved_findings: int = 0
    evidence_reference: str = ""

    def __post_init__(self) -> None:
        if not self.component.strip():
            raise ValueError("component must not be empty.")
        if self.status not in _RANK:
            raise ValueError("Unsupported component status.")
        if not self.reasons or any(not reason.strip() for reason in self.reasons):
            raise ValueError("At least one non-empty reason is required.")
        if self.unresolved_findings < 0:
            raise ValueError("unresolved_findings must be non-negative.")


@dataclass(frozen=True)
class PromotionDecision:
    """Portfolio-level release-candidate promotion result."""

    candidate_version: str
    status: str
    components: tuple[ComponentDecision, ...]
    blocking_components: tuple[str, ...]
    monitoring_components: tuple[str, ...]
    remediation_components: tuple[str, ...]
    hard_gates_passed: bool
    human_approval_required: bool
    production_approval: bool
    reason: str

    def __post_init__(self) -> None:
        if not self.candidate_version.strip():
            raise ValueError("candidate_version must not be empty.")
        if self.status not in _RANK:
            raise ValueError("Unsupported promotion status.")
        if not self.components:
            raise ValueError("At least one component decision is required.")
        if self.production_approval:
            raise ValueError("Gate 7 cannot grant production approval.")
        if not self.reason.strip():
            raise ValueError("reason must not be empty.")


def component_decision(
    component: str,
    diagnostic_statuses: Sequence[str],
    *,
    material: bool,
    unresolved_findings: int = 0,
    metrics: Mapping[str, float | int | str | bool] | None = None,
    evidence_reference: str = "",
) -> ComponentDecision:
    """Aggregate challenger and stability statuses for one component."""

    statuses = tuple(diagnostic_statuses)
    if not statuses or any(status not in _RANK for status in statuses):
        raise ValueError("diagnostic_statuses must contain governed statuses.")
    if unresolved_findings < 0:
        raise ValueError("unresolved_findings must be non-negative.")

    worst = max(statuses, key=lambda status: _RANK[status])
    reasons = [f"Worst diagnostic status: {worst}."]

    if unresolved_findings > 0 and material:
        worst = "BLOCK"
        reasons.append("Material unresolved findings prevent promotion.")
    elif unresolved_findings > 0 and _RANK[worst] < _RANK["REMEDIATE"]:
        worst = "REMEDIATE"
        reasons.append("Unresolved findings require remediation.")

    return ComponentDecision(
        component=component,
        status=worst,
        material=material,
        reasons=tuple(reasons),
        metrics=dict(metrics or {}),
        unresolved_findings=unresolved_findings,
        evidence_reference=evidence_reference,
    )


def portfolio_promotion_decision(
    candidate_version: str,
    components: Sequence[ComponentDecision],
    *,
    benchmarks_passed: bool,
    reproducibility_passed: bool,
    required_ci_passed: bool,
    evidence_complete: bool,
) -> PromotionDecision:
    """Apply hard gates and the no-material-BLOCK promotion rule."""

    component_tuple = tuple(components)
    if not component_tuple:
        raise ValueError("At least one component decision is required.")
    names = [item.component for item in component_tuple]
    if len(names) != len(set(names)):
        raise ValueError("Component names must be unique.")

    hard_gates = all((benchmarks_passed, reproducibility_passed, required_ci_passed, evidence_complete))
    blocking = tuple(item.component for item in component_tuple if item.status == "BLOCK" and item.material)
    remediation = tuple(item.component for item in component_tuple if item.status == "REMEDIATE")
    monitoring = tuple(item.component for item in component_tuple if item.status == "PASS_WITH_MONITORING")

    if not hard_gates:
        status = "BLOCK"
        reason = "One or more mandatory promotion gates failed."
    elif blocking:
        status = "BLOCK"
        reason = "At least one material component is classified as BLOCK."
    elif remediation:
        status = "REMEDIATE"
        reason = "One or more components require remediation before release-candidate promotion."
    elif monitoring:
        status = "PASS_WITH_MONITORING"
        reason = "The candidate passes with explicit monitoring obligations."
    else:
        status = "PASS"
        reason = "All components and mandatory promotion gates pass."

    return PromotionDecision(
        candidate_version=candidate_version,
        status=status,
        components=component_tuple,
        blocking_components=blocking,
        monitoring_components=monitoring,
        remediation_components=remediation,
        hard_gates_passed=hard_gates,
        human_approval_required=True,
        production_approval=False,
        reason=reason,
    )


def promotion_evidence_payload(
    decision: PromotionDecision,
    *,
    test_count: int,
    repository_commit: str,
    manifests: Sequence[str],
) -> dict[str, object]:
    """Build a machine-readable release-candidate evidence package."""

    if test_count <= 0:
        raise ValueError("test_count must be positive.")
    if not repository_commit.strip():
        raise ValueError("repository_commit must not be empty.")
    if not manifests:
        raise ValueError("At least one evidence manifest is required.")

    payload: dict[str, object] = {
        "schema_version": "1.0",
        "candidate_version": decision.candidate_version,
        "promotion_status": decision.status,
        "hard_gates_passed": decision.hard_gates_passed,
        "human_approval_required": decision.human_approval_required,
        "production_approval": decision.production_approval,
        "reason": decision.reason,
        "test_count": int(test_count),
        "repository_commit": repository_commit,
        "manifests": list(manifests),
        "components": [
            {
                "component": item.component,
                "status": item.status,
                "material": item.material,
                "reasons": list(item.reasons),
                "metrics": dict(item.metrics),
                "unresolved_findings": item.unresolved_findings,
                "evidence_reference": item.evidence_reference,
            }
            for item in decision.components
        ],
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    payload["evidence_sha256"] = hashlib.sha256(encoded).hexdigest()
    return payload

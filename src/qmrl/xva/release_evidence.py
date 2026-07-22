"""v1.3 release-candidate and publication governance evidence."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Iterable


_ALLOWED_COMPONENT_STATUSES = {
    "PASS",
    "PASS_WITH_MONITORING",
    "REMEDIATE",
    "BLOCK",
}


@dataclass(frozen=True)
class GateEvidence:
    gate: int
    status: str
    artifact_ref: str

    def __post_init__(self) -> None:
        if self.gate < 1:
            raise ValueError("gate must be positive.")
        if self.status not in _ALLOWED_COMPONENT_STATUSES:
            raise ValueError(f"Unsupported gate status: {self.status}")
        if not self.artifact_ref.strip():
            raise ValueError("artifact_ref must not be empty.")


@dataclass(frozen=True)
class ReleaseCandidateEvidence:
    version: str
    collected_test_count: int
    required_check: str
    ci_passed: bool
    gates: tuple[GateEvidence, ...]
    dashboard_status: str
    lifecycle_status: str
    genai_human_review_status: str
    open_gates: tuple[str, ...]
    production_approval: bool = False


@dataclass(frozen=True)
class ReleaseValidation:
    status: str
    issues: tuple[str, ...]

    @property
    def releasable(self) -> bool:
        return self.status in {"PASS", "PASS_WITH_MONITORING"}


def validate_release_candidate(
    evidence: ReleaseCandidateEvidence,
) -> ReleaseValidation:
    """Apply a fail-closed publication decision without granting production use."""

    issues: list[str] = []
    expected_gates = set(range(1, 9))
    supplied_gates = {item.gate for item in evidence.gates}

    if evidence.version != "1.3.0":
        issues.append("Release version must be 1.3.0.")
    if evidence.collected_test_count < 322:
        issues.append("Collected test count is below the Gate 7 baseline.")
    if evidence.required_check != "Python 3.12 validation":
        issues.append("Required CI check is not the governed provider-bound check.")
    if not evidence.ci_passed:
        issues.append("Required CI did not pass.")
    if supplied_gates != expected_gates:
        issues.append(
            f"Gate evidence must cover 1 through 8; received {sorted(supplied_gates)}."
        )
    if any(item.status in {"REMEDIATE", "BLOCK"} for item in evidence.gates):
        issues.append("One or more XVA gates are not promotion eligible.")
    if evidence.dashboard_status in {"REMEDIATE", "BLOCK"}:
        issues.append("Dashboard status is not release eligible.")
    if evidence.lifecycle_status in {"REMEDIATE", "BLOCK"}:
        issues.append("Lifecycle status is not release eligible.")
    if evidence.genai_human_review_status not in {
        "ACCEPTED",
        "ACCEPTED_WITH_MONITORING",
    }:
        issues.append("Governed GenAI findings lack completed human review.")
    if evidence.production_approval:
        issues.append("A public research release cannot grant production approval.")

    if issues:
        return ReleaseValidation(status="BLOCK", issues=tuple(issues))

    monitoring = bool(evidence.open_gates) or any(
        status == "PASS_WITH_MONITORING"
        for status in (
            evidence.dashboard_status,
            evidence.lifecycle_status,
            *(item.status for item in evidence.gates),
        )
    )

    return ReleaseValidation(
        status="PASS_WITH_MONITORING" if monitoring else "PASS",
        issues=(),
    )


def canonical_release_hash(evidence: ReleaseCandidateEvidence) -> str:
    payload = {
        "version": evidence.version,
        "collected_test_count": evidence.collected_test_count,
        "required_check": evidence.required_check,
        "ci_passed": evidence.ci_passed,
        "gates": [
            {
                "gate": item.gate,
                "status": item.status,
                "artifact_ref": item.artifact_ref,
            }
            for item in sorted(evidence.gates, key=lambda item: item.gate)
        ],
        "dashboard_status": evidence.dashboard_status,
        "lifecycle_status": evidence.lifecycle_status,
        "genai_human_review_status": evidence.genai_human_review_status,
        "open_gates": list(evidence.open_gates),
        "production_approval": evidence.production_approval,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

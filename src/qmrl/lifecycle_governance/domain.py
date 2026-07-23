"""Governed challenge, stability, drift, and lifecycle domain objects."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from enum import Enum
import hashlib
import json
import math
import re
from typing import Any, Mapping


CHALLENGE_BOUNDARY = "ADVISORY_CHALLENGE_NO_MODEL_APPROVAL"
GENAI_BOUNDARY = "GENAI_ADVISORY_ONLY_NO_AUTONOMOUS_APPROVAL"
RELEASE_CANDIDATE_STATUS = "RELEASE_CANDIDATE_VALIDATED"


class GovernanceStatus(str, Enum):
    PASS = "PASS"
    PASS_WITH_MONITORING = "PASS_WITH_MONITORING"
    REMEDIATE = "REMEDIATE"
    BLOCK = "BLOCK"
    INVALID = "INVALID"


STATUS_ORDER: Mapping[GovernanceStatus, int] = {
    GovernanceStatus.PASS: 0,
    GovernanceStatus.PASS_WITH_MONITORING: 1,
    GovernanceStatus.REMEDIATE: 2,
    GovernanceStatus.BLOCK: 3,
    GovernanceStatus.INVALID: 4,
}


class ChallengeComponent(str, Enum):
    PORTFOLIO_INGESTION = "portfolio_ingestion"
    MULTICURRENCY = "multicurrency"
    MARGIN_MVA = "margin_mva"
    CAPITAL_KVA = "capital_kva"
    INCREMENTAL_ALLOCATION = "incremental_allocation"
    OPERATIONS = "operations"
    GOVERNED_GENAI = "governed_genai"


def _nonblank(value: str, name: str) -> str:
    result = str(value).strip()
    if not result:
        raise ValueError(f"{name} cannot be blank.")
    return result


def _finite(value: float, name: str) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite.")
    return result


def _hash(value: str, name: str) -> str:
    result = value.strip().lower()
    if not re.fullmatch(r"[0-9a-f]{64}", result):
        raise ValueError(f"{name} must be a lowercase SHA-256 hex digest.")
    return result


def canonicalize(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return canonicalize(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): canonicalize(value[key]) for key in sorted(value, key=str)}
    if isinstance(value, (tuple, list)):
        return [canonicalize(item) for item in value]
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("Canonical evidence cannot contain non-finite values.")
        return float(format(value, ".17g"))
    return value


def canonical_json(value: Any) -> str:
    return json.dumps(
        canonicalize(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def evidence_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def worst_status(statuses: tuple[GovernanceStatus, ...]) -> GovernanceStatus:
    if not statuses:
        return GovernanceStatus.INVALID
    return max(statuses, key=lambda status: STATUS_ORDER[status])


@dataclass(frozen=True)
class ChallengeFinding:
    finding_id: str
    component: ChallengeComponent
    status: GovernanceStatus
    metric_name: str
    primary_value: float
    challenger_value: float
    tolerance: float
    absolute_difference: float
    relative_difference: float
    material: bool = False
    message: str = ""
    evidence_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "finding_id", _nonblank(self.finding_id, "finding_id"))
        object.__setattr__(self, "metric_name", _nonblank(self.metric_name, "metric_name"))
        object.__setattr__(self, "component", ChallengeComponent(self.component))
        object.__setattr__(self, "status", GovernanceStatus(self.status))
        for name in (
            "primary_value",
            "challenger_value",
            "tolerance",
            "absolute_difference",
            "relative_difference",
        ):
            object.__setattr__(self, name, _finite(getattr(self, name), name))
        if self.tolerance < 0.0 or self.absolute_difference < 0.0 or self.relative_difference < 0.0:
            raise ValueError("Tolerance and challenge differences cannot be negative.")
        if self.material and self.status not in {GovernanceStatus.BLOCK, GovernanceStatus.INVALID}:
            raise ValueError("Only BLOCK or INVALID findings may be marked material.")
        object.__setattr__(
            self,
            "evidence_ids",
            tuple(_nonblank(value, "evidence_id") for value in self.evidence_ids),
        )


@dataclass(frozen=True)
class ChallengeReport:
    report_id: str
    run_id: str
    challenger_id: str
    component: ChallengeComponent
    findings: tuple[ChallengeFinding, ...]
    evidence_hash: str
    created_at_utc: str = "2026-07-23T00:00:00Z"
    boundary: str = CHALLENGE_BOUNDARY

    def __post_init__(self) -> None:
        for name in ("report_id", "run_id", "challenger_id", "created_at_utc"):
            object.__setattr__(self, name, _nonblank(getattr(self, name), name))
        object.__setattr__(self, "component", ChallengeComponent(self.component))
        if not self.findings:
            raise ValueError("A challenge report requires at least one finding.")
        if any(finding.component != self.component for finding in self.findings):
            raise ValueError("All findings must match the report component.")
        if len({finding.finding_id for finding in self.findings}) != len(self.findings):
            raise ValueError("Challenge finding identifiers must be unique within a report.")
        object.__setattr__(self, "evidence_hash", _hash(self.evidence_hash, "evidence_hash"))
        if self.boundary != CHALLENGE_BOUNDARY:
            raise ValueError("Challenge reports must preserve the advisory boundary.")

    @property
    def status(self) -> GovernanceStatus:
        return worst_status(tuple(finding.status for finding in self.findings))

    @property
    def material_blocks(self) -> tuple[ChallengeFinding, ...]:
        return tuple(
            finding
            for finding in self.findings
            if finding.material and finding.status in {GovernanceStatus.BLOCK, GovernanceStatus.INVALID}
        )


@dataclass(frozen=True)
class StabilityObservation:
    dimension: str
    baseline_value: float
    challenged_value: float
    deviation: float
    warning_threshold: float
    block_threshold: float
    status: GovernanceStatus
    detail: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "dimension", _nonblank(self.dimension, "dimension"))
        object.__setattr__(self, "status", GovernanceStatus(self.status))
        for name in (
            "baseline_value",
            "challenged_value",
            "deviation",
            "warning_threshold",
            "block_threshold",
        ):
            object.__setattr__(self, name, _finite(getattr(self, name), name))
        if min(self.deviation, self.warning_threshold, self.block_threshold) < 0.0:
            raise ValueError("Stability deviations and thresholds cannot be negative.")
        if self.warning_threshold > self.block_threshold:
            raise ValueError("warning_threshold cannot exceed block_threshold.")


@dataclass(frozen=True)
class DriftObservation:
    metric_name: str
    reference_value: float
    current_value: float
    absolute_shift: float
    relative_shift: float
    warning_threshold: float
    block_threshold: float
    status: GovernanceStatus

    def __post_init__(self) -> None:
        object.__setattr__(self, "metric_name", _nonblank(self.metric_name, "metric_name"))
        object.__setattr__(self, "status", GovernanceStatus(self.status))
        for name in (
            "reference_value",
            "current_value",
            "absolute_shift",
            "relative_shift",
            "warning_threshold",
            "block_threshold",
        ):
            object.__setattr__(self, name, _finite(getattr(self, name), name))
        if min(self.absolute_shift, self.relative_shift, self.warning_threshold, self.block_threshold) < 0.0:
            raise ValueError("Drift shifts and thresholds cannot be negative.")
        if self.warning_threshold > self.block_threshold:
            raise ValueError("warning_threshold cannot exceed block_threshold.")


@dataclass(frozen=True)
class DispositionRecord:
    finding_id: str
    owner: str
    action: str
    state: str
    evidence_id: str
    reviewed_by: str

    def __post_init__(self) -> None:
        for name in ("finding_id", "owner", "action", "state", "evidence_id", "reviewed_by"):
            object.__setattr__(self, name, _nonblank(getattr(self, name), name))
        if self.state not in {"CLOSED", "ACCEPTED_RISK", "OPEN"}:
            raise ValueError("Unsupported disposition state.")

    @property
    def resolved(self) -> bool:
        return self.state in {"CLOSED", "ACCEPTED_RISK"}


@dataclass(frozen=True)
class GenAIEvidenceRecord:
    record_id: str
    prompt_id: str
    model_id: str
    model_version: str
    input_hash: str
    output_hash: str
    reviewer: str
    disposition: str
    autonomous_model_approval: bool = False
    changed_quantitative_result: bool = False
    promoted_release: bool = False
    boundary: str = GENAI_BOUNDARY

    def __post_init__(self) -> None:
        for name in (
            "record_id",
            "prompt_id",
            "model_id",
            "model_version",
            "reviewer",
            "disposition",
        ):
            object.__setattr__(self, name, _nonblank(getattr(self, name), name))
        object.__setattr__(self, "input_hash", _hash(self.input_hash, "input_hash"))
        object.__setattr__(self, "output_hash", _hash(self.output_hash, "output_hash"))
        if self.disposition not in {
            "ACCEPTED",
            "REJECTED",
            "REMEDIATION_REQUIRED",
            "INFORMATIONAL",
        }:
            raise ValueError("Unsupported GenAI evidence disposition.")


@dataclass(frozen=True)
class LifecycleAssessment:
    assessment_id: str
    status: str
    eligible_for_release_candidate: bool
    material_block_ids: tuple[str, ...]
    unresolved_remediation_ids: tuple[str, ...]
    monitoring_ids: tuple[str, ...]
    registry_missing_components: tuple[str, ...]
    evidence_hash: str
    production_approval: bool = False
    regulatory_approval: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "assessment_id", _nonblank(self.assessment_id, "assessment_id"))
        if self.status not in {RELEASE_CANDIDATE_STATUS, "REMEDIATE", "BLOCK", "INVALID"}:
            raise ValueError("Unsupported lifecycle assessment status.")
        object.__setattr__(self, "evidence_hash", _hash(self.evidence_hash, "evidence_hash"))
        if self.production_approval or self.regulatory_approval:
            raise ValueError("Gate 7 cannot grant production or regulatory approval.")
        if self.eligible_for_release_candidate != (self.status == RELEASE_CANDIDATE_STATUS):
            raise ValueError("Eligibility must reconcile with lifecycle status.")

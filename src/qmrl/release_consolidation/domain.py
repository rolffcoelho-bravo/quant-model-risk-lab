"""Release-consolidation domain objects for v1.4 Gate 8."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re

RELEASE_TAG = "v1.4.0"
RELEASE_STATUS = "RELEASED_WITH_MONITORING"
RELEASE_BOUNDARY = "PUBLIC_RESEARCH_RELEASE_WITH_MONITORING"


class CheckStatus(str, Enum):
    PASS = "PASS"
    PASS_WITH_MONITORING = "PASS_WITH_MONITORING"
    REMEDIATE = "REMEDIATE"
    BLOCK = "BLOCK"
    INVALID = "INVALID"


@dataclass(frozen=True)
class ReleaseArtifact:
    path: str
    sha256: str
    category: str
    required: bool = True

    def __post_init__(self) -> None:
        if not self.path.strip() or self.path.startswith("/") or ".." in self.path.split("/"):
            raise ValueError("Release artifact path must be a non-empty repository-relative path.")
        if not re.fullmatch(r"[0-9a-f]{64}", self.sha256):
            raise ValueError("Release artifact hash must be a lowercase SHA-256 digest.")
        if not self.category.strip():
            raise ValueError("Release artifact category cannot be blank.")


@dataclass(frozen=True)
class GateEvidence:
    gate: int
    status: str
    evidence_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.gate not in range(9):
            raise ValueError("Gate must lie in the closed interval [0, 8].")
        if not self.status.strip() or not self.evidence_ids:
            raise ValueError("Gate evidence requires status and evidence identifiers.")
        if any(not value.strip() for value in self.evidence_ids):
            raise ValueError("Evidence identifiers cannot be blank.")


@dataclass(frozen=True)
class AssuranceCheck:
    check_id: str
    status: CheckStatus
    evidence: str
    material: bool = False

    def __post_init__(self) -> None:
        if not self.check_id.strip() or not self.evidence.strip():
            raise ValueError("Assurance checks require identifiers and evidence.")
        object.__setattr__(self, "status", CheckStatus(self.status))
        if self.material and self.status not in {CheckStatus.BLOCK, CheckStatus.INVALID}:
            raise ValueError("Only BLOCK or INVALID checks may be material.")


@dataclass(frozen=True)
class ReleaseAssessment:
    status: str
    eligible: bool
    checks: tuple[AssuranceCheck, ...]
    monitoring_ids: tuple[str, ...] = ()
    release_tag_created: bool = False
    production_approval: bool = False
    regulatory_approval: bool = False
    boundary: str = RELEASE_BOUNDARY

    def __post_init__(self) -> None:
        allowed = {
            "BLOCK", "REMEDIATE", "RELEASE_APPROVAL_REQUIRED",
            "RELEASED", RELEASE_STATUS,
        }
        if self.status not in allowed:
            raise ValueError("Unsupported release assessment status.")
        if not self.checks:
            raise ValueError("Release assessment requires assurance checks.")
        if self.production_approval or self.regulatory_approval:
            raise ValueError("Gate 8 cannot grant production or regulatory approval.")
        if self.boundary != RELEASE_BOUNDARY:
            raise ValueError("Release boundary must remain public research with monitoring.")
        expected = self.status in {"RELEASED", RELEASE_STATUS}
        if self.eligible != expected:
            raise ValueError("Release eligibility must reconcile with status.")

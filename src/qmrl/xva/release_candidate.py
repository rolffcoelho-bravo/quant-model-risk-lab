"""Release-candidate evidence assembly and validation for Gate 7."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Mapping, Sequence

from .promotion import PromotionDecision, promotion_evidence_payload


@dataclass(frozen=True)
class ReleaseCandidatePackage:
    """Immutable Gate 7 release-candidate evidence package."""

    candidate_version: str
    promotion_status: str
    test_count: int
    repository_commit: str
    component_count: int
    evidence_sha256: str
    payload: Mapping[str, object]

    def __post_init__(self) -> None:
        if not self.candidate_version.strip():
            raise ValueError("candidate_version must not be empty.")
        if self.test_count <= 0 or self.component_count <= 0:
            raise ValueError("test_count and component_count must be positive.")
        if len(self.evidence_sha256) != 64:
            raise ValueError("evidence_sha256 must be a SHA-256 digest.")


def build_release_candidate_package(
    decision: PromotionDecision,
    *,
    test_count: int,
    repository_commit: str,
    manifests: Sequence[str],
) -> ReleaseCandidatePackage:
    """Create and verify a deterministic Gate 7 evidence package."""

    payload = promotion_evidence_payload(
        decision,
        test_count=test_count,
        repository_commit=repository_commit,
        manifests=manifests,
    )
    digest = str(payload["evidence_sha256"])
    verification_payload = dict(payload)
    verification_payload.pop("evidence_sha256")
    encoded = json.dumps(verification_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if hashlib.sha256(encoded).hexdigest() != digest:
        raise RuntimeError("Release-candidate evidence hash verification failed.")

    return ReleaseCandidatePackage(
        candidate_version=decision.candidate_version,
        promotion_status=decision.status,
        test_count=int(test_count),
        repository_commit=repository_commit,
        component_count=len(decision.components),
        evidence_sha256=digest,
        payload=payload,
    )


def write_release_candidate_package(
    package: ReleaseCandidatePackage,
    path: str | Path,
) -> Path:
    """Write a canonical JSON evidence package."""

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(package.payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output_path


def validate_release_candidate_payload(payload: Mapping[str, object]) -> None:
    """Validate required release-candidate evidence fields and hash."""

    required = {
        "schema_version",
        "candidate_version",
        "promotion_status",
        "hard_gates_passed",
        "human_approval_required",
        "production_approval",
        "reason",
        "test_count",
        "repository_commit",
        "manifests",
        "components",
        "evidence_sha256",
    }
    missing = required - set(payload)
    if missing:
        raise ValueError(f"Missing release-candidate fields: {sorted(missing)}")
    if payload["production_approval"] is not False:
        raise ValueError("Gate 7 release-candidate evidence cannot grant production approval.")
    if payload["human_approval_required"] is not True:
        raise ValueError("Gate 7 requires human approval.")
    digest = str(payload["evidence_sha256"])
    verification = dict(payload)
    verification.pop("evidence_sha256")
    encoded = json.dumps(verification, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if hashlib.sha256(encoded).hexdigest() != digest:
        raise ValueError("Release-candidate evidence hash mismatch.")

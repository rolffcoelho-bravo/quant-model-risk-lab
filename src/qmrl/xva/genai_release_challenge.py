"""Governed GenAI challenge contracts for the XVA v1.3 release."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Iterable


_ALLOWED_SEVERITIES = {"INFORMATIONAL", "MONITORING", "REMEDIATION", "BLOCK"}
_PROHIBITED_APPROVAL_LANGUAGE = (
    "approved for production",
    "production approved",
    "regulatory approval granted",
    "close the finding without human review",
    "autonomous model approval",
)


@dataclass(frozen=True)
class ApprovedArtifact:
    """One artifact permitted in a governed challenge packet."""

    path: str
    sha256: str

    def __post_init__(self) -> None:
        if not self.path.strip():
            raise ValueError("Approved artifact path must not be empty.")
        if len(self.sha256) != 64 or any(
            character not in "0123456789abcdef" for character in self.sha256.lower()
        ):
            raise ValueError("Approved artifact sha256 must be a 64-character hexadecimal digest.")


@dataclass(frozen=True)
class ChallengeFinding:
    """Structured GenAI finding that remains subject to human review."""

    finding_id: str
    severity: str
    claim: str
    recommendation: str
    artifact_citations: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.finding_id.strip():
            raise ValueError("finding_id must not be empty.")
        if self.severity not in _ALLOWED_SEVERITIES:
            raise ValueError(f"Unsupported finding severity: {self.severity}")
        if not self.claim.strip() or not self.recommendation.strip():
            raise ValueError("Finding claim and recommendation must not be empty.")


@dataclass(frozen=True)
class ChallengeValidation:
    """Deterministic validation result for structured GenAI findings."""

    valid: bool
    status: str
    issues: tuple[str, ...]
    human_review_required: bool = True
    autonomous_model_approval: bool = False


def artifact_sha256(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def build_challenge_packet(
    artifacts: Iterable[ApprovedArtifact],
    *,
    instruction_version: str,
) -> dict[str, object]:
    """Build a canonical evidence-only challenge packet."""

    approved = sorted(artifacts, key=lambda item: item.path)
    if not approved:
        raise ValueError("At least one approved artifact is required.")
    packet = {
        "instruction_version": instruction_version,
        "live_provider_execution_required": False,
        "human_review_required": True,
        "autonomous_model_approval": False,
        "approved_artifacts": [
            {"path": item.path, "sha256": item.sha256}
            for item in approved
        ],
    }
    canonical = json.dumps(packet, sort_keys=True, separators=(",", ":"))
    packet["packet_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return packet


def validate_findings(
    findings: Iterable[ChallengeFinding],
    approved_artifacts: Iterable[ApprovedArtifact],
) -> ChallengeValidation:
    """Fail closed on unsupported, uncited, or approval-like GenAI claims."""

    approved_paths = {artifact.path for artifact in approved_artifacts}
    issues: list[str] = []
    finding_list = tuple(findings)

    if not finding_list:
        issues.append("No structured findings were supplied.")

    identifiers: set[str] = set()
    for finding in finding_list:
        if finding.finding_id in identifiers:
            issues.append(f"Duplicate finding identifier: {finding.finding_id}")
        identifiers.add(finding.finding_id)

        if not finding.artifact_citations:
            issues.append(f"Finding {finding.finding_id} has no artifact citation.")

        unsupported = sorted(set(finding.artifact_citations) - approved_paths)
        if unsupported:
            issues.append(
                f"Finding {finding.finding_id} cites unapproved artifacts: {unsupported}"
            )

        combined = f"{finding.claim} {finding.recommendation}".lower()
        for phrase in _PROHIBITED_APPROVAL_LANGUAGE:
            if phrase in combined:
                issues.append(
                    f"Finding {finding.finding_id} uses prohibited approval language: {phrase}"
                )

    valid = not issues
    return ChallengeValidation(
        valid=valid,
        status="VALIDATED_PENDING_HUMAN_REVIEW" if valid else "BLOCK",
        issues=tuple(issues),
        human_review_required=True,
        autonomous_model_approval=False,
    )


def validate_human_review(
    review: dict[str, object],
    finding_ids: Iterable[str],
) -> bool:
    """Require an identified human reviewer and explicit governed decision."""

    allowed_decisions = {
        "ACCEPTED",
        "ACCEPTED_WITH_MONITORING",
        "REMEDIATE",
        "REJECTED",
    }
    if review.get("reviewer_type") != "HUMAN_MODEL_RISK_REVIEWER":
        return False
    if review.get("decision") not in allowed_decisions:
        return False
    if review.get("autonomous_model_approval") is not False:
        return False
    reviewed = set(review.get("reviewed_finding_ids", []))
    return reviewed == set(finding_ids)

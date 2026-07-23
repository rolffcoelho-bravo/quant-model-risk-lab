"""Promotion governance and remediation disposition controls."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .domain import (
    ChallengeReport,
    DispositionRecord,
    DriftObservation,
    GovernanceStatus,
    LifecycleAssessment,
    RELEASE_CANDIDATE_STATUS,
    StabilityObservation,
    evidence_sha256,
)
from .registry import ChallengerRegistry, REQUIRED_COMPONENTS


@dataclass(frozen=True)
class PromotionPolicy:
    required_components: tuple = REQUIRED_COMPONENTS
    require_resolved_remediations: bool = True
    require_human_release_decision: bool = True
    boundary: str = "HUMAN_PROMOTION_DECISION_REQUIRED"

    def __post_init__(self) -> None:
        if self.boundary != "HUMAN_PROMOTION_DECISION_REQUIRED":
            raise ValueError("Gate 7 promotion must remain a human decision.")


def disposition_map(records: Sequence[DispositionRecord]) -> dict[str, DispositionRecord]:
    result: dict[str, DispositionRecord] = {}
    for record in records:
        if record.finding_id in result:
            raise ValueError(f"Duplicate disposition for finding {record.finding_id}")
        result[record.finding_id] = record
    return result


def validate_dispositions(
    reports: Sequence[ChallengeReport],
    dispositions: Sequence[DispositionRecord],
) -> tuple[str, ...]:
    mapping = disposition_map(dispositions)
    unresolved = []
    for report in reports:
        for finding in report.findings:
            if finding.status == GovernanceStatus.REMEDIATE:
                record = mapping.get(finding.finding_id)
                if record is None or not record.resolved:
                    unresolved.append(finding.finding_id)
    return tuple(sorted(unresolved))


def assess_release_candidate(
    *,
    assessment_id: str,
    reports: Sequence[ChallengeReport],
    registry: ChallengerRegistry,
    dispositions: Sequence[DispositionRecord] = (),
    stability: Sequence[StabilityObservation] = (),
    drift: Sequence[DriftObservation] = (),
    policy: PromotionPolicy = PromotionPolicy(),
    decision_actor: str = "HUMAN_REVIEWER",
) -> LifecycleAssessment:
    report_values = tuple(reports)
    if not report_values:
        raise ValueError("Lifecycle assessment requires challenge reports.")
    if policy.require_human_release_decision and decision_actor != "HUMAN_REVIEWER":
        raise ValueError("Only a human reviewer may make the release-candidate decision.")

    missing = registry.missing(tuple(policy.required_components))
    block_ids = []
    monitoring_ids = []
    for report in report_values:
        for finding in report.findings:
            if finding.status in {GovernanceStatus.BLOCK, GovernanceStatus.INVALID}:
                block_ids.append(finding.finding_id)
            elif finding.status == GovernanceStatus.PASS_WITH_MONITORING:
                monitoring_ids.append(finding.finding_id)
    for observation in stability:
        if observation.status in {GovernanceStatus.BLOCK, GovernanceStatus.INVALID}:
            block_ids.append(f"stability:{observation.dimension}")
        elif observation.status == GovernanceStatus.PASS_WITH_MONITORING:
            monitoring_ids.append(f"stability:{observation.dimension}")
    for observation in drift:
        if observation.status in {GovernanceStatus.BLOCK, GovernanceStatus.INVALID}:
            block_ids.append(f"drift:{observation.metric_name}")
        elif observation.status == GovernanceStatus.PASS_WITH_MONITORING:
            monitoring_ids.append(f"drift:{observation.metric_name}")

    unresolved = validate_dispositions(report_values, dispositions)
    if block_ids or missing:
        status = "BLOCK"
    elif unresolved:
        status = "REMEDIATE"
    else:
        status = RELEASE_CANDIDATE_STATUS

    evidence = {
        "assessment_id": assessment_id,
        "report_hashes": tuple(report.evidence_hash for report in report_values),
        "registry_hash": registry.registry_hash,
        "dispositions": tuple(dispositions),
        "stability": tuple(stability),
        "drift": tuple(drift),
        "status": status,
    }
    return LifecycleAssessment(
        assessment_id=assessment_id,
        status=status,
        eligible_for_release_candidate=status == RELEASE_CANDIDATE_STATUS,
        material_block_ids=tuple(sorted(set(block_ids))),
        unresolved_remediation_ids=unresolved,
        monitoring_ids=tuple(sorted(set(monitoring_ids))),
        registry_missing_components=missing,
        evidence_hash=evidence_sha256(evidence),
    )

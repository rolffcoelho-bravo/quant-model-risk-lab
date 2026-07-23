"""Governed, advisory-only GenAI evidence challenge controls."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .domain import (
    GENAI_BOUNDARY,
    ChallengeComponent,
    ChallengeFinding,
    ChallengeReport,
    GenAIEvidenceRecord,
    GovernanceStatus,
    evidence_sha256,
)


def record_from_mapping(payload: Mapping[str, Any]) -> GenAIEvidenceRecord:
    return GenAIEvidenceRecord(
        record_id=str(payload["record_id"]),
        prompt_id=str(payload["prompt_id"]),
        model_id=str(payload["model_id"]),
        model_version=str(payload["model_version"]),
        input_hash=str(payload["input_hash"]),
        output_hash=str(payload["output_hash"]),
        reviewer=str(payload["reviewer"]),
        disposition=str(payload["disposition"]),
        autonomous_model_approval=bool(payload.get("autonomous_model_approval", False)),
        changed_quantitative_result=bool(payload.get("changed_quantitative_result", False)),
        promoted_release=bool(payload.get("promoted_release", False)),
        boundary=str(payload.get("boundary", GENAI_BOUNDARY)),
    )


def load_record(path: str | Path) -> GenAIEvidenceRecord:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("GenAI evidence fixture must contain one JSON object.")
    return record_from_mapping(payload)


def validate_genai_record(record: GenAIEvidenceRecord, run_id: str = "gate7") -> ChallengeReport:
    checks = (
        (
            "advisory_boundary",
            record.boundary == GENAI_BOUNDARY,
            "GenAI evidence must retain the advisory-only boundary.",
        ),
        (
            "autonomous_model_approval",
            not record.autonomous_model_approval,
            "GenAI cannot approve a model.",
        ),
        (
            "quantitative_result_immutability",
            not record.changed_quantitative_result,
            "GenAI cannot alter validated quantitative results.",
        ),
        (
            "release_promotion_prohibition",
            not record.promoted_release,
            "GenAI cannot promote a release.",
        ),
    )
    findings = []
    for metric, passed, message in checks:
        status = GovernanceStatus.PASS if passed else GovernanceStatus.BLOCK
        findings.append(
            ChallengeFinding(
                finding_id=f"{record.record_id}:{metric}",
                component=ChallengeComponent.GOVERNED_GENAI,
                status=status,
                metric_name=metric,
                primary_value=1.0,
                challenger_value=1.0 if passed else 0.0,
                tolerance=0.0,
                absolute_difference=0.0 if passed else 1.0,
                relative_difference=0.0 if passed else 1.0,
                material=not passed,
                message=message,
                evidence_ids=(record.record_id,),
            )
        )
    return ChallengeReport(
        report_id=f"genai:{record.record_id}",
        run_id=run_id,
        challenger_id="governed_genai_evidence_challenger",
        component=ChallengeComponent.GOVERNED_GENAI,
        findings=tuple(findings),
        evidence_hash=evidence_sha256(record),
    )


def challenge_evidence_bundle(
    records: Sequence[GenAIEvidenceRecord],
    run_id: str = "gate7",
) -> tuple[ChallengeReport, ...]:
    values = tuple(records)
    if not values:
        raise ValueError("At least one GenAI evidence record is required.")
    if len({record.record_id for record in values}) != len(values):
        raise ValueError("GenAI evidence record identifiers must be unique.")
    return tuple(validate_genai_record(record, run_id) for record in values)


def advisory_summary(record: GenAIEvidenceRecord) -> dict[str, str | bool]:
    return {
        "record_id": record.record_id,
        "model": f"{record.model_id}:{record.model_version}",
        "reviewer": record.reviewer,
        "disposition": record.disposition,
        "advisory_only": record.boundary == GENAI_BOUNDARY,
        "record_hash": evidence_sha256(record),
    }

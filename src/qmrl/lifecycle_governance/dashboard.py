"""Machine-readable lifecycle dashboard and review card."""

from __future__ import annotations

from typing import Sequence

from .domain import (
    GENAI_BOUNDARY,
    ChallengeReport,
    DriftObservation,
    LifecycleAssessment,
    StabilityObservation,
    evidence_sha256,
)
from .reconciliation import disagreement_matrix


def build_lifecycle_dashboard(
    *,
    reports: Sequence[ChallengeReport],
    assessment: LifecycleAssessment,
    stability: Sequence[StabilityObservation] = (),
    drift: Sequence[DriftObservation] = (),
) -> dict[str, object]:
    report_values = tuple(reports)
    payload: dict[str, object] = {
        "schema_version": "1.0",
        "release_line": "v1.4",
        "gate": 7,
        "assessment_status": assessment.status,
        "eligible_for_release_candidate": assessment.eligible_for_release_candidate,
        "component_challenges": disagreement_matrix(report_values),
        "material_block_ids": assessment.material_block_ids,
        "unresolved_remediation_ids": assessment.unresolved_remediation_ids,
        "monitoring_ids": assessment.monitoring_ids,
        "stability": tuple(
            {
                "dimension": item.dimension,
                "status": item.status.value,
                "deviation": item.deviation,
            }
            for item in stability
        ),
        "drift": tuple(
            {
                "metric_name": item.metric_name,
                "status": item.status.value,
                "relative_shift": item.relative_shift,
            }
            for item in drift
        ),
        "genai_boundary": GENAI_BOUNDARY,
        "production_approval": False,
        "regulatory_approval": False,
    }
    payload["dashboard_hash"] = evidence_sha256(payload)
    return payload


def render_review_card(dashboard: dict[str, object]) -> str:
    return "\n".join(
        (
            "# v1.4 Gate 7 Lifecycle Review",
            f"Status: {dashboard['assessment_status']}",
            f"Release-candidate eligible: {dashboard['eligible_for_release_candidate']}",
            f"Material blocks: {len(dashboard['material_block_ids'])}",
            f"Unresolved remediations: {len(dashboard['unresolved_remediation_ids'])}",
            f"Monitoring items: {len(dashboard['monitoring_ids'])}",
            f"Evidence hash: {dashboard['dashboard_hash']}",
        )
    )

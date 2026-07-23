from __future__ import annotations

import pytest

from qmrl.lifecycle_governance import (
    ChallengeComponent,
    ChallengeOrchestrator,
    GovernanceStatus,
    assess_release_candidate,
    default_registry,
    reconcile_scalar,
    validate_dispositions,
)
from tests.v1_4_gate7_helpers import closed_disposition, complete_pass_reports, remediation_report


def test_complete_pass_bundle_is_release_candidate_validated():
    registry, reports = complete_pass_reports()
    assessment = assess_release_candidate(assessment_id="a1", reports=reports, registry=registry)
    assert assessment.status == "RELEASE_CANDIDATE_VALIDATED"
    assert assessment.eligible_for_release_candidate


def test_material_block_prevents_release_candidate():
    registry, reports = complete_pass_reports()
    spec = registry.get(ChallengeComponent.CAPITAL_KVA)
    blocked = reconcile_scalar(run_id="block", metric_name="kva", primary_value=1.0, challenger_value=2.0, spec=spec)
    assessment = assess_release_candidate(assessment_id="a2", reports=(*reports, blocked), registry=registry)
    assert assessment.status == "BLOCK"
    assert assessment.material_block_ids


def test_unresolved_remediation_prevents_promotion():
    registry, remediation = remediation_report()
    reports = ChallengeOrchestrator(registry).run_scalar_bundle(
        "pass", {component: (1.0, 1.0, "total") for component in registry.components}
    )
    assessment = assess_release_candidate(assessment_id="a3", reports=(*reports, remediation), registry=registry)
    assert assessment.status == "REMEDIATE"
    assert assessment.unresolved_remediation_ids


def test_closed_disposition_resolves_remediation():
    registry, remediation = remediation_report()
    reports = ChallengeOrchestrator(registry).run_scalar_bundle(
        "pass2", {component: (1.0, 1.0, "total") for component in registry.components}
    )
    disposition = closed_disposition(remediation)
    assessment = assess_release_candidate(
        assessment_id="a4", reports=(*reports, remediation), registry=registry, dispositions=(disposition,)
    )
    assert assessment.status == "RELEASE_CANDIDATE_VALIDATED"
    assert validate_dispositions((*reports, remediation), (disposition,)) == ()


def test_missing_registry_component_blocks_promotion():
    full = default_registry()
    incomplete_specs = tuple(spec for spec in full.specs if spec.component != ChallengeComponent.OPERATIONS)
    from qmrl.lifecycle_governance import ChallengerRegistry
    incomplete = ChallengerRegistry(incomplete_specs)
    reports = ChallengeOrchestrator(incomplete).run_scalar_bundle(
        "partial", {component: (1.0, 1.0, "total") for component in incomplete.components}
    )
    assessment = assess_release_candidate(assessment_id="a5", reports=reports, registry=incomplete)
    assert assessment.status == "BLOCK"
    assert "operations" in assessment.registry_missing_components


def test_genai_actor_cannot_make_release_candidate_decision():
    registry, reports = complete_pass_reports()
    with pytest.raises(ValueError, match="human reviewer"):
        assess_release_candidate(
            assessment_id="a6", reports=reports, registry=registry, decision_actor="GENAI"
        )

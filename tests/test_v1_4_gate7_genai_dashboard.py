from __future__ import annotations

from pathlib import Path

from qmrl.lifecycle_governance import (
    GENAI_BOUNDARY,
    GovernanceStatus,
    advisory_summary,
    assess_release_candidate,
    build_lifecycle_dashboard,
    challenge_evidence_bundle,
    load_record,
    render_review_card,
    validate_genai_record,
)
from tests.v1_4_gate7_helpers import complete_pass_reports


FIXTURES = Path("data/genai/fixtures")


def test_valid_genai_fixture_passes_advisory_controls():
    record = load_record(FIXTURES / "valid_advisory_review.json")
    report = validate_genai_record(record)
    assert report.status == GovernanceStatus.PASS
    assert record.boundary == GENAI_BOUNDARY


def test_autonomous_approval_fixture_is_blocked():
    record = load_record(FIXTURES / "invalid_autonomous_approval.json")
    report = validate_genai_record(record)
    assert report.status == GovernanceStatus.BLOCK
    assert report.material_blocks


def test_genai_bundle_requires_unique_record_ids():
    record = load_record(FIXTURES / "valid_advisory_review.json")
    import pytest
    with pytest.raises(ValueError, match="unique"):
        challenge_evidence_bundle((record, record))


def test_advisory_summary_contains_deterministic_record_hash():
    record = load_record(FIXTURES / "remediation_required_review.json")
    first = advisory_summary(record)
    second = advisory_summary(record)
    assert first == second
    assert first["advisory_only"] is True


def test_lifecycle_dashboard_is_hashed_and_machine_readable():
    registry, reports = complete_pass_reports()
    assessment = assess_release_candidate(assessment_id="dashboard", reports=reports, registry=registry)
    dashboard = build_lifecycle_dashboard(reports=reports, assessment=assessment)
    assert dashboard["eligible_for_release_candidate"] is True
    assert len(dashboard["dashboard_hash"]) == 64
    assert dashboard["genai_boundary"] == GENAI_BOUNDARY


def test_review_card_discloses_status_and_hash():
    registry, reports = complete_pass_reports()
    assessment = assess_release_candidate(assessment_id="card", reports=reports, registry=registry)
    dashboard = build_lifecycle_dashboard(reports=reports, assessment=assessment)
    card = render_review_card(dashboard)
    assert "RELEASE_CANDIDATE_VALIDATED" in card
    assert dashboard["dashboard_hash"] in card

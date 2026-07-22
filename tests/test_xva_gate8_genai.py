from __future__ import annotations

import json
from pathlib import Path

from qmrl.xva.genai_release_challenge import (
    ApprovedArtifact,
    ChallengeFinding,
    artifact_sha256,
    build_challenge_packet,
    validate_findings,
    validate_human_review,
)


def artifact(path: str = "docs/evidence.md") -> ApprovedArtifact:
    return ApprovedArtifact(path=path, sha256=artifact_sha256("evidence"))


def finding(citations: tuple[str, ...] = ("docs/evidence.md",), claim: str = "Evidence remains non-production.") -> ChallengeFinding:
    return ChallengeFinding(
        finding_id="F-001",
        severity="MONITORING",
        claim=claim,
        recommendation="Retain human review and monitoring.",
        artifact_citations=citations,
    )


def test_challenge_packet_hash_is_deterministic() -> None:
    first = build_challenge_packet([artifact()], instruction_version="v1")
    second = build_challenge_packet([artifact()], instruction_version="v1")
    assert first["packet_sha256"] == second["packet_sha256"]
    assert first["autonomous_model_approval"] is False


def test_valid_grounded_finding_passes_schema_control() -> None:
    result = validate_findings([finding()], [artifact()])
    assert result.valid
    assert result.status == "VALIDATED_PENDING_HUMAN_REVIEW"
    assert result.human_review_required


def test_uncited_finding_is_blocked() -> None:
    result = validate_findings([finding(())], [artifact()])
    assert not result.valid
    assert result.status == "BLOCK"


def test_unapproved_artifact_citation_is_blocked() -> None:
    result = validate_findings([finding(("docs/other.md",))], [artifact()])
    assert not result.valid
    assert "unapproved artifacts" in result.issues[0]


def test_production_approval_language_is_blocked() -> None:
    result = validate_findings(
        [finding(claim="The model is approved for production.")],
        [artifact()],
    )
    assert not result.valid
    assert any("prohibited approval language" in issue for issue in result.issues)


def test_static_human_review_covers_all_findings() -> None:
    findings = json.loads(
        Path("data/genai/outputs/xva_v1_3_release_challenge.json").read_text(
            encoding="utf-8-sig"
        )
    )["findings"]
    review = json.loads(
        Path("data/genai/outputs/xva_v1_3_human_review.json").read_text(
            encoding="utf-8-sig"
        )
    )
    assert validate_human_review(review, [item["finding_id"] for item in findings])
    assert review["autonomous_model_approval"] is False

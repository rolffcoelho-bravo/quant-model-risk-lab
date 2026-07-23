from __future__ import annotations
import pytest
from qmrl.release_consolidation import AssuranceCheck, CheckStatus, GateEvidence, ReleaseArtifact, ReleaseAssessment, RELEASE_BOUNDARY

def test_release_artifact_accepts_valid_sha():
    item = ReleaseArtifact("docs/a.md", "a" * 64, "documentation")
    assert item.required

def test_release_artifact_rejects_absolute_path():
    with pytest.raises(ValueError, match="repository-relative"):
        ReleaseArtifact("/tmp/a", "a" * 64, "x")

def test_release_artifact_rejects_invalid_hash():
    with pytest.raises(ValueError, match="SHA-256"):
        ReleaseArtifact("a", "bad", "x")

def test_gate_evidence_requires_gate_range():
    with pytest.raises(ValueError, match="interval"):
        GateEvidence(9, "PASS", ("e",))

def test_material_check_must_block():
    with pytest.raises(ValueError, match="Only BLOCK"):
        AssuranceCheck("c", CheckStatus.PASS, "e", material=True)

def test_release_assessment_preserves_boundaries():
    check = AssuranceCheck("c", CheckStatus.PASS, "e")
    result = ReleaseAssessment("RELEASED", True, (check,), boundary=RELEASE_BOUNDARY)
    assert result.production_approval is False and result.regulatory_approval is False

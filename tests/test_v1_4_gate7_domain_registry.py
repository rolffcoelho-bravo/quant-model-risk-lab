from __future__ import annotations

import pytest

from qmrl.lifecycle_governance import (
    CHALLENGE_BOUNDARY,
    ChallengeComponent,
    ChallengeFinding,
    ChallengeReport,
    ChallengerRegistry,
    ChallengerSpec,
    GovernanceStatus,
    default_registry,
    evidence_sha256,
)


def test_default_registry_covers_every_required_component():
    registry = default_registry()
    assert registry.missing() == ()
    assert len(registry.components) == 6


def test_registry_hash_is_deterministic():
    assert default_registry().registry_hash == default_registry().registry_hash


def test_registry_rejects_duplicate_component():
    spec = default_registry().specs[0]
    with pytest.raises(ValueError, match="Duplicate challenger component"):
        ChallengerRegistry((spec, spec))


def test_challenge_finding_rejects_nonfinite_values():
    with pytest.raises(ValueError, match="finite"):
        ChallengeFinding(
            "f", ChallengeComponent.MULTICURRENCY, GovernanceStatus.PASS,
            "metric", float("nan"), 1.0, 0.0, 0.0, 0.0,
        )


def test_report_worst_status_and_material_blocks():
    findings = (
        ChallengeFinding("f1", ChallengeComponent.CAPITAL_KVA, GovernanceStatus.PASS, "a", 1, 1, 0, 0, 0),
        ChallengeFinding("f2", ChallengeComponent.CAPITAL_KVA, GovernanceStatus.BLOCK, "b", 1, 2, 0, 1, 0.5, True),
    )
    report = ChallengeReport(
        "r", "run", "challenger", ChallengeComponent.CAPITAL_KVA,
        findings, evidence_sha256(findings), boundary=CHALLENGE_BOUNDARY,
    )
    assert report.status == GovernanceStatus.BLOCK
    assert report.material_blocks == (findings[1],)


def test_challenger_spec_requires_materiality_above_tolerance():
    with pytest.raises(ValueError, match="Materiality"):
        ChallengerSpec(
            ChallengeComponent.OPERATIONS, "id", "primary", "challenger",
            tolerance=1.0, materiality_threshold=0.5, required_evidence=("x",),
        )

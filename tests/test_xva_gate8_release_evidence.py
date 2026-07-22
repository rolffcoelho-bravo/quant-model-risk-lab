from __future__ import annotations

from dataclasses import replace

from qmrl.xva.release_evidence import (
    GateEvidence,
    ReleaseCandidateEvidence,
    canonical_release_hash,
    validate_release_candidate,
)


def evidence() -> ReleaseCandidateEvidence:
    return ReleaseCandidateEvidence(
        version="1.3.0",
        collected_test_count=350,
        required_check="Python 3.12 validation",
        ci_passed=True,
        gates=tuple(
            GateEvidence(
                gate=index,
                status=("PASS_WITH_MONITORING" if index in {4, 6, 8} else "PASS"),
                artifact_ref=f"configs/release_manifest_v1_3_gate{index}.json" if index < 8 else "configs/release_manifest_v1_3.json",
            )
            for index in range(1, 9)
        ),
        dashboard_status="PASS_WITH_MONITORING",
        lifecycle_status="PASS_WITH_MONITORING",
        genai_human_review_status="ACCEPTED_WITH_MONITORING",
        open_gates=("OPEN_NO_PUBLIC_QUOTE_DATA",),
        production_approval=False,
    )


def test_valid_release_is_pass_with_monitoring() -> None:
    result = validate_release_candidate(evidence())
    assert result.releasable
    assert result.status == "PASS_WITH_MONITORING"


def test_missing_gate_blocks_release() -> None:
    candidate = evidence()
    candidate = replace(candidate, gates=candidate.gates[:-1])
    assert validate_release_candidate(candidate).status == "BLOCK"


def test_ci_failure_blocks_release() -> None:
    assert validate_release_candidate(replace(evidence(), ci_passed=False)).status == "BLOCK"


def test_production_approval_claim_blocks_release() -> None:
    assert validate_release_candidate(replace(evidence(), production_approval=True)).status == "BLOCK"


def test_release_hash_is_deterministic() -> None:
    assert canonical_release_hash(evidence()) == canonical_release_hash(evidence())

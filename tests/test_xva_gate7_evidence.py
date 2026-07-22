from __future__ import annotations

import json

import pytest

from qmrl.xva import (
    build_release_candidate_package,
    component_decision,
    portfolio_promotion_decision,
    validate_release_candidate_payload,
    write_release_candidate_package,
)


def _package():
    component = component_decision("CVA", ["PASS"], material=True)
    decision = portfolio_promotion_decision(
        "v1.3.0-rc1", [component], benchmarks_passed=True, reproducibility_passed=True, required_ci_passed=True, evidence_complete=True
    )
    return build_release_candidate_package(
        decision, test_count=322, repository_commit="abc123", manifests=["gate1", "gate2", "gate3", "gate4", "gate5", "gate6", "gate7"]
    )


def test_release_candidate_package_has_verified_hash() -> None:
    package = _package()
    assert len(package.evidence_sha256) == 64
    validate_release_candidate_payload(package.payload)


def test_release_candidate_package_writes_canonical_json(tmp_path) -> None:
    package = _package()
    path = write_release_candidate_package(package, tmp_path / "evidence.json")
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert loaded["evidence_sha256"] == package.evidence_sha256


def test_tampered_release_candidate_payload_is_rejected() -> None:
    package = _package()
    tampered = dict(package.payload)
    tampered["test_count"] = 1
    with pytest.raises(ValueError):
        validate_release_candidate_payload(tampered)

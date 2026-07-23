from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def normalized_hash(path: Path) -> str:
    data = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(data).hexdigest()


def test_gate6_contracts_are_machine_readable():
    paths = sorted((ROOT / "configs").glob("v1_4_*contract.yml"))
    gate6 = []
    for path in paths:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if data.get("gate") == 6:
            gate6.append(path.name)
            assert data["release_line"] == "v1.4"
    assert len(gate6) == 6


def test_gate_sequence_requires_gate5_and_targets_operational_scale():
    sequence = yaml.safe_load(
        (ROOT / "configs/v1_4_gate_sequence.yml").read_text(encoding="utf-8")
    )
    gate = next(item for item in sequence["gates"] if item["gate"] == 6)
    assert gate["depends_on"] == [5]
    assert gate["target_status"] == "OPERATIONAL_SCALE_VALIDATED"


def test_gate6_manifest_locks_expected_test_surface():
    manifest = json.loads(
        (ROOT / "configs/release_manifest_v1_4_gate6.json").read_text(encoding="utf-8")
    )
    assert manifest["gate"] == 6
    assert manifest["base_main_commit"] == "a06e93c"
    assert manifest["validation"]["prior_collected_test_count"] == 582
    assert manifest["validation"]["new_test_count"] == 42
    assert manifest["validation"]["collected_test_count"] == 624


def test_gate6_manifest_hashes_all_declared_artifacts():
    manifest = json.loads(
        (ROOT / "configs/release_manifest_v1_4_gate6.json").read_text(encoding="utf-8")
    )
    assert len(manifest["artifacts"]) == 26
    for item in manifest["artifacts"]:
        path = ROOT / item["path"]
        assert path.is_file(), item["path"]
        assert normalized_hash(path) == item["sha256"], item["path"]


def test_gate6_governance_preserves_non_approval_boundaries():
    contract = yaml.safe_load(
        (ROOT / "configs/v1_4_operational_governance_contract.yml").read_text(
            encoding="utf-8"
        )
    )
    assert contract["boundaries"]["production_approval"] is False
    assert contract["boundaries"]["regulatory_approval"] is False
    assert contract["boundaries"]["quantitative_boundary"] == "QUANTITATIVE_EQUIVALENCE_REQUIRED"


def test_gate6_stops_before_gate7_lifecycle_implementation():
    manifest = json.loads(
        (ROOT / "configs/release_manifest_v1_4_gate6.json").read_text(encoding="utf-8")
    )
    assert manifest["next_gate"] == "independent_challenge_stability_and_lifecycle"
    assert not (ROOT / "src/qmrl/lifecycle").exists()
    assert manifest["boundaries"]["governed_genai_challenge_introduced"] is False

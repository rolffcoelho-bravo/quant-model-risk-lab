from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml

from qmrl.lifecycle_governance import benchmark_evidence, run_gate7_benchmarks


def normalized_hash(path: Path) -> str:
    data = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(data).hexdigest()


def test_gate7_manifest_and_test_surface_contract():
    manifest = json.loads(Path("configs/release_manifest_v1_4_gate7.json").read_text(encoding="utf-8"))
    assert manifest["base_main_commit"] == "bc1f22f"
    assert manifest["gate"] == 7
    assert manifest["target_status"] == "RELEASE_CANDIDATE_VALIDATED"
    assert manifest["validation"]["prior_collected_test_count"] == 624
    assert manifest["validation"]["new_test_count"] == 42
    assert manifest["validation"]["collected_test_count"] == 666


def test_gate7_manifest_hashes_reconcile():
    manifest = json.loads(Path("configs/release_manifest_v1_4_gate7.json").read_text(encoding="utf-8"))
    assert all(normalized_hash(Path(item["path"])) == item["sha256"] for item in manifest["artifacts"])


def test_gate_sequence_preserves_order_and_gate7_dependency():
    sequence = yaml.safe_load(Path("configs/v1_4_gate_sequence.yml").read_text(encoding="utf-8"))
    assert sequence["required_order"] == list(range(9))
    gate = next(item for item in sequence["gates"] if item["gate"] == 7)
    assert gate["depends_on"] == [6]
    assert gate["target_status"] == "RELEASE_CANDIDATE_VALIDATED"


def test_genai_contract_is_advisory_only():
    contract = yaml.safe_load(Path("configs/v1_4_genai_challenge_contract.yml").read_text(encoding="utf-8"))
    assert contract["role"] == "advisory_evidence_challenge"
    assert "autonomous_model_approval" in contract["prohibited"]
    assert contract["external_model_call_required_for_tests"] is False


def test_all_locked_gate7_benchmarks_confirm_expected_behaviour():
    results = run_gate7_benchmarks()
    assert len(results) == 9
    assert all(result.status == "PASS" for result in results)


def test_benchmark_evidence_is_hashed_and_complete():
    evidence = benchmark_evidence()
    assert evidence["all_expected_behaviour_confirmed"] is True
    assert len(evidence["evidence_hash"]) == 64
    assert evidence["gate"] == 7

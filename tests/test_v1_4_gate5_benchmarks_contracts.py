from pathlib import Path
import hashlib
import json

import yaml

from qmrl.allocation import run_gate5_benchmarks


ROOT = Path(__file__).resolve().parents[1]


def _sha256(path: Path) -> str:
    data = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(data).hexdigest()


def test_gate5_benchmarks_execute():
    result = run_gate5_benchmarks()
    assert result["additive_euler_status"] == "PASS"
    assert result["nonlinear_euler_valid"] is False
    assert result["challenger_status"] == "PASS"


def test_gate5_contracts_declare_boundaries():
    incremental = yaml.safe_load(
        (ROOT / "configs/v1_4_incremental_xva_contract.yml").read_text(encoding="utf-8")
    )
    allocation = yaml.safe_load(
        (ROOT / "configs/v1_4_marginal_allocation_contract.yml").read_text(encoding="utf-8")
    )
    governance = yaml.safe_load(
        (ROOT / "configs/v1_4_allocation_governance_contract.yml").read_text(encoding="utf-8")
    )
    assert incremental["boundary"] == "FULL_REVALUATION_PRIMARY_APPROXIMATION_DISCLOSED"
    assert allocation["boundary"] == "FULL_REVALUATION_PRIMARY_APPROXIMATION_DISCLOSED"
    assert governance["production_approval"] is False
    assert governance["regulatory_approval"] is False


def test_gate5_sequence_contract_matches_frozen_architecture():
    sequence = yaml.safe_load(
        (ROOT / "configs/v1_4_gate_sequence.yml").read_text(encoding="utf-8")
    )
    gate = next(item for item in sequence["gates"] if item["gate"] == 5)
    assert gate["depends_on"] == [3, 4]
    assert gate["target_status"] == "INCREMENTAL_ANALYTICS_VALIDATED"


def test_gate5_manifest_artifact_hashes_reconcile():
    manifest = json.loads(
        (ROOT / "configs/release_manifest_v1_4_gate5.json").read_text(encoding="utf-8")
    )
    assert manifest["validation"]["collected_test_count"] == 582
    assert manifest["validation"]["artifact_hash_policy"] == {
        "algorithm": "sha256",
        "encoding": "UTF-8",
        "text_line_endings": "LF",
    }
    for item in manifest["artifacts"]:
        assert _sha256(ROOT / item["path"]) == item["sha256"]

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from qmrl.portfolio import run_portfolio_benchmark_suite

SCHEMA = ROOT / "configs" / "v1_4_portfolio_schema_contract.yml"
VALIDATION = ROOT / "configs" / "v1_4_portfolio_validation_contract.yml"
LINEAGE = ROOT / "configs" / "v1_4_portfolio_lineage_contract.yml"
BENCHMARK = ROOT / "configs" / "v1_4_portfolio_benchmark_contract.yml"
MANIFEST = ROOT / "configs" / "release_manifest_v1_4_gate1.json"


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8-sig"))


def normalized_sha256(path: Path) -> str:
    data = path.read_bytes()
    normalized = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(normalized).hexdigest()


def test_benchmark_suite_passes_all_locked_cases() -> None:
    results = run_portfolio_benchmark_suite(BENCHMARK, root=ROOT)
    assert len(results) == 6
    assert all(result.passed for result in results)


def test_schema_contract_declares_canonical_entities() -> None:
    contract = load_yaml(SCHEMA)
    assert contract["gate"] == 1
    assert contract["status"] == "PORTFOLIO_CONTRACTS_VALIDATED"
    assert {
        "PortfolioSnapshot",
        "Counterparty",
        "NettingSet",
        "CollateralSet",
        "TradeRecord",
    } <= set(contract["canonical_entities"])


def test_validation_contract_blocks_partial_mapping() -> None:
    contract = load_yaml(VALIDATION)
    assert contract["portfolio_statuses"]["invalid"] == "BLOCK"
    assert contract["rejection_controls"]["partial_mapping"] is True
    assert (
        contract["downstream_calculation_permitted_only_when"]
        == "validation_status == PASS"
    )


def test_lineage_contract_requires_complete_calculation_identity() -> None:
    contract = load_yaml(LINEAGE)
    assert {
        "run_id",
        "portfolio_snapshot_id",
        "configuration_hash",
        "input_hash",
        "source_hash",
        "model_version",
        "random_seed",
    } <= set(contract["required_run_fields"])
    assert contract["hash_policy"]["algorithm"] == "sha256"


def test_fixture_inventory_contains_valid_and_invalid_evidence() -> None:
    fixture_names = {
        path.name
        for path in (ROOT / "data" / "portfolio" / "fixtures").glob("*.json")
    }
    assert "valid_reference_portfolio.json" in fixture_names
    assert {
        "invalid_missing_netting_set.json",
        "invalid_duplicate_trade.json",
        "invalid_counterparty_cycle.json",
        "invalid_collateral_mapping.json",
        "invalid_unknown_field.json",
    } <= fixture_names


def test_release_manifest_identity_and_boundaries() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8-sig"))
    assert manifest["release_line"] == "v1.4"
    assert manifest["gate"] == 1
    assert manifest["status"] == "PORTFOLIO_CONTRACTS_VALIDATED"
    assert manifest["base_release"]["tag"] == "v1.3.0"
    assert manifest["scope"]["portfolio_ingestion"] is True
    assert manifest["scope"]["multi_currency_calculation"] is False
    assert manifest["scope"]["mva"] is False
    assert manifest["scope"]["kva"] is False
    assert manifest["scope"]["production_approval"] is False
    assert manifest["scope"]["regulatory_approval"] is False


def test_release_manifest_records_test_and_ci_governance() -> None:
    validation = json.loads(
        MANIFEST.read_text(encoding="utf-8-sig")
    )["validation"]
    assert validation["prior_gate_test_count"] == 373
    assert validation["collected_test_count"] == 412
    assert validation["new_gate_tests"] == 39
    assert validation["required_check"] == "Python 3.12 validation"
    assert validation["pull_request_ci_required"] is True
    assert validation["post_merge_ci_required"] is True
    assert validation["human_squash_approval_required"] is True
    assert validation["artifact_hash_policy"] == {
        "algorithm": "sha256",
        "encoding": "UTF-8",
        "text_line_endings": "LF",
    }


def test_release_manifest_artifact_hashes_reconcile() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8-sig"))
    artifacts = manifest["artifacts"]
    assert len(artifacts) >= 18
    for item in artifacts:
        path = ROOT / item["path"]
        assert path.is_file(), item["path"]
        assert item["sha256"] == normalized_sha256(path)


def test_release_manifest_promotes_only_gate_2_next() -> None:
    next_gate = json.loads(MANIFEST.read_text(encoding="utf-8-sig"))["next_gate"]
    assert next_gate == {
        "gate": 2,
        "title": "Multi-currency exposure and collateral",
        "implementation_permitted_after_gate_1_merge": True,
    }

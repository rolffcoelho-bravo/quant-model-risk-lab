from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCOPE_PATH = ROOT / "configs" / "v1_4_scope_contract.yml"
ARCHITECTURE_PATH = ROOT / "configs" / "v1_4_architecture_contract.yml"
SEQUENCE_PATH = ROOT / "configs" / "v1_4_gate_sequence.yml"
MANIFEST_PATH = ROOT / "configs" / "release_manifest_v1_4_gate0.json"
BLUEPRINT_PATH = ROOT / "docs" / "v1_4_architecture_and_execution_blueprint.md"
TEST_PATH = ROOT / "tests" / "test_v1_4_gate0_contracts.py"


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8-sig"))


def sha256(path: Path) -> str:
    data = path.read_bytes()
    normalized = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(normalized).hexdigest()


def test_gate0_artifacts_exist() -> None:
    for path in (
        SCOPE_PATH,
        ARCHITECTURE_PATH,
        SEQUENCE_PATH,
        MANIFEST_PATH,
        BLUEPRINT_PATH,
        TEST_PATH,
    ):
        assert path.is_file(), path


def test_scope_identity_and_frozen_status() -> None:
    scope = load_yaml(SCOPE_PATH)
    assert scope["release_line"] == "v1.4"
    assert scope["gate"] == 0
    assert scope["status"] == "ARCHITECTURE_FROZEN"


def test_scope_preserves_v1_3_release_evidence() -> None:
    scope = load_yaml(SCOPE_PATH)
    base = scope["base_release"]
    assert base["version"] == "1.3.0"
    assert base["tag"] == "v1.3.0"
    assert base["immutable_historical_evidence"] is True
    assert base["semantic_reinterpretation_permitted"] is False


def test_scope_contains_required_institutional_capabilities() -> None:
    scope = load_yaml(SCOPE_PATH)
    identifiers = {item["id"] for item in scope["in_scope"]}
    assert {
        "portfolio_ingestion",
        "multi_currency_xva",
        "mva",
        "kva",
        "incremental_allocation",
        "operational_recalculation",
        "independent_governance",
    } <= identifiers


def test_scope_contains_required_exclusions() -> None:
    scope = load_yaml(SCOPE_PATH)
    exclusions = set(scope["out_of_scope"])
    assert "production trade capture" in exclusions
    assert "live market-data ingestion" in exclusions
    assert "SIMM certification" in exclusions
    assert "public claims of regulatory compliance" in exclusions


def test_gate0_has_no_quantitative_or_regulatory_approval() -> None:
    boundaries = load_yaml(SCOPE_PATH)["boundaries"]
    assert boundaries["production_approval"] is False
    assert boundaries["regulatory_approval"] is False
    assert boundaries["quantitative_implementation_in_gate_0"] is False
    assert boundaries["release_tag_creation_in_gate_0"] is False


def test_scope_required_artifact_inventory_is_exact() -> None:
    scope = load_yaml(SCOPE_PATH)
    assert set(scope["required_gate_0_artifacts"]) == {
        "docs/v1_4_architecture_and_execution_blueprint.md",
        "configs/v1_4_scope_contract.yml",
        "configs/v1_4_architecture_contract.yml",
        "configs/v1_4_gate_sequence.yml",
        "configs/release_manifest_v1_4_gate0.json",
        "tests/test_v1_4_gate0_contracts.py",
    }


def test_architecture_layers_are_ordered_and_complete() -> None:
    architecture = load_yaml(ARCHITECTURE_PATH)
    layers = architecture["layers"]
    assert [layer["id"] for layer in layers] == list(range(1, 9))
    assert len({layer["name"] for layer in layers}) == 8


def test_architecture_dependencies_are_acyclic_and_prior_only() -> None:
    architecture = load_yaml(ARCHITECTURE_PATH)
    for layer in architecture["layers"]:
        assert all(dependency < layer["id"] for dependency in layer["depends_on"])


def test_canonical_domain_entities_are_complete() -> None:
    entities = set(load_yaml(ARCHITECTURE_PATH)["canonical_entities"])
    assert {
        "PortfolioSnapshot",
        "Counterparty",
        "NettingSet",
        "CollateralSet",
        "TradeRecord",
        "AgreementTerms",
        "CurrencyDefinition",
        "CalculationRun",
        "EvidenceManifest",
    } <= entities


def test_calculation_run_lineage_is_mandatory() -> None:
    architecture = load_yaml(ARCHITECTURE_PATH)
    assert architecture["calculation_identity_required"] is True
    required = set(architecture["calculation_run_required_fields"])
    assert {
        "run_id",
        "valuation_date",
        "portfolio_snapshot_id",
        "model_version",
        "configuration_hash",
        "input_hash",
        "random_seed",
        "created_at_utc",
    } == required


def test_architecture_invariants_cover_key_model_boundaries() -> None:
    architecture = load_yaml(ARCHITECTURE_PATH)
    invariant_ids = {item["id"] for item in architecture["invariants"]}
    assert {
        "v1_3_composition",
        "run_identity",
        "no_hidden_aggregation",
        "mva_separation",
        "kva_boundary",
        "approximation_disclosure",
        "gate_0_no_quantitative_code",
    } == invariant_ids


def test_component_status_vocabulary_is_governed() -> None:
    architecture = load_yaml(ARCHITECTURE_PATH)
    assert architecture["permitted_component_statuses"] == [
        "PASS",
        "PASS_WITH_MONITORING",
        "REMEDIATE",
        "BLOCK",
    ]
    assert "BLOCK" in architecture["portfolio_promotion_rule"]


def test_gate_sequence_is_complete_and_ordered() -> None:
    sequence = load_yaml(SEQUENCE_PATH)
    assert sequence["required_order"] == list(range(9))
    assert [gate["gate"] for gate in sequence["gates"]] == list(range(9))


def test_gate_sequence_dependencies_follow_approved_graph() -> None:
    sequence = load_yaml(SEQUENCE_PATH)
    dependencies = {gate["gate"]: gate["depends_on"] for gate in sequence["gates"]}
    assert dependencies == {
        0: [],
        1: [0],
        2: [1],
        3: [2],
        4: [2],
        5: [3, 4],
        6: [5],
        7: [6],
        8: [7],
    }


def test_every_gate_has_capabilities_evidence_and_promotion_conditions() -> None:
    sequence = load_yaml(SEQUENCE_PATH)
    for gate in sequence["gates"]:
        assert gate["objective"]
        assert gate["required_capabilities"]
        assert gate["required_evidence"]
        assert gate["promotion_conditions"]
        assert gate["target_status"]


def test_gate0_explicitly_prohibits_quantitative_implementation() -> None:
    gate0 = load_yaml(SEQUENCE_PATH)["gates"][0]
    prohibited = set(gate0["prohibited_before_promotion"])
    assert {
        "portfolio ingestion implementation",
        "multi-currency calculation implementation",
        "MVA implementation",
        "KVA implementation",
        "incremental-XVA implementation",
    } <= prohibited


def test_blueprint_contains_required_architecture_sections() -> None:
    blueprint = BLUEPRINT_PATH.read_text(encoding="utf-8-sig")
    for heading in (
        "## 1. Executive decision",
        "## 4. Scope",
        "## 5. Target architecture",
        "## 6. Canonical domain model",
        "## 7. Quantitative specification",
        "## 8. Gated implementation sequence",
        "## 12. Testing strategy",
        "## 14. Model-risk governance",
        "## 19. Final architectural decision",
    ):
        assert heading in blueprint


def test_blueprint_documents_all_nine_gates() -> None:
    blueprint = BLUEPRINT_PATH.read_text(encoding="utf-8-sig")
    for gate in range(9):
        assert f"## Gate {gate} —" in blueprint


def test_manifest_identity_and_boundaries() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8-sig"))
    assert manifest["release_line"] == "v1.4"
    assert manifest["gate"] == 0
    assert manifest["status"] == "ARCHITECTURE_FROZEN"
    assert manifest["base_release"]["tag"] == "v1.3.0"
    assert manifest["scope"]["architecture_only"] is True
    assert manifest["scope"]["quantitative_implementation"] is False
    assert manifest["scope"]["production_approval"] is False
    assert manifest["scope"]["regulatory_approval"] is False
    assert manifest["scope"]["release_tag_created"] is False


def test_manifest_records_expanded_test_surface_and_ci_governance() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8-sig"))
    validation = manifest["validation"]
    assert validation["prior_release_test_count"] == 350
    assert validation["collected_test_count"] > 350
    assert validation["required_check"] == "Python 3.12 validation"
    assert validation["pull_request_ci_required"] is True
    assert validation["post_merge_ci_required"] is True
    assert validation["human_squash_approval_required"] is True
    assert validation["artifact_hash_policy"] == {
        "algorithm": "sha256",
        "encoding": "UTF-8",
        "text_line_endings": "LF",
    }


def test_manifest_artifact_hashes_reconcile() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8-sig"))
    artifacts = manifest["artifacts"]
    expected_paths = {
        "docs/v1_4_architecture_and_execution_blueprint.md",
        "configs/v1_4_scope_contract.yml",
        "configs/v1_4_architecture_contract.yml",
        "configs/v1_4_gate_sequence.yml",
        "tests/test_v1_4_gate0_contracts.py",
    }
    assert {item["path"] for item in artifacts} == expected_paths
    for item in artifacts:
        assert item["sha256"] == sha256(ROOT / item["path"])


def test_manifest_declares_gate1_as_the_only_next_implementation_gate() -> None:
    next_gate = json.loads(MANIFEST_PATH.read_text(encoding="utf-8-sig"))["next_gate"]
    assert next_gate == {
        "gate": 1,
        "title": "Canonical portfolio ingestion and lineage",
        "implementation_permitted_after_gate_0_merge": True,
    }

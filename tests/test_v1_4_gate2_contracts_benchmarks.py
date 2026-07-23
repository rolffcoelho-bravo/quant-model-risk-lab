from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml

from qmrl.multicurrency import run_multicurrency_benchmark_suite


ROOT = Path(__file__).resolve().parents[1]
CONFIGS = ROOT / "configs"


def normalized_hash(path: Path) -> str:
    data = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(data).hexdigest()


def test_gate2_yaml_contracts_parse():
    names = (
        "v1_4_multicurrency_contract.yml",
        "v1_4_fx_contract.yml",
        "v1_4_collateral_currency_contract.yml",
        "v1_4_multicurrency_benchmark_contract.yml",
    )
    for name in names:
        payload = yaml.safe_load((CONFIGS / name).read_text(encoding="utf-8"))
        assert payload["schema_version"] == "1.0"


def test_scope_contract_preserves_gate_boundaries():
    contract = yaml.safe_load(
        (CONFIGS / "v1_4_multicurrency_contract.yml").read_text(
            encoding="utf-8"
        )
    )
    assert contract["status"] == "MULTICURRENCY_EXPOSURE_VALIDATED"
    assert contract["scope"]["mva"] is False
    assert contract["scope"]["kva"] is False
    assert contract["scope"]["conversion_before_netting"] is True


def test_locked_benchmark_suite_passes():
    results = run_multicurrency_benchmark_suite(
        CONFIGS / "v1_4_multicurrency_benchmark_contract.yml"
    )
    assert len(results) == 8
    assert all(result.passed for result in results)


def test_release_manifest_artifacts_reconcile():
    manifest = json.loads(
        (CONFIGS / "release_manifest_v1_4_gate2.json").read_text(
            encoding="utf-8"
        )
    )
    assert manifest["validation"]["artifact_hash_policy"] == {
        "algorithm": "sha256",
        "encoding": "UTF-8",
        "text_line_endings": "LF",
    }
    for item in manifest["artifacts"]:
        assert normalized_hash(ROOT / item["path"]) == item["sha256"]


def test_gate2_documentation_contains_required_boundaries():
    content = (
        ROOT / "docs" / "v1_4_multicurrency_exposure_and_collateral.md"
    ).read_text(encoding="utf-8")
    for heading in (
        "# v1.4 Gate 2",
        "## Conversion-before-netting rule",
        "## Single-currency compatibility",
        "## Model boundaries",
    ):
        assert heading in content


def test_gate2_manifest_declares_next_gate():
    manifest = json.loads(
        (CONFIGS / "release_manifest_v1_4_gate2.json").read_text(
            encoding="utf-8"
        )
    )
    assert manifest["gate"] == 2
    assert manifest["validation"]["collected_test_count"] == 456
    assert manifest["next_gate"]["gate"] == 3
    assert manifest["next_gate"]["title"] == "Initial margin and MVA"

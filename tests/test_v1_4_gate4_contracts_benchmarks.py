from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import yaml

from qmrl.capital import run_capital_benchmarks

ROOT = Path(__file__).resolve().parents[1]


def normalized_sha256(path: Path) -> str:
    data = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(data).hexdigest()


def test_capital_contract_keeps_public_boundary() -> None:
    contract = yaml.safe_load((ROOT / "configs/v1_4_capital_contract.yml").read_text(encoding="utf-8"))
    assert contract["boundaries"]["label"] == "PUBLIC_CAPITAL_PROXY_NOT_REGULATORY_APPROVAL"
    assert contract["boundaries"]["regulatory_approval"] is False


def test_kva_contract_requires_zero_hurdle_rule() -> None:
    contract = yaml.safe_load((ROOT / "configs/v1_4_kva_contract.yml").read_text(encoding="utf-8"))
    assert contract["kva"]["zero_hurdle_zero_kva"] == "required"


def test_governance_contract_prohibits_regulatory_claims() -> None:
    contract = yaml.safe_load((ROOT / "configs/v1_4_capital_governance_contract.yml").read_text(encoding="utf-8"))
    assert "Basel_capital_approval" in contract["prohibited_claims"]
    assert contract["governance"]["production_approval"] is False


def test_attribution_contract_requires_all_dimensions() -> None:
    contract = yaml.safe_load((ROOT / "configs/v1_4_capital_attribution_contract.yml").read_text(encoding="utf-8"))
    assert set(contract["required_dimensions"]) == {"counterparty", "netting_set", "trade", "currency", "time_bucket"}


def test_locked_capital_benchmarks_reconcile() -> None:
    contract = yaml.safe_load((ROOT / "configs/v1_4_capital_benchmark_contract.yml").read_text(encoding="utf-8"))
    expected = {item["name"]: float(item["expected"]) for item in contract["benchmarks"]}
    observed = {item.name: item.observed for item in run_capital_benchmarks()}
    assert expected.keys() == observed.keys()
    for name in expected:
        assert np.isclose(observed[name], expected[name], atol=float(contract["absolute_tolerance"]), rtol=0.0)


def test_gate4_release_manifest_scope_is_correct() -> None:
    manifest = json.loads((ROOT / "configs/release_manifest_v1_4_gate4.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "CAPITAL_KVA_VALIDATED"
    assert manifest["validation"]["expected_total_tests"] == 540
    assert manifest["scope"]["incremental_XVA"] == "not_introduced"


def test_gate4_manifest_artifact_hashes_reconcile() -> None:
    manifest = json.loads((ROOT / "configs/release_manifest_v1_4_gate4.json").read_text(encoding="utf-8"))
    for item in manifest["artifacts"]:
        assert normalized_sha256(ROOT / item["path"]) == item["sha256"]

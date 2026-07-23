import hashlib
import json
from pathlib import Path

import yaml

from qmrl.margin import run_margin_benchmark_suite


ROOT = Path(__file__).resolve().parents[1]


def normalized_sha256(path: Path) -> str:
    data = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(data).hexdigest()


def test_margin_contract_preserves_proxy_and_separation_boundaries():
    contract = yaml.safe_load((ROOT / "configs/v1_4_margin_contract.yml").read_text())
    assert contract["proxy_label"] == "PUBLIC_PROXY_NOT_SIMM_OR_CCP"
    assert "mva_not_embedded_in_fva" in contract["invariants"]
    assert "certified_SIMM" in contract["prohibited_claims"]


def test_initial_margin_contract_approves_two_proxy_families():
    contract = yaml.safe_load((ROOT / "configs/v1_4_initial_margin_contract.yml").read_text())
    assert contract["historical_simulation"]["quantile_interpolation"] == "linear"
    assert contract["parametric"]["margin_period_scaling"] == "square_root_time"


def test_mva_contract_requires_component_separation():
    contract = yaml.safe_load((ROOT / "configs/v1_4_mva_contract.yml").read_text())
    assert contract["separation"]["mva_separate_from_fva"] is True
    assert contract["received_margin"]["benefit_allowed_only_when_reusable"] is True


def test_governance_contract_keeps_kva_outside_gate3():
    contract = yaml.safe_load((ROOT / "configs/v1_4_margin_governance_contract.yml").read_text())
    assert contract["downstream_boundaries"]["KVA"] == "not_introduced"
    assert contract["downstream_boundaries"]["production_approval"] is False


def test_locked_margin_benchmarks_all_pass():
    results = run_margin_benchmark_suite(ROOT / "configs/v1_4_margin_benchmark_contract.yml")
    assert len(results) == 8
    assert all(result.status == "PASS" for result in results)


def test_gate3_manifest_hashes_and_test_surface_reconcile():
    manifest = json.loads((ROOT / "configs/release_manifest_v1_4_gate3.json").read_text())
    assert manifest["status"] == "INITIAL_MARGIN_MVA_VALIDATED"
    assert manifest["validation"]["prior_gate_test_count"] == 456
    assert manifest["validation"]["new_gate_tests"] == 42
    assert manifest["validation"]["collected_test_count"] == 498
    assert manifest["scope"]["mva_separate_from_fva"] is True
    assert manifest["scope"]["KVA"] == "not_introduced"
    for artifact in manifest["artifacts"]:
        assert normalized_sha256(ROOT / artifact["path"]) == artifact["sha256"]

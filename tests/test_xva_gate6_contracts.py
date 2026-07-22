from __future__ import annotations

import json
from pathlib import Path


CONFIGS = (
    Path("configs/xva_wwr_dependence_contract.yml"),
    Path("configs/xva_stress_scenario_contract.yml"),
    Path("configs/xva_stress_governance_contract.yml"),
    Path("configs/xva_wwr_benchmark_contract.yml"),
    Path("configs/release_manifest_v1_3_gate6.json"),
)


def test_gate6_contracts_use_json_syntax_yaml() -> None:
    for path in CONFIGS:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
        assert isinstance(value, dict)
        assert value


def test_dependence_contract_preserves_base_and_stressed_results() -> None:
    contract = json.loads(CONFIGS[0].read_text(encoding="utf-8-sig"))
    assert contract["gate"] == "XVA_EXPOSURE_GATE_6"
    assert contract["baseline_result_preserved"] is True
    assert contract["arbitrary_correlation_forbidden"] is True


def test_stress_governance_requires_human_review() -> None:
    contract = json.loads(CONFIGS[2].read_text(encoding="utf-8-sig"))
    assert contract["severe_scenario_requires_approval"] is True
    assert contract["production_approval"] is False


def test_gate6_documentation_states_validation_boundary() -> None:
    content = Path("docs/xva_wrong_way_risk_and_stress.md").read_text(encoding="utf-8-sig")
    for phrase in (
        "Gaussian copula baseline",
        "Baseline preservation",
        "Stress-channel governance",
        "not a production stress engine",
    ):
        assert phrase in content

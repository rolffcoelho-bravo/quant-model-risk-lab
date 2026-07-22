from __future__ import annotations

import json
from pathlib import Path


CONTRACTS = (
    Path("configs/xva_dashboard_contract.yml"),
    Path("configs/xva_lifecycle_monitoring_contract.yml"),
    Path("configs/xva_genai_release_challenge_contract.yml"),
    Path("configs/xva_release_governance_contract.yml"),
    Path("configs/release_manifest_v1_3.json"),
)


def test_gate8_contracts_are_json_syntax_yaml() -> None:
    for path in CONTRACTS:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        assert payload
        assert payload.get("gate") == "XVA_RELEASE_GATE_8" or path.name == "release_manifest_v1_3.json"


def test_release_contract_preserves_human_and_nonproduction_boundaries() -> None:
    contract = json.loads(
        Path("configs/xva_release_governance_contract.yml").read_text(
            encoding="utf-8-sig"
        )
    )
    assert contract["human_release_approval_required"] is True
    assert contract["production_approval"] is False
    assert contract["required_check"] == "Python 3.12 validation"


def test_release_architecture_and_validation_matrix_are_institutional() -> None:
    architecture = Path("docs/xva_v1_3_release_validation.md").read_text(
        encoding="utf-8-sig"
    )
    matrix = Path("docs/validation_matrix.md").read_text(encoding="utf-8-sig")
    for phrase in (
        "Decision-grade dashboard",
        "Lifecycle monitoring",
        "Governed GenAI challenge",
        "not production approval",
    ):
        assert phrase in architecture
    assert "v1.3.0" in matrix
    assert "XVA exposure simulation" in matrix

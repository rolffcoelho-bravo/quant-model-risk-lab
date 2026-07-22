import json
from pathlib import Path

CONFIGS = (
    Path("configs/xva_integration_contract.yml"),
    Path("configs/xva_discount_curve_contract.yml"),
    Path("configs/xva_funding_curve_contract.yml"),
    Path("configs/xva_attribution_contract.yml"),
    Path("configs/xva_sensitivity_contract.yml"),
    Path("configs/xva_integration_benchmark_contract.yml"),
    Path("configs/release_manifest_v1_3_gate5.json"),
)

def test_gate5_contracts_use_json_syntax_yaml() -> None:
    for path in CONFIGS:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        assert payload

def test_gate5_preserves_human_approval_boundary() -> None:
    contract = json.loads(CONFIGS[0].read_text(encoding="utf-8-sig"))
    assert contract["human_review_required"] is True
    assert contract["production_approval"] is False
    assert contract["sign_convention"] == "total_adjustment = -CVA + DVA - FCA + FBA"

def test_architecture_documents_scope_and_next_gate() -> None:
    content = Path("docs/xva_integration_and_attribution.md").read_text(encoding="utf-8-sig")
    for phrase in (
        "Gate 5 is not a production XVA engine",
        "Attribution hierarchy",
        "Independent challenger and reconciliation",
        "Wrong-way risk, stress scenarios, and dependence controls remain Gate 6",
    ):
        assert phrase in content

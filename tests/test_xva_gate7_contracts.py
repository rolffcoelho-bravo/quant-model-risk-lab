from __future__ import annotations

import json
from pathlib import Path


CONFIGS = (
    Path("configs/xva_challenger_contract.yml"),
    Path("configs/xva_stability_contract.yml"),
    Path("configs/xva_promotion_contract.yml"),
    Path("configs/xva_gate7_benchmark_contract.yml"),
    Path("configs/release_manifest_v1_3_gate7.json"),
)


def test_gate7_contract_files_are_json_syntax_yaml() -> None:
    for path in CONFIGS:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        assert isinstance(data, dict)
        assert data


def test_promotion_contract_requires_human_review() -> None:
    contract = json.loads(Path("configs/xva_promotion_contract.yml").read_text(encoding="utf-8-sig"))
    assert contract["human_approval_required"] is True
    assert contract["production_approval"] is False


def test_stability_contract_contains_required_diagnostics() -> None:
    contract = json.loads(Path("configs/xva_stability_contract.yml").read_text(encoding="utf-8-sig"))
    assert {"path_count", "seed", "time_grid", "quantile", "wwr_correlation", "hazard_curve", "collateral", "attribution"}.issubset(set(contract["required_diagnostics"]))


def test_gate7_architecture_states_release_candidate_boundary() -> None:
    content = Path("docs/xva_independent_challenger_and_promotion.md").read_text(encoding="utf-8-sig")
    assert "release-candidate evidence package" in content
    assert "does not publish v1.3" in content
    assert "no material component classified as `BLOCK`" in content

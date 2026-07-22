from __future__ import annotations

import json
from pathlib import Path


CONFIGS = (
    Path("configs/xva_pathwise_exposure_contract.yml"),
    Path("configs/xva_exposure_aggregation_contract.yml"),
    Path("configs/xva_collateral_integration_contract.yml"),
    Path("configs/xva_exposure_integration_benchmark_contract.yml"),
    Path("configs/release_manifest_v1_3_gate3.json"),
)


def test_gate3_contract_files_use_json_syntax_yaml() -> None:
    for path in CONFIGS:
        assert path.exists(), path

        payload = json.loads(
            path.read_text(
                encoding="utf-8-sig"
            )
        )

        assert isinstance(payload, dict)
        assert payload


def test_gate3_model_contract_is_fail_closed() -> None:
    payload = json.loads(
        Path(
            "configs/xva_pathwise_exposure_contract.yml"
        ).read_text(
            encoding="utf-8-sig"
        )
    )

    assert payload["gate"] == "XVA_EXPOSURE_GATE_3"
    assert payload["production_approval"] is False
    assert payload["human_review_required"] is True


def test_gate3_architecture_preserves_credit_boundary() -> None:
    content = Path(
        "docs/xva_pathwise_exposure_integration.md"
    ).read_text(
        encoding="utf-8-sig"
    )

    for phrase in (
        "Pathwise trade-to-netting-set allocation",
        "Collateral state by path",
        "No cross-netting across legal sets",
        "not a counterparty credit calibration layer",
        "Gate 4",
    ):
        assert phrase in content


def test_gate3_release_manifest_records_expanded_surface() -> None:
    payload = json.loads(
        Path(
            "configs/release_manifest_v1_3_gate3.json"
        ).read_text(
            encoding="utf-8-sig"
        )
    )

    assert payload["test_count"] >= 211
    assert payload["previous_gate"] == "XVA_EXPOSURE_GATE_2"
    assert payload["next_gate"] == (
        "XVA_EXPOSURE_GATE_4_COUNTERPARTY_CREDIT_CALIBRATION"
    )

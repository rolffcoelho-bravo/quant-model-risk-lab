from __future__ import annotations

import json
from pathlib import Path


CONFIGS = (
    Path("configs/xva_exposure_model_contract.yml"),
    Path("configs/xva_time_grid.yml"),
    Path("configs/netting_set_contract.yml"),
    Path("configs/collateral_agreement_contract.yml"),
    Path("configs/xva_benchmark_contract.yml"),
    Path("configs/release_manifest_v1_3_gate1.json"),
)


def test_gate1_contract_files_are_json_syntax_yaml() -> None:
    for path in CONFIGS:
        assert path.exists(), path

        content = json.loads(
            path.read_text(
                encoding="utf-8-sig"
            )
        )

        assert isinstance(content, dict)
        assert content


def test_model_contract_preserves_human_approval_boundary() -> None:
    contract = json.loads(
        Path(
            "configs/xva_exposure_model_contract.yml"
        ).read_text(
            encoding="utf-8-sig"
        )
    )

    assert contract["gate"] == "XVA_EXPOSURE_GATE_1"
    assert contract["production_approval"] is False
    assert contract["human_review_required"] is True


def test_architecture_documents_gate1_boundaries() -> None:
    architecture = Path(
        "docs/xva_exposure_simulation_architecture.md"
    ).read_text(
        encoding="utf-8-sig"
    )

    for phrase in (
        "Time-grid control",
        "Netting-set representation",
        "Collateral as a state process",
        "Deterministic benchmark framework",
        "not a production exposure engine",
    ):
        assert phrase in architecture

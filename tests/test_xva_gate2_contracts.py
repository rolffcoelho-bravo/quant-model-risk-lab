from __future__ import annotations

import json
from pathlib import Path


CONFIGS = (
    Path("configs/xva_scenario_model_contract.yml"),
    Path("configs/xva_risk_factor_contract.yml"),
    Path("configs/xva_random_control.yml"),
    Path("configs/xva_future_value_contract.yml"),
    Path("configs/xva_scenario_benchmark_contract.yml"),
    Path("configs/release_manifest_v1_3_gate2.json"),
)


def test_gate2_contract_files_are_json_syntax_yaml() -> None:
    for path in CONFIGS:
        assert path.exists(), path

        content = json.loads(
            path.read_text(
                encoding="utf-8-sig"
            )
        )

        assert isinstance(content, dict)
        assert content


def test_scenario_contract_preserves_model_risk_boundaries() -> None:
    contract = json.loads(
        Path(
            "configs/xva_scenario_model_contract.yml"
        ).read_text(
            encoding="utf-8-sig"
        )
    )

    assert contract["gate"] == "XVA_EXPOSURE_GATE_2"
    assert contract["production_approval"] is False
    assert contract["human_review_required"] is True
    assert (
        contract["separation_controls"][
            "simulation_output_cannot_recalibrate_inputs"
        ]
        is True
    )
    assert (
        contract["separation_controls"][
            "credit_calibration_is_out_of_scope"
        ]
        is True
    )


def test_gate2_architecture_documents_required_controls() -> None:
    architecture = Path(
        "docs/xva_scenario_path_architecture.md"
    ).read_text(
        encoding="utf-8-sig"
    )

    for phrase in (
        "Random-number and variance-reduction controls",
        "Scenario cube",
        "Future-value cube",
        "Analytical challengers",
        "Calibration and simulation separation",
        "not a production Monte Carlo engine",
    ):
        assert phrase in architecture


def test_gate2_manifest_points_to_pathwise_exposure_integration() -> None:
    manifest = json.loads(
        Path(
            "configs/release_manifest_v1_3_gate2.json"
        ).read_text(
            encoding="utf-8-sig"
        )
    )

    assert (
        manifest["next_gate"]
        == "XVA_EXPOSURE_GATE_3_PATHWISE_EXPOSURE_INTEGRATION"
    )
    assert manifest["production_approval"] is False

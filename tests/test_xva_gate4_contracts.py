from __future__ import annotations

import json
from pathlib import Path


CONFIGS = (
    Path("configs/xva_credit_curve_contract.yml"),
    Path("configs/xva_credit_quote_contract.yml"),
    Path("configs/xva_recovery_lgd_contract.yml"),
    Path("configs/xva_credit_proxy_contract.yml"),
    Path("configs/xva_credit_benchmark_contract.yml"),
    Path("configs/release_manifest_v1_3_gate4.json"),
)


def test_gate4_contract_files_use_json_syntax_yaml() -> None:
    for path in CONFIGS:
        assert path.exists(), path
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        assert isinstance(payload, dict)
        assert payload


def test_gate4_curve_contract_is_fail_closed() -> None:
    payload = json.loads(
        Path("configs/xva_credit_curve_contract.yml").read_text(
            encoding="utf-8-sig"
        )
    )

    assert payload["gate"] == "XVA_EXPOSURE_GATE_4"
    assert payload["production_approval"] is False
    assert payload["human_review_required"] is True
    assert payload["probability_measure_separation"] is True


def test_gate4_architecture_preserves_xva_integration_boundary() -> None:
    content = Path("docs/xva_counterparty_credit_calibration.md").read_text(
        encoding="utf-8-sig"
    )

    for phrase in (
        "Risk-neutral versus historical separation",
        "Piecewise-constant hazard calibration",
        "Counterparty and own-credit separation",
        "Proxy hierarchy",
        "not a CVA, DVA, or FVA integration layer",
        "Gate 5",
    ):
        assert phrase in content


def test_gate4_manifest_records_credit_gate_sequence() -> None:
    payload = json.loads(
        Path("configs/release_manifest_v1_3_gate4.json").read_text(
            encoding="utf-8-sig"
        )
    )

    assert payload["test_count"] >= 211
    assert payload["previous_gate"] == "XVA_EXPOSURE_GATE_3"
    assert payload["next_gate"] == "XVA_EXPOSURE_GATE_5_XVA_INTEGRATION"

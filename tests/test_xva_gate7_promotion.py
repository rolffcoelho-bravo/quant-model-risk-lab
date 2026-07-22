from __future__ import annotations

import pytest

from qmrl.xva import component_decision, portfolio_promotion_decision


def _component(name: str, statuses: list[str], material: bool = True, findings: int = 0):
    return component_decision(name, statuses, material=material, unresolved_findings=findings)


def test_all_pass_components_promote() -> None:
    decision = portfolio_promotion_decision(
        "v1.3.0-rc1", [_component("CVA", ["PASS"]), _component("FVA", ["PASS"])],
        benchmarks_passed=True, reproducibility_passed=True, required_ci_passed=True, evidence_complete=True,
    )
    assert decision.status == "PASS"
    assert decision.production_approval is False


def test_monitoring_component_produces_pass_with_monitoring() -> None:
    decision = portfolio_promotion_decision(
        "v1.3.0-rc1", [_component("CVA", ["PASS_WITH_MONITORING"])],
        benchmarks_passed=True, reproducibility_passed=True, required_ci_passed=True, evidence_complete=True,
    )
    assert decision.status == "PASS_WITH_MONITORING"


def test_material_block_prevents_portfolio_pass() -> None:
    decision = portfolio_promotion_decision(
        "v1.3.0-rc1", [_component("WWR", ["BLOCK"], material=True)],
        benchmarks_passed=True, reproducibility_passed=True, required_ci_passed=True, evidence_complete=True,
    )
    assert decision.status == "BLOCK"
    assert decision.blocking_components == ("WWR",)


def test_failed_hard_gate_blocks_even_when_components_pass() -> None:
    decision = portfolio_promotion_decision(
        "v1.3.0-rc1", [_component("CVA", ["PASS"])],
        benchmarks_passed=False, reproducibility_passed=True, required_ci_passed=True, evidence_complete=True,
    )
    assert decision.status == "BLOCK"
    assert not decision.hard_gates_passed


def test_material_unresolved_finding_forces_block() -> None:
    component = _component("Collateral", ["PASS"], material=True, findings=1)
    assert component.status == "BLOCK"

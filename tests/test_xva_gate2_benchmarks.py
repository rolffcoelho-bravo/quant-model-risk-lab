from __future__ import annotations

from pathlib import Path

from qmrl.xva import (
    load_scenario_benchmark_contract,
    run_scenario_benchmark_suite,
)


CONTRACT = Path(
    "configs/xva_scenario_benchmark_contract.yml"
)


def test_scenario_contract_contains_locked_reference_cases() -> None:
    contract = load_scenario_benchmark_contract(
        CONTRACT
    )

    assert len(contract["benchmarks"]) == 8


def test_all_gate2_scenario_benchmarks_pass() -> None:
    results = run_scenario_benchmark_suite(
        CONTRACT
    )

    assert len(results) == 8
    assert {
        result.status
        for result in results
    } == {"PASS"}

from __future__ import annotations

from pathlib import Path

from qmrl.xva import (
    load_benchmark_contract,
    run_benchmark_suite,
)


CONTRACT = Path(
    "configs/xva_benchmark_contract.yml"
)


def test_benchmark_contract_contains_ten_reference_cases() -> None:
    contract = load_benchmark_contract(
        CONTRACT
    )

    assert len(contract["benchmarks"]) == 10


def test_all_gate1_reference_cases_pass() -> None:
    results = run_benchmark_suite(
        CONTRACT
    )

    assert len(results) == 10
    assert {
        result.status
        for result in results
    } == {"PASS"}
    assert max(
        result.max_abs_error
        for result in results
    ) <= 1e-10

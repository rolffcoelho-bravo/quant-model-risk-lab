from __future__ import annotations

from pathlib import Path

from qmrl.xva import (
    load_credit_benchmark_contract,
    run_credit_benchmark_suite,
)


CONTRACT = Path("configs/xva_credit_benchmark_contract.yml")


def test_gate4_benchmark_contract_contains_ten_cases() -> None:
    contract = load_credit_benchmark_contract(CONTRACT)
    assert len(contract["benchmarks"]) == 10


def test_all_gate4_credit_benchmarks_pass() -> None:
    results = run_credit_benchmark_suite(CONTRACT)

    assert len(results) == 10
    assert {result.status for result in results} == {"PASS"}
    assert max(result.max_abs_error for result in results) <= 1e-7

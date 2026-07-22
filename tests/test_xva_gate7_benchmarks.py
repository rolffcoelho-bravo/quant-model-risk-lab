from __future__ import annotations

from pathlib import Path

from qmrl.xva import load_gate7_benchmark_contract, run_gate7_benchmarks


CONTRACT = Path("configs/xva_gate7_benchmark_contract.yml")


def test_gate7_benchmark_contract_contains_twelve_cases() -> None:
    contract = load_gate7_benchmark_contract(CONTRACT)
    assert len(contract["benchmarks"]) == 12


def test_all_gate7_locked_benchmarks_pass() -> None:
    results = run_gate7_benchmarks(CONTRACT)
    assert len(results) == 12
    assert {result.status for result in results} == {"PASS"}

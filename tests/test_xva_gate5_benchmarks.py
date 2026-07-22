from pathlib import Path

from qmrl.xva import load_xva_integration_benchmark_contract, run_xva_integration_benchmark_suite

CONTRACT = Path("configs/xva_integration_benchmark_contract.yml")

def test_gate5_contract_contains_eleven_locked_cases() -> None:
    assert len(load_xva_integration_benchmark_contract(CONTRACT)["benchmarks"]) == 11

def test_all_gate5_benchmarks_pass() -> None:
    results = run_xva_integration_benchmark_suite(CONTRACT)
    assert len(results) == 11
    assert {result.status for result in results} == {"PASS"}

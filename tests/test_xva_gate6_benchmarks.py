from pathlib import Path

from qmrl.xva.wwr_benchmark import load_wwr_benchmark_contract, run_wwr_benchmark_suite


CONTRACT = Path("configs/xva_wwr_benchmark_contract.yml")


def test_benchmark_contract_has_eleven_cases() -> None:
    contract = load_wwr_benchmark_contract(CONTRACT)
    assert len(contract["benchmarks"]) == 11


def test_all_gate6_benchmarks_pass() -> None:
    results = run_wwr_benchmark_suite(CONTRACT)
    assert len(results) == 11
    assert {result.status for result in results} == {"PASS"}

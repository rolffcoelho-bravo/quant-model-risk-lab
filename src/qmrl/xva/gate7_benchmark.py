"""Locked independent-challenger, stability, and promotion benchmarks."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any

from .challenger import ToleranceBand, compare_component
from .promotion import component_decision, portfolio_promotion_decision
from .stability import StabilityThresholds, assess_stability


@dataclass(frozen=True)
class Gate7BenchmarkResult:
    benchmark_id: str
    status: str
    actual_status: str
    expected_status: str


def load_gate7_benchmark_contract(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if data.get("gate") != "XVA_EXPOSURE_GATE_7":
        raise ValueError("Unexpected Gate 7 benchmark contract.")
    if not isinstance(data.get("benchmarks"), list) or not data["benchmarks"]:
        raise ValueError("Gate 7 benchmark contract must contain cases.")
    return data


def evaluate_gate7_case(case: dict[str, Any]) -> str:
    case_type = case["type"]
    if case_type == "challenger":
        band = ToleranceBand(**case["tolerance"])
        return compare_component(
            case["component"],
            case["primary"],
            case["challenger"],
            band,
        ).status

    if case_type == "stability":
        thresholds = StabilityThresholds(**case["thresholds"])
        return assess_stability(
            case["diagnostic"],
            case["estimates"],
            thresholds,
            expect_monotone_error_reduction=bool(case.get("expect_monotone_error_reduction", False)),
        ).status

    if case_type == "promotion":
        components = [
            component_decision(
                item["component"],
                item["diagnostic_statuses"],
                material=bool(item["material"]),
                unresolved_findings=int(item.get("unresolved_findings", 0)),
            )
            for item in case["components"]
        ]
        return portfolio_promotion_decision(
            case["candidate_version"],
            components,
            benchmarks_passed=bool(case["hard_gates"]["benchmarks_passed"]),
            reproducibility_passed=bool(case["hard_gates"]["reproducibility_passed"]),
            required_ci_passed=bool(case["hard_gates"]["required_ci_passed"]),
            evidence_complete=bool(case["hard_gates"]["evidence_complete"]),
        ).status

    raise ValueError(f"Unsupported Gate 7 benchmark type: {case_type}")


def run_gate7_benchmarks(path: str | Path) -> tuple[Gate7BenchmarkResult, ...]:
    contract = load_gate7_benchmark_contract(path)
    results: list[Gate7BenchmarkResult] = []
    for case in contract["benchmarks"]:
        actual = evaluate_gate7_case(case)
        expected = case["expected_status"]
        results.append(
            Gate7BenchmarkResult(
                benchmark_id=case["benchmark_id"],
                status="PASS" if actual == expected else "FAIL",
                actual_status=actual,
                expected_status=expected,
            )
        )
    return tuple(results)

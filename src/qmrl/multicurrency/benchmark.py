"""Locked deterministic benchmark suite for v1.4 Gate 2."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .collateral import accrue_collateral
from .curves import TermCurve
from .domain import FXQuote
from .fx import FXScenarioMarket


@dataclass(frozen=True)
class MultiCurrencyBenchmarkResult:
    case_id: str
    observed: float
    expected: float
    tolerance: float
    passed: bool


def load_multicurrency_benchmark_contract(
    path: str | Path,
) -> dict[str, Any]:
    payload = yaml.safe_load(
        Path(path).read_text(encoding="utf-8-sig")
    )
    if not isinstance(payload, dict):
        raise ValueError("Benchmark contract must be a mapping.")
    if payload.get("schema_version") != "1.0":
        raise ValueError("Unsupported benchmark schema version.")
    return payload


def _evaluate(case: dict[str, Any]) -> float:
    kind = case["kind"]
    if kind == "identity_fx":
        return float(case["amount"])
    if kind == "direct_fx":
        return float(case["amount"]) * float(case["rate"])
    if kind == "inverse_fx":
        return float(case["amount"]) / float(case["rate"])
    if kind == "triangular_fx":
        return (
            float(case["amount"])
            * float(case["first_rate"])
            * float(case["second_rate"])
        )
    if kind == "collateral_net":
        return float(case["trade_value"]) - float(case["collateral_value"])
    if kind == "discount":
        curve = TermCurve(
            curve_id="benchmark",
            currency="USD",
            kind="discount",
            times=tuple(case["times"]),
            values=tuple(case["values"]),
        )
        return float(case["exposure"]) * curve.value(float(case["time"]))
    if kind == "remuneration":
        accrued = accrue_collateral(
            float(case["initial_balance"]),
            tuple(case["times"]),
            tuple(case["rates"]),
        )
        return accrued[-1]
    if kind == "triangulation_error":
        direct = float(case["direct_rate"])
        implied = float(case["first_rate"]) * float(case["second_rate"])
        return abs(direct - implied)
    raise ValueError(f"Unsupported benchmark kind: {kind}.")


def run_multicurrency_benchmark_suite(
    path: str | Path,
) -> tuple[MultiCurrencyBenchmarkResult, ...]:
    contract = load_multicurrency_benchmark_contract(path)
    results = []
    for case in contract["cases"]:
        observed = _evaluate(case)
        expected = float(case["expected"])
        tolerance = float(case.get("tolerance", 1.0e-12))
        results.append(
            MultiCurrencyBenchmarkResult(
                case_id=case["case_id"],
                observed=observed,
                expected=expected,
                tolerance=tolerance,
                passed=abs(observed - expected) <= tolerance,
            )
        )
    return tuple(results)

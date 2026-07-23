"""Deterministic Gate 1 ingestion benchmark runner."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .ingestion import (
    PortfolioIngestionError,
    PortfolioSchemaError,
    load_portfolio_snapshot,
)


@dataclass(frozen=True)
class PortfolioBenchmarkResult:
    case_id: str
    passed: bool
    observed_valid: bool | None
    observed_codes: tuple[str, ...]
    message: str


def load_portfolio_benchmark_contract(
    path: str | Path,
) -> dict[str, Any]:
    payload = yaml.safe_load(
        Path(path).read_text(encoding="utf-8-sig")
    )
    if not isinstance(payload, dict):
        raise ValueError("Benchmark contract must be an object.")
    return payload


def evaluate_portfolio_benchmark(
    case: dict[str, Any],
    *,
    root: str | Path,
) -> PortfolioBenchmarkResult:
    case_id = str(case["case_id"])
    expected_valid = case.get("expected_valid")
    expected_schema_error = bool(case.get("expected_schema_error", False))
    expected_codes = tuple(sorted(case.get("expected_codes", [])))
    path = Path(root) / str(case["fixture"])

    try:
        result = load_portfolio_snapshot(
            path,
            reject_invalid=False,
        )
    except (PortfolioSchemaError, ValueError) as exc:
        passed = expected_schema_error
        return PortfolioBenchmarkResult(
            case_id=case_id,
            passed=passed,
            observed_valid=None,
            observed_codes=(),
            message=(
                "Expected schema rejection."
                if passed
                else f"Unexpected schema rejection: {exc}"
            ),
        )

    observed_codes = tuple(sorted(set(result.validation.issue_codes)))
    passed = (
        not expected_schema_error
        and result.validation.is_valid is expected_valid
        and set(expected_codes) <= set(observed_codes)
    )

    expected_counts = case.get("expected_counts")
    if expected_counts is not None:
        passed = passed and result.snapshot.counts() == expected_counts

    return PortfolioBenchmarkResult(
        case_id=case_id,
        passed=passed,
        observed_valid=result.validation.is_valid,
        observed_codes=observed_codes,
        message="Benchmark matched." if passed else "Benchmark mismatch.",
    )


def run_portfolio_benchmark_suite(
    contract_path: str | Path,
    *,
    root: str | Path,
) -> tuple[PortfolioBenchmarkResult, ...]:
    contract = load_portfolio_benchmark_contract(contract_path)
    return tuple(
        evaluate_portfolio_benchmark(case, root=root)
        for case in contract["cases"]
    )

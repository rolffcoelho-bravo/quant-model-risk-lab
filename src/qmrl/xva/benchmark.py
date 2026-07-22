"""Configuration-driven deterministic XVA Gate 1 benchmarks."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
import json
from pathlib import Path
from typing import Any

import numpy as np

from .collateral import (
    CollateralAgreement,
    effective_collateral,
    simulate_collateral_path,
)
from .exposure import (
    collateralized_exposure,
    margin_period_of_risk_exposure,
)
from .netting import (
    NettingSet,
    Trade,
    aggregate_netting_set,
)


@dataclass(frozen=True)
class BenchmarkResult:
    """One benchmark evaluation and its validation status."""

    benchmark_id: str
    status: str
    tolerance: float
    max_abs_error: float
    actual: dict[str, Any]
    expected: dict[str, Any]


def load_benchmark_contract(
    path: str | Path,
) -> dict[str, Any]:
    """Load the JSON-syntax YAML 1.2 benchmark contract."""

    contract_path = Path(path)

    data = json.loads(
        contract_path.read_text(
            encoding="utf-8-sig"
        )
    )

    if data.get("gate") != "XVA_EXPOSURE_GATE_1":
        raise ValueError(
            "Unexpected benchmark contract gate."
        )

    benchmarks = data.get("benchmarks")

    if not isinstance(benchmarks, list) or not benchmarks:
        raise ValueError(
            "The benchmark contract must contain cases."
        )

    return data


def _agreement(
    values: dict[str, Any],
) -> CollateralAgreement:
    return CollateralAgreement(**values)


def _date_values(
    values: list[str],
) -> list[date]:
    return [
        date.fromisoformat(value)
        for value in values
    ]


def evaluate_reference_case(
    case: dict[str, Any],
) -> dict[str, Any]:
    """Evaluate one supported deterministic reference case."""

    case_type = case["type"]

    if case_type == "exposure":
        profile = collateralized_exposure(
            case["clean_values"],
            case["collateral_values"],
        )

        return {
            "positive_exposure": (
                profile.positive_exposure.tolist()
            ),
            "negative_exposure": (
                profile.negative_exposure.tolist()
            ),
        }

    if case_type == "collateral_path":
        agreement = _agreement(
            case["agreement"]
        )

        points = simulate_collateral_path(
            _date_values(case["dates"]),
            case["clean_values"],
            agreement,
        )

        effective = [
            point.effective_balance
            for point in points
        ]

        profile = collateralized_exposure(
            case["clean_values"],
            effective,
        )

        return {
            "effective_collateral": effective,
            "positive_exposure": (
                profile.positive_exposure.tolist()
            ),
            "negative_exposure": (
                profile.negative_exposure.tolist()
            ),
        }

    if case_type == "mpor":
        profile = margin_period_of_risk_exposure(
            case["clean_values"],
            case["collateral_values"],
            mpor_steps=int(case["mpor_steps"]),
        )

        return {
            "positive_exposure": (
                profile.positive_exposure.tolist()
            ),
            "negative_exposure": (
                profile.negative_exposure.tolist()
            ),
        }

    if case_type == "netting":
        netting_set = NettingSet(
            netting_set_id=case["netting_set_id"],
            counterparty_id=case["counterparty_id"],
            agreement_id=case["agreement_id"],
            settlement_currency=case["currency"],
            trade_ids=tuple(
                trade["trade_id"]
                for trade in case["trades"]
            ),
            netting_eligible=bool(
                case["netting_eligible"]
            ),
        )

        trades = [
            Trade(
                trade_id=trade["trade_id"],
                counterparty_id=case[
                    "counterparty_id"
                ],
                netting_set_id=case[
                    "netting_set_id"
                ],
                currency=case["currency"],
                clean_value=float(
                    trade["clean_value"]
                ),
            )
            for trade in case["trades"]
        ]

        result = aggregate_netting_set(
            trades,
            netting_set,
        )

        return {
            "clean_value": result.clean_value,
            "positive_exposure": (
                result.positive_exposure
            ),
            "negative_exposure": (
                result.negative_exposure
            ),
        }

    if case_type == "haircut":
        agreement = _agreement(
            case["agreement"]
        )

        effective = effective_collateral(
            float(case["collateral_face"]),
            agreement,
        )

        profile = collateralized_exposure(
            [case["clean_value"]],
            [effective],
        )

        return {
            "effective_collateral": effective,
            "positive_exposure": float(
                profile.positive_exposure[0]
            ),
            "negative_exposure": float(
                profile.negative_exposure[0]
            ),
        }

    raise ValueError(
        f"Unsupported benchmark case type: {case_type}"
    )


def _maximum_error(
    actual: Any,
    expected: Any,
) -> float:
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return float("inf")

        if set(actual) != set(expected):
            return float("inf")

        return max(
            (
                _maximum_error(
                    actual[key],
                    expected[key],
                )
                for key in expected
            ),
            default=0.0,
        )

    actual_array = np.asarray(
        actual,
        dtype=float,
    )

    expected_array = np.asarray(
        expected,
        dtype=float,
    )

    if actual_array.shape != expected_array.shape:
        return float("inf")

    return float(
        np.max(
            np.abs(
                actual_array
                - expected_array
            )
        )
        if actual_array.size
        else 0.0
    )


def run_benchmark_suite(
    path: str | Path,
) -> tuple[BenchmarkResult, ...]:
    """Run every reference case in the Gate 1 contract."""

    contract = load_benchmark_contract(path)
    results: list[BenchmarkResult] = []

    for case in contract["benchmarks"]:
        tolerance = float(
            case.get("tolerance", 1e-10)
        )

        actual = evaluate_reference_case(case)
        expected = case["expected"]
        maximum_error = _maximum_error(
            actual,
            expected,
        )

        results.append(
            BenchmarkResult(
                benchmark_id=case["benchmark_id"],
                status=(
                    "PASS"
                    if maximum_error <= tolerance
                    else "FAIL"
                ),
                tolerance=tolerance,
                max_abs_error=maximum_error,
                actual=actual,
                expected=expected,
            )
        )

    return tuple(results)

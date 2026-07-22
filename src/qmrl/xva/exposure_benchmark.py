"""Configuration-driven Gate 3 pathwise exposure benchmarks."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import json
from pathlib import Path
from typing import Any

import numpy as np

from .collateral import CollateralAgreement
from .future_value import FutureValueCube
from .netting import NettingSet
from .pathwise_exposure import (
    aggregate_pathwise_exposure,
    allocate_future_values,
    build_pathwise_exposure_cube,
    exposure_manifest,
    reconcile_pathwise_exposure,
    simulate_pathwise_collateral,
)


@dataclass(frozen=True)
class ExposureIntegrationBenchmarkResult:
    """One locked Gate 3 benchmark result."""

    benchmark_id: str
    status: str
    tolerance: float
    max_abs_error: float
    actual: dict[str, Any]
    expected: dict[str, Any]


def load_exposure_integration_benchmark_contract(
    path: str | Path,
) -> dict[str, Any]:
    """Load the JSON-syntax YAML 1.2 Gate 3 contract."""

    data = json.loads(
        Path(path).read_text(
            encoding="utf-8-sig"
        )
    )

    if data.get("gate") != "XVA_EXPOSURE_GATE_3":
        raise ValueError(
            "Unexpected exposure benchmark gate."
        )

    benchmarks = data.get("benchmarks")

    if (
        not isinstance(benchmarks, list)
        or not benchmarks
    ):
        raise ValueError(
            "Exposure integration benchmarks are required."
        )

    return data


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

    if isinstance(expected, str):
        return 0.0 if actual == expected else float("inf")

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

    if actual_array.size == 0:
        return 0.0

    return float(
        np.max(
            np.abs(
                actual_array
                - expected_array
            )
        )
    )


def _netting_set(
    payload: dict[str, Any],
) -> NettingSet:
    return NettingSet(
        netting_set_id=payload["netting_set_id"],
        counterparty_id=payload["counterparty_id"],
        agreement_id=payload["agreement_id"],
        settlement_currency=payload.get(
            "settlement_currency",
            "USD",
        ),
        trade_ids=tuple(payload["trade_ids"]),
        netting_eligible=payload.get(
            "netting_eligible",
            True,
        ),
        collateral_agreement_id=payload.get(
            "collateral_agreement_id"
        ),
        close_out_convention=payload.get(
            "close_out_convention",
            "replacement_cost",
        ),
        wrong_way_risk_classification=payload.get(
            "wrong_way_risk_classification",
            "none",
        ),
    )


def evaluate_exposure_integration_benchmark(
    case: dict[str, Any],
) -> dict[str, Any]:
    """Evaluate one deterministic Gate 3 integration case."""

    values = np.asarray(
        case["trade_values"],
        dtype=float,
    )

    times = np.asarray(
        case["times"],
        dtype=float,
    )

    trade_ids = tuple(case["trade_ids"])

    future_values = FutureValueCube(
        times=times,
        trade_ids=trade_ids,
        values=values,
        portfolio_values=np.sum(
            values,
            axis=2,
        ),
    )

    netting_sets = tuple(
        _netting_set(payload)
        for payload in case["netting_sets"]
    )

    agreements = {
        payload["agreement_id"]:
        CollateralAgreement(**payload)
        for payload in case.get(
            "agreements",
            [],
        )
    }

    dates = tuple(
        date.fromisoformat(value)
        for value in case["dates"]
    )

    netting = allocate_future_values(
        future_values,
        netting_sets,
        dates,
    )

    collateral = simulate_pathwise_collateral(
        netting,
        agreements,
    )

    exposure = build_pathwise_exposure_cube(
        netting,
        collateral,
        agreements,
    )

    aggregation = aggregate_pathwise_exposure(
        exposure,
        quantile=float(
            case.get("quantile", 0.95)
        ),
    )

    reconciliation = reconcile_pathwise_exposure(
        future_values,
        netting,
        collateral,
        exposure,
    )

    manifest = exposure_manifest(
        netting,
        collateral,
        exposure,
        aggregation,
    )

    metrics = case["metrics"]
    actual: dict[str, Any] = {}

    for metric in metrics:
        if metric == "clean_values":
            actual[metric] = (
                netting.clean_values.tolist()
            )
        elif metric == "gross_positive_values":
            actual[metric] = (
                netting.gross_positive_values.tolist()
            )
        elif metric == "effective_collateral":
            actual[metric] = (
                collateral.effective_balances.tolist()
            )
        elif metric == "face_balances":
            actual[metric] = (
                collateral.face_balances.tolist()
            )
        elif metric == "pending_collateral":
            actual[metric] = (
                collateral.pending_face_balances.tolist()
            )
        elif metric == "positive_exposure":
            actual[metric] = (
                exposure.positive_exposure.tolist()
            )
        elif metric == "negative_exposure":
            actual[metric] = (
                exposure.negative_exposure.tolist()
            )
        elif metric == "mpor_positive_exposure":
            actual[metric] = (
                exposure.mpor_positive_exposure.tolist()
            )
        elif metric == "portfolio_expected_positive":
            actual[metric] = (
                aggregation.portfolio_expected_positive.tolist()
            )
        elif metric == "portfolio_pfe":
            actual[metric] = (
                aggregation.portfolio_pfe.tolist()
            )
        elif metric == "counterparty_expected_positive":
            actual[metric] = (
                aggregation.counterparty_expected_positive.tolist()
            )
        elif metric == "reconciliation_status":
            actual[metric] = reconciliation.status
        elif metric == "manifest_hash_length":
            actual[metric] = len(
                manifest["exposure_sha256"]
            )
        else:
            raise ValueError(
                f"Unsupported benchmark metric: {metric}"
            )

    return actual


def run_exposure_integration_benchmark_suite(
    path: str | Path,
) -> tuple[
    ExposureIntegrationBenchmarkResult,
    ...,
]:
    """Run every locked Gate 3 integration benchmark."""

    contract = (
        load_exposure_integration_benchmark_contract(
            path
        )
    )

    results: list[
        ExposureIntegrationBenchmarkResult
    ] = []

    for case in contract["benchmarks"]:
        actual = (
            evaluate_exposure_integration_benchmark(
                case
            )
        )

        expected = case["expected"]

        tolerance = float(
            case.get("tolerance", 1e-10)
        )

        error = _maximum_error(
            actual,
            expected,
        )

        results.append(
            ExposureIntegrationBenchmarkResult(
                benchmark_id=case["benchmark_id"],
                status=(
                    "PASS"
                    if error <= tolerance
                    else "FAIL"
                ),
                tolerance=tolerance,
                max_abs_error=error,
                actual=actual,
                expected=expected,
            )
        )

    return tuple(results)

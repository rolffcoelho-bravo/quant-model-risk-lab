"""Configuration-driven Gate 2 scenario and valuation benchmarks."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

import numpy as np

from .future_value import (
    FXForwardTrade,
    ZeroCouponBondTrade,
    value_portfolio,
)
from .random_control import (
    RandomControl,
    generate_standard_normal,
)
from .risk_factors import (
    RiskFactorSet,
    RiskFactorSpec,
)
from .scenario_challenger import (
    compare_terminal_moments,
)
from .scenario_paths import (
    generate_scenario_cube,
    scenario_manifest,
)


@dataclass(frozen=True)
class ScenarioBenchmarkResult:
    """One Gate 2 benchmark and its locked validation status."""

    benchmark_id: str
    status: str
    tolerance: float
    error: float
    actual: Any
    expected: Any


def load_scenario_benchmark_contract(
    path: str | Path,
) -> dict[str, Any]:
    """Load the JSON-syntax YAML 1.2 scenario benchmark contract."""

    data = json.loads(
        Path(path).read_text(
            encoding="utf-8-sig"
        )
    )

    if data.get("gate") != "XVA_EXPOSURE_GATE_2":
        raise ValueError(
            "Unexpected scenario benchmark gate."
        )

    benchmarks = data.get("benchmarks")

    if not isinstance(benchmarks, list) or not benchmarks:
        raise ValueError(
            "Scenario benchmark cases are required."
        )

    return data


def _factor_set(
    payload: dict[str, Any],
) -> RiskFactorSet:
    factors = tuple(
        RiskFactorSpec(**factor)
        for factor in payload["factors"]
    )

    return RiskFactorSet(
        factors=factors,
        correlation=np.asarray(
            payload["correlation"],
            dtype=float,
        ),
        calibration_source=payload.get(
            "calibration_source",
            "locked_benchmark_parameters",
        ),
        calibration_as_of=payload.get(
            "calibration_as_of"
        ),
    )


def _maximum_error(
    actual: Any,
    expected: Any,
) -> float:
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


def evaluate_scenario_benchmark(
    case: dict[str, Any],
) -> tuple[Any, Any, float]:
    """Evaluate one governed Gate 2 benchmark case."""

    case_type = case["type"]

    if case_type == "seed_reproducibility":
        factor_set = _factor_set(
            case["factor_set"]
        )
        control = RandomControl(
            **case["random_control"]
        )
        times = np.asarray(
            case["times"],
            dtype=float,
        )
        first = generate_scenario_cube(
            factor_set,
            times,
            num_paths=int(case["num_paths"]),
            random_control=control,
        )
        second = generate_scenario_cube(
            factor_set,
            times,
            num_paths=int(case["num_paths"]),
            random_control=control,
        )
        first_hash = scenario_manifest(
            first,
            factor_set,
        )["scenario_sha256"]
        second_hash = scenario_manifest(
            second,
            factor_set,
        )["scenario_sha256"]
        actual = 1.0 if first_hash == second_hash else 0.0
        expected = 1.0
        return actual, expected, abs(actual - expected)

    if case_type == "antithetic_mean":
        control = RandomControl(
            **case["random_control"]
        )
        draws = generate_standard_normal(
            control,
            num_paths=int(case["num_paths"]),
            num_steps=int(case["num_steps"]),
            num_factors=int(case["num_factors"]),
        )
        actual = float(
            np.max(
                np.abs(
                    np.mean(
                        draws,
                        axis=0,
                    )
                )
            )
        )
        expected = 0.0
        return actual, expected, abs(actual)

    if case_type == "correlation_recovery":
        control = RandomControl(
            **case["random_control"]
        )
        draws = generate_standard_normal(
            control,
            num_paths=int(case["num_paths"]),
            num_steps=1,
            num_factors=2,
        )[:, 0, :]
        target = np.asarray(
            case["correlation"],
            dtype=float,
        )
        eigenvalues, eigenvectors = np.linalg.eigh(
            target
        )
        square_root = (
            eigenvectors
            @ np.diag(
                np.sqrt(
                    np.clip(
                        eigenvalues,
                        0.0,
                        None,
                    )
                )
            )
            @ eigenvectors.T
        )
        correlated = draws @ square_root
        actual = float(
            np.corrcoef(
                correlated.T
            )[0, 1]
        )
        expected = float(target[0, 1])
        return actual, expected, abs(actual - expected)

    if case_type in {
        "deterministic_path",
        "gbm_moment",
        "vasicek_moment",
        "manifest_metadata",
        "future_value_cube",
    }:
        factor_set = _factor_set(
            case["factor_set"]
        )
        cube = generate_scenario_cube(
            factor_set,
            np.asarray(
                case["times"],
                dtype=float,
            ),
            num_paths=int(case["num_paths"]),
            random_control=RandomControl(
                **case["random_control"]
            ),
        )

        if case_type == "deterministic_path":
            factor_name = case["factor_name"]
            actual = cube.factor_values(
                factor_name
            )[0].tolist()
            expected = case["expected_values"]
            return (
                actual,
                expected,
                _maximum_error(actual, expected),
            )

        if case_type in {
            "gbm_moment",
            "vasicek_moment",
        }:
            check = compare_terminal_moments(
                cube,
                factor_set,
                case["factor_name"],
            )
            actual = (
                check.mean_relative_error
                if case["moment"] == "mean"
                else check.variance_relative_error
            )
            expected = 0.0
            return actual, expected, abs(actual)

        if case_type == "manifest_metadata":
            manifest = scenario_manifest(
                cube,
                factor_set,
            )
            actual = [
                manifest["num_paths"],
                manifest["num_times"],
                len(manifest["factor_names"]),
                len(manifest["scenario_sha256"]),
            ]
            expected = case["expected"]
            return (
                actual,
                expected,
                _maximum_error(actual, expected),
            )

        trades = []

        for trade_payload in case["trades"]:
            trade_type = trade_payload.pop(
                "trade_type"
            )

            if trade_type == "fx_forward":
                trades.append(
                    FXForwardTrade(
                        **trade_payload
                    )
                )
            elif trade_type == "zero_coupon_bond":
                trades.append(
                    ZeroCouponBondTrade(
                        **trade_payload
                    )
                )
            else:
                raise ValueError(
                    f"Unsupported trade type: {trade_type}"
                )

        future_values = value_portfolio(
            cube,
            trades,
        )

        actual = [
            float(
                future_values.portfolio_values[
                    0,
                    index,
                ]
            )
            for index in case[
                "observation_indices"
            ]
        ]
        expected = case["expected"]
        return (
            actual,
            expected,
            _maximum_error(actual, expected),
        )

    raise ValueError(
        f"Unsupported benchmark type: {case_type}"
    )


def run_scenario_benchmark_suite(
    path: str | Path,
) -> tuple[ScenarioBenchmarkResult, ...]:
    """Run every locked Gate 2 reference case."""

    contract = load_scenario_benchmark_contract(
        path
    )
    results: list[
        ScenarioBenchmarkResult
    ] = []

    for original_case in contract["benchmarks"]:
        case = json.loads(
            json.dumps(original_case)
        )
        tolerance = float(
            case.get("tolerance", 1e-10)
        )
        actual, expected, error = (
            evaluate_scenario_benchmark(case)
        )
        results.append(
            ScenarioBenchmarkResult(
                benchmark_id=case[
                    "benchmark_id"
                ],
                status=(
                    "PASS"
                    if error <= tolerance
                    else "FAIL"
                ),
                tolerance=tolerance,
                error=float(error),
                actual=actual,
                expected=expected,
            )
        )

    return tuple(results)

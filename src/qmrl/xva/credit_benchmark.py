"""Configuration-driven Gate 4 credit-calibration benchmarks."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
import json
from pathlib import Path
from typing import Any

import numpy as np

from .credit_curve import (
    CreditQuote,
    RecoveryAssumption,
    build_flat_credit_curve,
    calibrate_piecewise_credit_curve,
    credit_curve_manifest,
    credit_curve_sensitivity,
    reprice_credit_quotes,
    validate_credit_quotes,
)
from .credit_proxy import (
    CreditProxyCandidate,
    select_credit_proxy,
)


@dataclass(frozen=True)
class CreditCalibrationBenchmarkResult:
    """One locked Gate 4 benchmark result."""

    benchmark_id: str
    status: str
    tolerance: float
    max_abs_error: float
    actual: dict[str, Any]
    expected: dict[str, Any]


def load_credit_benchmark_contract(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if payload.get("gate") != "XVA_EXPOSURE_GATE_4":
        raise ValueError("Unexpected credit benchmark gate.")
    benchmarks = payload.get("benchmarks")
    if not isinstance(benchmarks, list) or not benchmarks:
        raise ValueError("Credit calibration benchmarks are required.")
    return payload


def _quotes(case: dict[str, Any], as_of: date) -> tuple[CreditQuote, ...]:
    return tuple(
        CreditQuote(
            quote_id=item["quote_id"],
            obligor_id=case.get("obligor_id", "CP1"),
            tenor_years=float(item["tenor_years"]),
            spread_bps=float(item["spread_bps"]),
            as_of_date=as_of - timedelta(days=int(item.get("age_days", 0))),
            source_id=item.get("source_id", "BENCHMARK"),
            quote_type=item.get("quote_type", "cds"),
            probability_measure=item.get("probability_measure", "risk_neutral"),
            currency=item.get("currency", "USD"),
            seniority=item.get("seniority", "senior_unsecured"),
        )
        for item in case.get("quotes", [])
    )


def _recovery(case: dict[str, Any], as_of: date) -> RecoveryAssumption:
    return RecoveryAssumption(
        obligor_id=case.get("obligor_id", "CP1"),
        recovery_rate=float(case.get("recovery_rate", 0.40)),
        as_of_date=as_of,
        source_id="BENCHMARK-RECOVERY",
    )


def evaluate_credit_benchmark(case: dict[str, Any]) -> dict[str, Any]:
    case_type = case["type"]
    as_of = date.fromisoformat(case.get("as_of_date", "2026-01-02"))

    if case_type == "flat_survival":
        curve = build_flat_credit_curve(
            curve_id="FLAT",
            obligor_id="CP1",
            role="counterparty",
            probability_measure="risk_neutral",
            currency="USD",
            as_of_date=as_of,
            recovery_rate=float(case["recovery_rate"]),
            spread_bps=float(case["spread_bps"]),
            node_times=case["node_times"],
        )
        terminal = float(case["terminal_time"])
        return {
            "hazard_rate": curve.hazard_rate(terminal),
            "survival_probability": curve.survival_probability(terminal),
            "cumulative_pd": curve.cumulative_default_probability(terminal),
        }

    if case_type == "piecewise_repricing":
        quotes = _quotes(case, as_of)
        curve = calibrate_piecewise_credit_curve(
            quotes,
            _recovery(case, as_of),
            curve_id="PIECEWISE",
            role="counterparty",
            as_of_date=as_of,
            required_tenors=[quote.tenor_years for quote in quotes],
        )
        report = reprice_credit_quotes(curve, quotes)
        survival = curve.survival_probabilities(curve.node_times)
        return {
            "max_abs_repricing_error_bps": report.max_abs_error_bps,
            "hazards_non_negative": bool(np.all(curve.hazard_rates >= 0.0)),
            "survival_monotone": bool(np.all(np.diff(survival) <= 1e-12)),
        }

    if case_type == "probability_reconciliation":
        curve = build_flat_credit_curve(
            curve_id="PD-RECON",
            obligor_id="CP1",
            role="counterparty",
            probability_measure="risk_neutral",
            currency="USD",
            as_of_date=as_of,
            recovery_rate=float(case["recovery_rate"]),
            spread_bps=float(case["spread_bps"]),
            node_times=case["node_times"],
        )
        marginal = curve.marginal_default_probabilities()
        terminal_pd = curve.cumulative_default_probability(float(curve.node_times[-1]))
        return {
            "marginal_pd_sum": float(np.sum(marginal)),
            "terminal_cumulative_pd": terminal_pd,
        }

    if case_type == "stale_quote_rejection":
        rejected = False
        try:
            validate_credit_quotes(
                _quotes(case, as_of),
                as_of_date=as_of,
                max_age_days=int(case["max_age_days"]),
            )
        except ValueError:
            rejected = True
        return {"rejected": rejected}

    if case_type == "missing_tenor_rejection":
        rejected = False
        try:
            validate_credit_quotes(
                _quotes(case, as_of),
                as_of_date=as_of,
                max_age_days=5,
                required_tenors=case["required_tenors"],
            )
        except ValueError:
            rejected = True
        return {"rejected": rejected}

    if case_type == "proxy_hierarchy":
        candidates = tuple(
            CreditProxyCandidate(
                candidate_id=item["candidate_id"],
                obligor_id="CP1",
                proxy_obligor_id=item["proxy_obligor_id"],
                level=item["level"],
                tenor_years=float(item["tenor_years"]),
                spread_bps=float(item["spread_bps"]),
                basis_adjustment_bps=float(item.get("basis_adjustment_bps", 0.0)),
                as_of_date=as_of - timedelta(days=int(item.get("age_days", 0))),
                source_id="BENCHMARK",
            )
            for item in case["candidates"]
        )
        selected = select_credit_proxy(
            candidates,
            as_of_date=as_of,
            max_age_days=int(case["max_age_days"]),
            required_tenor=float(case["required_tenor"]),
            expected_measure="risk_neutral",
            expected_currency="USD",
            expected_seniority="senior_unsecured",
        )
        return {
            "selected_candidate_id": selected.selected_candidate_id,
            "selected_level": selected.selected_level,
            "adjusted_spread_bps": selected.adjusted_spread_bps,
            "human_review_required": selected.human_review_required,
        }

    if case_type == "extrapolation_rejection":
        curve = build_flat_credit_curve(
            curve_id="NO-EXTRAP",
            obligor_id="CP1",
            role="counterparty",
            probability_measure="risk_neutral",
            currency="USD",
            as_of_date=as_of,
            recovery_rate=0.40,
            spread_bps=100.0,
            node_times=[1.0, 3.0],
            extrapolation_mode="forbidden",
        )
        rejected = False
        try:
            curve.survival_probability(5.0)
        except ValueError:
            rejected = True
        return {"rejected": rejected}

    if case_type in {"spread_sensitivity", "recovery_sensitivity"}:
        quotes = _quotes(case, as_of)
        sensitivity = credit_curve_sensitivity(
            quotes,
            _recovery(case, as_of),
            curve_id="SENSITIVITY",
            role="counterparty",
            as_of_date=as_of,
            parallel_spread_bump_bps=float(case.get("parallel_spread_bump_bps", 1.0)),
            recovery_bump=float(case.get("recovery_bump", 0.01)),
        )
        if case_type == "spread_sensitivity":
            return {
                "positive_pd_delta": sensitivity.parallel_spread_pd_delta > 0.0,
                "max_abs_repricing_error_bps": sensitivity.max_quote_repricing_error_bps,
            }
        return {
            "positive_pd_delta": sensitivity.recovery_pd_delta > 0.0,
            "max_abs_repricing_error_bps": sensitivity.max_quote_repricing_error_bps,
        }

    if case_type == "manifest_hash":
        curve = build_flat_credit_curve(
            curve_id="MANIFEST",
            obligor_id="CP1",
            role="counterparty",
            probability_measure="risk_neutral",
            currency="USD",
            as_of_date=as_of,
            recovery_rate=0.40,
            spread_bps=100.0,
            node_times=[1.0, 3.0, 5.0],
        )
        manifest = credit_curve_manifest(curve)
        return {
            "hash_length": len(str(manifest["credit_curve_sha256"])),
            "role": manifest["role"],
            "probability_measure": manifest["probability_measure"],
        }

    raise ValueError(f"Unsupported credit benchmark type: {case_type}")


def _maximum_error(actual: Any, expected: Any) -> float:
    if isinstance(expected, dict):
        if not isinstance(actual, dict) or set(actual) != set(expected):
            return float("inf")
        return max(
            (_maximum_error(actual[key], expected[key]) for key in expected),
            default=0.0,
        )
    if isinstance(expected, (str, bool)):
        return 0.0 if actual == expected else float("inf")
    actual_array = np.asarray(actual, dtype=float)
    expected_array = np.asarray(expected, dtype=float)
    if actual_array.shape != expected_array.shape:
        return float("inf")
    if actual_array.size == 0:
        return 0.0
    return float(np.max(np.abs(actual_array - expected_array)))


def run_credit_benchmark_suite(
    path: str | Path,
) -> tuple[CreditCalibrationBenchmarkResult, ...]:
    contract = load_credit_benchmark_contract(path)
    results: list[CreditCalibrationBenchmarkResult] = []

    for case in contract["benchmarks"]:
        actual = evaluate_credit_benchmark(case)
        expected = case["expected"]
        tolerance = float(case.get("tolerance", 1e-10))
        error = _maximum_error(actual, expected)
        results.append(
            CreditCalibrationBenchmarkResult(
                benchmark_id=case["benchmark_id"],
                status="PASS" if error <= tolerance else "FAIL",
                tolerance=tolerance,
                max_abs_error=error,
                actual=actual,
                expected=expected,
            )
        )

    return tuple(results)

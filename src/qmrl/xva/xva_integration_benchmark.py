"""Configuration-driven Gate 5 CVA/DVA/FVA benchmarks."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import json
from pathlib import Path
from typing import Any

import numpy as np

from .credit_curve import build_flat_credit_curve
from .xva_attribution import (
    allocate_xva_to_trades,
    equal_trade_weights,
    reconcile_xva,
)
from .xva_integration import (
    DiscountCurve,
    FundingCurve,
    XVAExposureInput,
    XVAIntegrationPolicy,
    integrate_xva,
    xva_manifest,
)
from .xva_sensitivity import run_standard_xva_sensitivities


@dataclass(frozen=True)
class XVAIntegrationBenchmarkResult:
    benchmark_id: str
    status: str
    tolerance: float
    max_abs_error: float
    actual: dict[str, Any]
    expected: dict[str, Any]


def load_xva_integration_benchmark_contract(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if payload.get("gate") != "XVA_EXPOSURE_GATE_5":
        raise ValueError("Unexpected XVA integration benchmark gate.")
    cases = payload.get("benchmarks")
    if not isinstance(cases, list) or not cases:
        raise ValueError("Gate 5 benchmark cases are required.")
    return payload


def _environment(case: dict[str, Any]):
    as_of = date.fromisoformat(case.get("as_of_date", "2026-01-02"))
    times = np.asarray(case.get("times", [0.0, 1.0]), dtype=float)
    positive = np.asarray(case.get("expected_positive", [[0.0], [100.0]]), dtype=float)
    negative = np.asarray(case.get("expected_negative", np.zeros_like(positive)), dtype=float)
    set_ids = tuple(case.get("netting_set_ids", ["NS1"]))
    cp_ids = tuple(case.get("counterparty_ids", ["CP1"]))
    exposure = XVAExposureInput(
        times=times,
        netting_set_ids=set_ids,
        counterparty_ids=cp_ids,
        expected_positive=positive,
        expected_negative=negative,
        mpor_expected_positive=np.asarray(
            case.get("mpor_expected_positive", positive),
            dtype=float,
        ),
        mpor_expected_negative=np.asarray(
            case.get("mpor_expected_negative", negative),
            dtype=float,
        ),
    )

    node_times = case.get("credit_node_times", [float(times[-1])])
    counterparty_curves = {}
    cp_spreads = case.get("counterparty_spreads_bps", {})
    for cp_id in dict.fromkeys(cp_ids):
        counterparty_curves[cp_id] = build_flat_credit_curve(
            curve_id=f"{cp_id}-CURVE",
            obligor_id=cp_id,
            role="counterparty",
            probability_measure="risk_neutral",
            currency="USD",
            as_of_date=as_of,
            recovery_rate=float(case.get("counterparty_recovery", 0.40)),
            spread_bps=float(cp_spreads.get(cp_id, case.get("counterparty_spread_bps", 100.0))),
            node_times=node_times,
        )
    own_curve = build_flat_credit_curve(
        curve_id="OWN-CURVE",
        obligor_id="BANK",
        role="own",
        probability_measure="risk_neutral",
        currency="USD",
        as_of_date=as_of,
        recovery_rate=float(case.get("own_recovery", 0.40)),
        spread_bps=float(case.get("own_spread_bps", 120.0)),
        node_times=node_times,
    )
    discount_rate = float(case.get("discount_rate", 0.0))
    discount = DiscountCurve(
        curve_id="OIS",
        currency="USD",
        as_of_date=as_of,
        times=times,
        discount_factors=np.exp(-discount_rate * times),
    )
    funding = FundingCurve(
        curve_id="FUNDING",
        currency="USD",
        as_of_date=as_of,
        times=times,
        borrowing_spreads_bps=np.full(times.shape, float(case.get("borrowing_spread_bps", 0.0))),
        lending_spreads_bps=np.full(times.shape, float(case.get("lending_spread_bps", 0.0))),
    )
    policy = XVAIntegrationPolicy(
        valuation_mode=case.get("valuation_mode", "bilateral"),
        exposure_rule=case.get("exposure_rule", "interval_end"),
        fva_basis=case.get("fva_basis", "collateralized"),
        funding_survival_mode=case.get("funding_survival_mode", "none"),
    )
    return exposure, counterparty_curves, own_curve, discount, funding, policy


def evaluate_xva_integration_benchmark(case: dict[str, Any]) -> dict[str, Any]:
    exposure, cp_curves, own, discount, funding, policy = _environment(case)
    result = integrate_xva(
        exposure,
        counterparty_curves=cp_curves,
        own_curve=own,
        discount_curve=discount,
        funding_curve=funding,
        policy=policy,
    )
    case_type = case["type"]

    if case_type in {"unilateral_cva", "bilateral_cva", "dva", "fca", "fba", "total_identity"}:
        return {
            "cva": result.cva,
            "dva": result.dva,
            "fca": result.fca,
            "fba": result.fba,
            "fva": result.fva,
            "total_adjustment": result.total_adjustment,
        }
    if case_type == "netting_set_attribution":
        return {
            "set_cva_sum": float(np.sum(result.cva_by_netting_set)),
            "portfolio_cva": result.cva,
            "set_fca_sum": float(np.sum(result.fca_by_netting_set)),
            "portfolio_fca": result.fca,
        }
    if case_type == "counterparty_attribution":
        return {
            "counterparty_cva_sum": float(np.sum(result.cva_by_counterparty)),
            "portfolio_cva": result.cva,
            "counterparty_count": len(result.unique_counterparty_ids),
        }
    if case_type == "trade_allocation":
        mapping = case["trade_to_netting_set"]
        allocation = allocate_xva_to_trades(result, equal_trade_weights(mapping))
        return {
            "trade_cva_sum": float(np.sum(allocation.cva)),
            "portfolio_cva": result.cva,
            "trade_total_sum": float(np.sum(allocation.total_adjustment)),
            "portfolio_total": result.total_adjustment,
        }
    if case_type == "challenger_reconciliation":
        reconciliation = reconcile_xva(
            exposure,
            result,
            counterparty_curves=cp_curves,
            own_curve=own,
            discount_curve=discount,
            funding_curve=funding,
            policy=policy,
        )
        return {
            "status": reconciliation.status,
            "max_error": max(
                reconciliation.challenger_cva_error,
                reconciliation.challenger_dva_error,
                reconciliation.challenger_fca_error,
                reconciliation.challenger_fba_error,
                reconciliation.bucket_to_set_error,
                reconciliation.set_to_counterparty_error,
                reconciliation.component_identity_error,
            ),
        }
    if case_type == "sensitivity_direction":
        sensitivity = run_standard_xva_sensitivities(
            exposure,
            counterparty_curves=cp_curves,
            own_curve=own,
            discount_curve=discount,
            funding_curve=funding,
            policy=policy,
        )
        return {
            "cp_spread_increases_cva": sensitivity.counterparty_spread_cva_delta > 0.0,
            "own_spread_increases_dva": sensitivity.own_spread_dva_delta > 0.0,
            "funding_bump_increases_fca": sensitivity.funding_cost_fca_delta > 0.0,
            "manifest_hash_length": len(xva_manifest(exposure, result, policy)["calculation_sha256"]),
        }
    raise ValueError(f"Unsupported Gate 5 benchmark type: {case_type}")


def _maximum_error(actual: Any, expected: Any) -> float:
    if isinstance(expected, dict):
        if not isinstance(actual, dict) or set(actual) != set(expected):
            return float("inf")
        return max(
            (_maximum_error(actual[key], expected[key]) for key in expected),
            default=0.0,
        )
    if isinstance(expected, str) or isinstance(expected, bool):
        return 0.0 if actual == expected else float("inf")
    left = np.asarray(actual, dtype=float)
    right = np.asarray(expected, dtype=float)
    if left.shape != right.shape:
        return float("inf")
    return float(np.max(np.abs(left - right))) if left.size else 0.0


def run_xva_integration_benchmark_suite(
    path: str | Path,
) -> tuple[XVAIntegrationBenchmarkResult, ...]:
    contract = load_xva_integration_benchmark_contract(path)
    results = []
    for case in contract["benchmarks"]:
        actual = evaluate_xva_integration_benchmark(case)
        expected = case["expected"]
        tolerance = float(case.get("tolerance", 1e-10))
        error = _maximum_error(actual, expected)
        results.append(
            XVAIntegrationBenchmarkResult(
                benchmark_id=case["benchmark_id"],
                status="PASS" if error <= tolerance else "FAIL",
                tolerance=tolerance,
                max_abs_error=error,
                actual=actual,
                expected=expected,
            )
        )
    return tuple(results)

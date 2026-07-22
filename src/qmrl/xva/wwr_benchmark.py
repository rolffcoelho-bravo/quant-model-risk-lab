"""Locked wrong-way-risk and stress benchmarks for XVA Gate 6."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from .credit_curve import CreditCurve
from .pathwise_exposure import PathwiseExposureCube
from .wrong_way_risk import WWRDependenceSpec, calculate_wwr_cva, wwr_manifest
from .xva_integration import DiscountCurve, FundingCurve, XVAExposureInput, XVAIntegrationPolicy
from .xva_stress import XVAStressScenario, evaluate_xva_stress, stress_manifest


@dataclass(frozen=True)
class WWRBenchmarkResult:
    benchmark_id: str
    status: str
    actual: float | str
    expected_relation: str


def load_wwr_benchmark_contract(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if data.get("gate") != "XVA_EXPOSURE_GATE_6":
        raise ValueError("Unexpected WWR benchmark gate.")
    if not isinstance(data.get("benchmarks"), list) or not data["benchmarks"]:
        raise ValueError("WWR benchmark contract must contain cases.")
    return data


def _credit_curve(obligor: str, role: str, hazard: float = 0.20) -> CreditCurve:
    return CreditCurve(
        curve_id=f"{obligor}-CURVE",
        obligor_id=obligor,
        role=role,
        probability_measure="risk_neutral",
        currency="USD",
        as_of_date=date(2026, 1, 2),
        recovery_rate=0.40,
        node_times=np.array([0.5, 1.0, 2.0]),
        hazard_rates=np.array([hazard, hazard, hazard]),
        source_quote_spreads_bps=np.array([1200.0, 1200.0, 1200.0]),
        source_quote_types=("cds", "cds", "cds"),
    )


def _discount_curve() -> DiscountCurve:
    return DiscountCurve(
        curve_id="USD-OIS",
        currency="USD",
        as_of_date=date(2026, 1, 2),
        times=np.array([0.0, 0.5, 1.0, 2.0]),
        discount_factors=np.exp(-0.03 * np.array([0.0, 0.5, 1.0, 2.0])),
    )


def _funding_curve() -> FundingCurve:
    return FundingCurve(
        curve_id="USD-FUNDING",
        currency="USD",
        as_of_date=date(2026, 1, 2),
        times=np.array([0.0, 0.5, 1.0, 2.0]),
        borrowing_spreads_bps=np.array([80.0, 80.0, 90.0, 100.0]),
        lending_spreads_bps=np.array([20.0, 20.0, 25.0, 30.0]),
    )


def _pathwise_cube() -> PathwiseExposureCube:
    paths = 200
    times = np.array([0.0, 0.5, 1.0, 2.0])
    scale = np.linspace(0.20, 2.00, paths)[:, None]
    base = np.array([0.0, 40.0, 70.0, 100.0])[None, :]
    positive = (scale * base)[:, :, None]
    negative = np.zeros_like(positive)
    clean = positive.copy()
    collateral = np.zeros_like(positive)
    indices = np.tile(np.arange(times.size)[:, None], (1, 1))
    return PathwiseExposureCube(
        times=times,
        dates=(date(2026, 1, 2), date(2026, 7, 2), date(2027, 1, 2), date(2028, 1, 2)),
        netting_set_ids=("NS1",),
        counterparty_ids=("CP1",),
        clean_values=clean,
        collateral_values=collateral,
        net_values=clean,
        uncollateralized_positive=positive,
        uncollateralized_negative=negative,
        positive_exposure=positive,
        negative_exposure=negative,
        mpor_positive_exposure=positive,
        mpor_negative_exposure=negative,
        mpor_target_indices=indices,
    )


def _exposure_input() -> XVAExposureInput:
    cube = _pathwise_cube()
    expected = np.mean(cube.positive_exposure, axis=0)
    negative = np.zeros_like(expected)
    return XVAExposureInput(
        times=cube.times,
        netting_set_ids=cube.netting_set_ids,
        counterparty_ids=cube.counterparty_ids,
        expected_positive=expected,
        expected_negative=negative,
        mpor_expected_positive=expected,
        mpor_expected_negative=negative,
    )


def _spec(correlation: float, classification: str) -> WWRDependenceSpec:
    return WWRDependenceSpec(
        dependence_id=f"DEP-{classification}",
        netting_set_id="NS1",
        counterparty_id="CP1",
        market_factor_id="FX-USD-BRL",
        classification=classification,
        channel="fx",
        correlation=correlation,
        as_of_date=date(2026, 1, 2),
        calibration_source="LOCKED_BENCHMARK",
        rationale="Deterministic Gate 6 benchmark.",
        approved=True,
    )


def evaluate_wwr_benchmark(case: dict[str, Any]) -> WWRBenchmarkResult:
    case_type = case["type"]
    cube = _pathwise_cube()
    cp = {"CP1": _credit_curve("CP1", "counterparty")}
    own = _credit_curve("BANK", "own", hazard=0.05)
    discount = _discount_curve()

    if case_type in {"independence", "wwr", "rwr", "boundary", "manifest"}:
        rho = float(case.get("correlation", 0.0))
        classification = case.get("classification", "independent")
        result = calculate_wwr_cva(
            cube,
            counterparty_curves=cp,
            discount_curve=discount,
            dependence_specs={"NS1": _spec(rho, classification)},
            own_curve=own,
        )
        if case_type == "independence":
            actual = abs(result.uplift)
            passed = actual <= float(case["tolerance"])
            relation = "abs(uplift) <= tolerance"
        elif case_type == "wwr":
            actual = result.uplift
            passed = actual > 0.0
            relation = "uplift > 0"
        elif case_type == "rwr":
            actual = result.uplift
            passed = actual < 0.0
            relation = "uplift < 0"
        elif case_type == "boundary":
            actual = result.dependent_cva
            passed = math.isfinite(actual) and actual >= 0.0
            relation = "finite dependent CVA"
        else:
            first = wwr_manifest(cube, result, {"NS1": _spec(rho, classification)})
            second = wwr_manifest(cube, result, {"NS1": _spec(rho, classification)})
            actual = first["sha256"]
            passed = first["sha256"] == second["sha256"]
            relation = "deterministic manifest"
        return WWRBenchmarkResult(case["benchmark_id"], "PASS" if passed else "FAIL", actual, relation)

    exposure = _exposure_input()
    funding = _funding_curve()
    base_kwargs = dict(
        counterparty_curves=cp,
        own_curve=own,
        discount_curve=discount,
        funding_curve=funding,
        policy=XVAIntegrationPolicy(),
    )

    if case_type == "governance":
        try:
            XVAStressScenario(
                scenario_id="UNAPPROVED-SEVERE",
                channel="systemic",
                severity="severe",
                as_of_date=date(2026, 1, 2),
                calibration_source="BENCHMARK",
                rationale="Expected rejection.",
                approved=False,
            )
        except ValueError:
            return WWRBenchmarkResult(case["benchmark_id"], "PASS", "REJECTED", "unapproved severe scenario rejected")
        return WWRBenchmarkResult(case["benchmark_id"], "FAIL", "ACCEPTED", "unapproved severe scenario rejected")

    scenario_parameters = dict(
        scenario_id=case["benchmark_id"],
        channel=case.get("channel", "systemic"),
        severity="moderate",
        as_of_date=date(2026, 1, 2),
        calibration_source="LOCKED_BENCHMARK",
        rationale="Deterministic stress benchmark.",
        approved=True,
    )
    scenario_parameters.update(case.get("parameters", {}))
    scenario = XVAStressScenario(**scenario_parameters)
    stress = evaluate_xva_stress(exposure, scenario=scenario, **base_kwargs)

    if case_type == "hazard_stress":
        actual = stress.cva_delta
        passed = actual > 0.0
        relation = "CVA delta > 0"
    elif case_type == "exposure_stress":
        actual = stress.cva_delta
        passed = actual > 0.0
        relation = "CVA delta > 0"
    elif case_type == "funding_stress":
        actual = stress.fca_delta
        passed = actual > 0.0
        relation = "FCA delta > 0"
    elif case_type == "discount_stress":
        actual = stress.cva_delta
        passed = actual < 0.0
        relation = "CVA delta < 0"
    elif case_type == "reconciliation":
        actual = stress.total_adjustment_delta - (-stress.cva_delta + stress.dva_delta - stress.fca_delta + stress.fba_delta)
        passed = abs(actual) <= float(case["tolerance"])
        relation = "component delta reconciliation"
    elif case_type == "stress_manifest":
        first = stress_manifest(stress, scenario)
        second = stress_manifest(stress, scenario)
        actual = first["sha256"]
        passed = first["sha256"] == second["sha256"]
        relation = "deterministic manifest"
    else:
        raise ValueError(f"Unsupported Gate 6 benchmark type: {case_type}")

    return WWRBenchmarkResult(case["benchmark_id"], "PASS" if passed else "FAIL", actual, relation)


def run_wwr_benchmark_suite(path: str | Path) -> tuple[WWRBenchmarkResult, ...]:
    contract = load_wwr_benchmark_contract(path)
    return tuple(evaluate_wwr_benchmark(case) for case in contract["benchmarks"])

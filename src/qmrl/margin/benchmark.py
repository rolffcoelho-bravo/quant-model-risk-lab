"""Locked deterministic margin and MVA benchmark suite."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from qmrl.multicurrency import CurrencyCurveSet, TermCurve

from .challenger import challenge_mva
from .domain import (
    InitialMarginProfile,
    MarginPolicy,
    ParametricMarginInput,
    PathwiseMarginInput,
)
from .initial_margin import (
    calculate_historical_initial_margin,
    calculate_parametric_initial_margin,
)
from .mva import calculate_mva


@dataclass(frozen=True)
class MarginBenchmarkResult:
    case_id: str
    status: str
    observed: float
    expected: float
    absolute_difference: float


def load_margin_benchmark_contract(path: str | Path) -> dict[str, Any]:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8-sig"))


def _curves(case: dict[str, Any]) -> CurrencyCurveSet:
    times = tuple(float(value) for value in case["times"])
    currency = case.get("currency", "USD")
    return CurrencyCurveSet(
        (
            TermCurve("DISC", currency, "discount", times, tuple(case["discount"])),
            TermCurve("FUND", currency, "funding", times, tuple(case["funding"])),
            TermCurve("COLL", currency, "collateral_remuneration", times, tuple(case["remuneration"])),
        )
    )


def _observe(case: dict[str, Any]) -> float:
    kind = case["kind"]
    if kind == "historical_posted_sum":
        policy = MarginPolicy(method="historical_simulation", **case["policy"])
        profile = calculate_historical_initial_margin(
            PathwiseMarginInput(
                case["netting_set_id"],
                case.get("currency", "USD"),
                tuple(case["times"]),
                tuple(tuple(row) for row in case["values"]),
            ),
            policy,
        )
        return sum(profile.posted_margin)
    if kind == "parametric_posted_sum":
        policy = MarginPolicy(method="parametric", **case["policy"])
        profile = calculate_parametric_initial_margin(
            ParametricMarginInput(
                case["netting_set_id"],
                case.get("currency", "USD"),
                tuple(case["times"]),
                tuple(tuple(row) for row in case["sensitivities"]),
                tuple(tuple(row) for row in case["covariance"]),
                posted_multiplier=case.get("posted_multiplier", 1.0),
                received_multiplier=case.get("received_multiplier", 1.0),
                volatility_scale=case.get("volatility_scale", 1.0),
            ),
            policy,
        )
        return sum(profile.posted_margin)
    if kind in {"mva_net", "challenger_difference"}:
        policy = MarginPolicy(method="historical_simulation", **case["policy"])
        profile = InitialMarginProfile(
            netting_set_id=case["netting_set_id"],
            currency=case.get("currency", "USD"),
            times=tuple(case["times"]),
            posted_margin=tuple(case["posted_margin"]),
            received_margin=tuple(case["received_margin"]),
            method="historical_simulation",
            policy_hash="benchmark-policy",
            received_margin_reusable=policy.received_margin_reusable,
        )
        curves = _curves(case)
        primary = calculate_mva(profile, curves, policy)
        if kind == "mva_net":
            return primary.net_mva
        report = challenge_mva(primary.net_mva, profile, curves, policy)
        return report.absolute_difference
    if kind == "fva_separation_flag":
        policy = MarginPolicy(method="historical_simulation", **case["policy"])
        profile = InitialMarginProfile(
            netting_set_id=case["netting_set_id"],
            currency=case.get("currency", "USD"),
            times=tuple(case["times"]),
            posted_margin=tuple(case["posted_margin"]),
            received_margin=tuple(case["received_margin"]),
            method="historical_simulation",
            policy_hash="benchmark-policy",
            received_margin_reusable=policy.received_margin_reusable,
        )
        return float(calculate_mva(profile, _curves(case), policy).fva_embedded)
    raise ValueError(f"Unsupported benchmark kind: {kind}.")


def run_margin_benchmark_suite(path: str | Path) -> tuple[MarginBenchmarkResult, ...]:
    contract = load_margin_benchmark_contract(path)
    tolerance = float(contract["tolerance"])
    results: list[MarginBenchmarkResult] = []
    for case in contract["cases"]:
        observed = float(_observe(case))
        expected = float(case["expected"])
        difference = abs(observed - expected)
        results.append(
            MarginBenchmarkResult(
                case_id=case["case_id"],
                status="PASS" if difference <= tolerance else "FAIL",
                observed=observed,
                expected=expected,
                absolute_difference=difference,
            )
        )
    return tuple(results)

"""Governed XVA stress scenarios and component attribution for Gate 6."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import hashlib
import json
import math
from typing import Mapping

import numpy as np

from .credit_curve import CreditCurve
from .xva_integration import (
    DiscountCurve,
    FundingCurve,
    XVAExposureInput,
    XVAIntegrationPolicy,
    XVAResult,
    integrate_xva,
)
from .xva_sensitivity import shift_discount_curve, shift_funding_curve


_CHANNELS = {
    "systemic",
    "sector",
    "sovereign",
    "commodity",
    "fx",
    "rates",
    "idiosyncratic",
}
_SEVERITIES = {"mild", "moderate", "severe"}


def _finite(value: float, name: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{name} must be finite.")
    return number


@dataclass(frozen=True)
class XVAStressScenario:
    """Governed joint exposure, credit, funding, and discount stress."""

    scenario_id: str
    channel: str
    severity: str
    as_of_date: date
    calibration_source: str
    rationale: str
    exposure_multiplier: float = 1.0
    negative_exposure_multiplier: float = 1.0
    counterparty_hazard_multiplier: float = 1.0
    own_hazard_multiplier: float = 1.0
    borrowing_spread_bump_bps: float = 0.0
    lending_spread_bump_bps: float = 0.0
    discount_rate_bump_bps: float = 0.0
    correlation_shift: float = 0.0
    plausibility_score: float = 1.0
    human_review_required: bool = True
    approved: bool = False

    def __post_init__(self) -> None:
        for name in ("scenario_id", "calibration_source", "rationale"):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} must not be empty.")
        if self.channel not in _CHANNELS:
            raise ValueError("Unsupported stress channel.")
        if self.severity not in _SEVERITIES:
            raise ValueError("Unsupported stress severity.")

        for name in (
            "exposure_multiplier",
            "negative_exposure_multiplier",
            "counterparty_hazard_multiplier",
            "own_hazard_multiplier",
        ):
            value = _finite(getattr(self, name), name)
            if value < 0.0:
                raise ValueError(f"{name} must be non-negative.")

        for name in (
            "borrowing_spread_bump_bps",
            "lending_spread_bump_bps",
            "discount_rate_bump_bps",
            "correlation_shift",
            "plausibility_score",
        ):
            _finite(getattr(self, name), name)

        if not -0.50 <= self.correlation_shift <= 0.50:
            raise ValueError("correlation_shift must be within [-0.50, 0.50].")
        if not 0.0 <= self.plausibility_score <= 1.0:
            raise ValueError("plausibility_score must be within [0, 1].")
        if self.severity == "severe" and (not self.human_review_required or not self.approved):
            raise ValueError("Severe stress scenarios require approved human review.")
        if self.plausibility_score < 0.50 and not self.approved:
            raise ValueError("Low-plausibility scenarios require explicit approval.")


@dataclass(frozen=True)
class XVAStressResult:
    """Base and stressed XVA with fully reconciled component deltas."""

    scenario_id: str
    channel: str
    severity: str
    base: XVAResult
    stressed: XVAResult
    cva_delta: float
    dva_delta: float
    fca_delta: float
    fba_delta: float
    fva_delta: float
    total_adjustment_delta: float
    cva_delta_by_netting_set: np.ndarray
    dva_delta_by_netting_set: np.ndarray
    fca_delta_by_netting_set: np.ndarray
    fba_delta_by_netting_set: np.ndarray

    def __post_init__(self) -> None:
        count = len(self.base.netting_set_ids)
        if self.base.netting_set_ids != self.stressed.netting_set_ids:
            raise ValueError("Base and stressed netting-set identifiers must match.")
        for name in (
            "cva_delta_by_netting_set",
            "dva_delta_by_netting_set",
            "fca_delta_by_netting_set",
            "fba_delta_by_netting_set",
        ):
            values = np.asarray(getattr(self, name), dtype=float)
            if values.ndim != 1 or values.size != count or not np.isfinite(values).all():
                raise ValueError(f"{name} is invalid.")
            immutable = values.copy()
            immutable.setflags(write=False)
            object.__setattr__(self, name, immutable)


def scale_credit_curve(curve: CreditCurve, multiplier: float) -> CreditCurve:
    """Apply a non-negative hazard multiplier while preserving curve governance."""

    factor = _finite(multiplier, "multiplier")
    if factor < 0.0:
        raise ValueError("multiplier must be non-negative.")
    return CreditCurve(
        curve_id=curve.curve_id + "-STRESS",
        obligor_id=curve.obligor_id,
        role=curve.role,
        probability_measure=curve.probability_measure,
        currency=curve.currency,
        as_of_date=curve.as_of_date,
        recovery_rate=curve.recovery_rate,
        node_times=curve.node_times,
        hazard_rates=curve.hazard_rates * factor,
        source_quote_spreads_bps=curve.source_quote_spreads_bps * factor,
        source_quote_types=curve.source_quote_types,
        extrapolation_mode=curve.extrapolation_mode,
    )


def scale_exposure_input(
    exposure: XVAExposureInput,
    *,
    positive_multiplier: float,
    negative_multiplier: float,
) -> XVAExposureInput:
    positive = _finite(positive_multiplier, "positive_multiplier")
    negative = _finite(negative_multiplier, "negative_multiplier")
    if positive < 0.0 or negative < 0.0:
        raise ValueError("Exposure multipliers must be non-negative.")
    return XVAExposureInput(
        times=exposure.times,
        netting_set_ids=exposure.netting_set_ids,
        counterparty_ids=exposure.counterparty_ids,
        expected_positive=exposure.expected_positive * positive,
        expected_negative=exposure.expected_negative * negative,
        mpor_expected_positive=exposure.mpor_expected_positive * positive,
        mpor_expected_negative=exposure.mpor_expected_negative * negative,
    )


def evaluate_xva_stress(
    exposure: XVAExposureInput,
    *,
    counterparty_curves: Mapping[str, CreditCurve],
    own_curve: CreditCurve,
    discount_curve: DiscountCurve,
    funding_curve: FundingCurve,
    scenario: XVAStressScenario,
    policy: XVAIntegrationPolicy | None = None,
) -> XVAStressResult:
    """Recalculate and attribute CVA, DVA, FCA, and FBA under one scenario."""

    governed_policy = policy or XVAIntegrationPolicy()
    base = integrate_xva(
        exposure,
        counterparty_curves=counterparty_curves,
        own_curve=own_curve,
        discount_curve=discount_curve,
        funding_curve=funding_curve,
        policy=governed_policy,
    )

    stressed_exposure = scale_exposure_input(
        exposure,
        positive_multiplier=scenario.exposure_multiplier,
        negative_multiplier=scenario.negative_exposure_multiplier,
    )
    stressed_counterparties = {
        key: scale_credit_curve(value, scenario.counterparty_hazard_multiplier)
        for key, value in counterparty_curves.items()
    }
    stressed_own = scale_credit_curve(own_curve, scenario.own_hazard_multiplier)
    stressed_discount = shift_discount_curve(
        discount_curve,
        rate_bump_bps=scenario.discount_rate_bump_bps,
    )
    stressed_funding = shift_funding_curve(
        funding_curve,
        borrowing_bump_bps=scenario.borrowing_spread_bump_bps,
        lending_bump_bps=scenario.lending_spread_bump_bps,
    )

    stressed = integrate_xva(
        stressed_exposure,
        counterparty_curves=stressed_counterparties,
        own_curve=stressed_own,
        discount_curve=stressed_discount,
        funding_curve=stressed_funding,
        policy=governed_policy,
    )

    cva_by_set = stressed.cva_by_netting_set - base.cva_by_netting_set
    dva_by_set = stressed.dva_by_netting_set - base.dva_by_netting_set
    fca_by_set = stressed.fca_by_netting_set - base.fca_by_netting_set
    fba_by_set = stressed.fba_by_netting_set - base.fba_by_netting_set

    result = XVAStressResult(
        scenario_id=scenario.scenario_id,
        channel=scenario.channel,
        severity=scenario.severity,
        base=base,
        stressed=stressed,
        cva_delta=stressed.cva - base.cva,
        dva_delta=stressed.dva - base.dva,
        fca_delta=stressed.fca - base.fca,
        fba_delta=stressed.fba - base.fba,
        fva_delta=stressed.fva - base.fva,
        total_adjustment_delta=stressed.total_adjustment - base.total_adjustment,
        cva_delta_by_netting_set=cva_by_set,
        dva_delta_by_netting_set=dva_by_set,
        fca_delta_by_netting_set=fca_by_set,
        fba_delta_by_netting_set=fba_by_set,
    )

    reconciled = -result.cva_delta + result.dva_delta - result.fca_delta + result.fba_delta
    if not math.isclose(reconciled, result.total_adjustment_delta, rel_tol=1e-11, abs_tol=1e-11):
        raise RuntimeError("Stressed total-adjustment delta does not reconcile.")
    if not math.isclose(float(np.sum(cva_by_set)), result.cva_delta, rel_tol=1e-11, abs_tol=1e-11):
        raise RuntimeError("Stressed CVA attribution does not reconcile.")

    return result


def stress_manifest(
    result: XVAStressResult,
    scenario: XVAStressScenario,
) -> dict[str, object]:
    """Create deterministic content-addressed stress evidence."""

    digest = hashlib.sha256()
    for values in (
        result.base.cva_by_bucket,
        result.base.dva_by_bucket,
        result.stressed.cva_by_bucket,
        result.stressed.dva_by_bucket,
        result.cva_delta_by_netting_set,
        result.dva_delta_by_netting_set,
        result.fca_delta_by_netting_set,
        result.fba_delta_by_netting_set,
    ):
        digest.update(np.ascontiguousarray(values, dtype=np.float64).tobytes())
    metadata = {
        "scenario_id": scenario.scenario_id,
        "channel": scenario.channel,
        "severity": scenario.severity,
        "exposure_multiplier": scenario.exposure_multiplier,
        "counterparty_hazard_multiplier": scenario.counterparty_hazard_multiplier,
        "own_hazard_multiplier": scenario.own_hazard_multiplier,
        "borrowing_spread_bump_bps": scenario.borrowing_spread_bump_bps,
        "discount_rate_bump_bps": scenario.discount_rate_bump_bps,
        "approved": scenario.approved,
    }
    digest.update(json.dumps(metadata, sort_keys=True).encode("utf-8"))
    return {
        "schema_version": "1.0",
        "gate": "XVA_EXPOSURE_GATE_6",
        "scenario_id": scenario.scenario_id,
        "channel": scenario.channel,
        "severity": scenario.severity,
        "cva_delta": result.cva_delta,
        "dva_delta": result.dva_delta,
        "fca_delta": result.fca_delta,
        "fba_delta": result.fba_delta,
        "total_adjustment_delta": result.total_adjustment_delta,
        "sha256": digest.hexdigest(),
        "production_approval": False,
    }

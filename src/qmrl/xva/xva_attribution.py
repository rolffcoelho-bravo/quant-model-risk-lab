"""Trade allocation and independent reconciliation for XVA Gate 5."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping, Sequence

import numpy as np

from .credit_curve import CreditCurve
from .xva_integration import (
    DiscountCurve,
    FundingCurve,
    XVAExposureInput,
    XVAIntegrationPolicy,
    XVAResult,
)


def _immutable(values: Sequence[float] | np.ndarray, name: str) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    if array.ndim != 1 or not np.isfinite(array).all():
        raise ValueError(f"{name} must be a finite one-dimensional array.")
    if np.any(array < -1e-12):
        raise ValueError(f"{name} must be non-negative.")
    result = np.maximum(array, 0.0)
    result.setflags(write=False)
    return result


@dataclass(frozen=True)
class TradeAllocationWeights:
    """Transparent component-specific allocation weights by trade."""

    trade_ids: tuple[str, ...]
    netting_set_ids: tuple[str, ...]
    cva_weights: np.ndarray
    dva_weights: np.ndarray
    fca_weights: np.ndarray
    fba_weights: np.ndarray

    def __post_init__(self) -> None:
        if not self.trade_ids or len(set(self.trade_ids)) != len(self.trade_ids):
            raise ValueError("trade_ids must be non-empty and unique.")
        if len(self.netting_set_ids) != len(self.trade_ids):
            raise ValueError("netting_set_ids length mismatch.")
        if any(not value.strip() for value in self.netting_set_ids):
            raise ValueError("netting_set_ids must not be empty.")

        for name in (
            "cva_weights",
            "dva_weights",
            "fca_weights",
            "fba_weights",
        ):
            values = _immutable(getattr(self, name), name)
            if values.size != len(self.trade_ids):
                raise ValueError(f"{name} length mismatch.")
            object.__setattr__(self, name, values)

        for set_id in set(self.netting_set_ids):
            indices = [
                index
                for index, value in enumerate(self.netting_set_ids)
                if value == set_id
            ]
            for name in (
                "cva_weights",
                "dva_weights",
                "fca_weights",
                "fba_weights",
            ):
                total = float(np.sum(getattr(self, name)[indices]))
                if not math.isclose(total, 1.0, abs_tol=1e-12):
                    raise ValueError(
                        f"{name} must sum to one within netting set {set_id}."
                    )


@dataclass(frozen=True)
class TradeXVAAllocation:
    """Trade-level component allocation with full reconciliation."""

    trade_ids: tuple[str, ...]
    netting_set_ids: tuple[str, ...]
    cva: np.ndarray
    dva: np.ndarray
    fca: np.ndarray
    fba: np.ndarray
    total_adjustment: np.ndarray

    def __post_init__(self) -> None:
        expected = len(self.trade_ids)
        for name in ("cva", "dva", "fca", "fba"):
            values = _immutable(getattr(self, name), name)
            if values.size != expected:
                raise ValueError(f"{name} length mismatch.")
            object.__setattr__(self, name, values)
        total = np.asarray(self.total_adjustment, dtype=float)
        if total.ndim != 1 or total.size != expected or not np.isfinite(total).all():
            raise ValueError("total_adjustment length mismatch.")
        expected_total = -self.cva + self.dva - self.fca + self.fba
        if not np.allclose(total, expected_total, atol=1e-12):
            raise ValueError("Trade allocation sign identity failed.")
        total = total.copy()
        total.setflags(write=False)
        object.__setattr__(self, "total_adjustment", total)


@dataclass(frozen=True)
class XVAReconciliation:
    """Independent Gate 5 calculation and attribution reconciliation."""

    challenger_cva_error: float
    challenger_dva_error: float
    challenger_fca_error: float
    challenger_fba_error: float
    bucket_to_set_error: float
    set_to_counterparty_error: float
    component_identity_error: float
    tolerance: float
    status: str


def equal_trade_weights(
    trade_to_netting_set: Mapping[str, str],
) -> TradeAllocationWeights:
    """Build auditable equal weights within each legal netting set."""

    if not trade_to_netting_set:
        raise ValueError("At least one trade is required.")
    trade_ids = tuple(trade_to_netting_set)
    set_ids = tuple(trade_to_netting_set[trade_id] for trade_id in trade_ids)
    counts = {value: set_ids.count(value) for value in set(set_ids)}
    weights = np.asarray([1.0 / counts[value] for value in set_ids], dtype=float)
    return TradeAllocationWeights(
        trade_ids=trade_ids,
        netting_set_ids=set_ids,
        cva_weights=weights,
        dva_weights=weights,
        fca_weights=weights,
        fba_weights=weights,
    )


def allocate_xva_to_trades(
    result: XVAResult,
    weights: TradeAllocationWeights,
) -> TradeXVAAllocation:
    """Allocate netting-set components without changing portfolio totals."""

    known_sets = set(result.netting_set_ids)
    supplied_sets = set(weights.netting_set_ids)
    if supplied_sets != known_sets:
        raise ValueError(
            "Trade allocation must cover every and only result netting set."
        )
    set_index = {value: index for index, value in enumerate(result.netting_set_ids)}

    def allocate(component: np.ndarray, component_weights: np.ndarray) -> np.ndarray:
        values = np.zeros(len(weights.trade_ids), dtype=float)
        for index, set_id in enumerate(weights.netting_set_ids):
            values[index] = component[set_index[set_id]] * component_weights[index]
        return values

    cva = allocate(result.cva_by_netting_set, weights.cva_weights)
    dva = allocate(result.dva_by_netting_set, weights.dva_weights)
    fca = allocate(result.fca_by_netting_set, weights.fca_weights)
    fba = allocate(result.fba_by_netting_set, weights.fba_weights)
    return TradeXVAAllocation(
        trade_ids=weights.trade_ids,
        netting_set_ids=weights.netting_set_ids,
        cva=cva,
        dva=dva,
        fca=fca,
        fba=fba,
        total_adjustment=-cva + dva - fca + fba,
    )


def challenger_xva_components(
    exposure: XVAExposureInput,
    *,
    counterparty_curves: Mapping[str, CreditCurve],
    own_curve: CreditCurve,
    discount_curve: DiscountCurve,
    funding_curve: FundingCurve,
    policy: XVAIntegrationPolicy,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Loop-based challenger independent from vectorized Gate 5 integration."""

    num_intervals = exposure.times.size - 1
    num_sets = len(exposure.netting_set_ids)
    cva = np.zeros((num_intervals, num_sets), dtype=float)
    dva = np.zeros_like(cva)
    fca = np.zeros_like(cva)
    fba = np.zeros_like(cva)

    positive_funding = (
        exposure.mpor_expected_positive
        if policy.fva_basis == "mpor"
        else exposure.expected_positive
    )
    negative_funding = (
        exposure.mpor_expected_negative
        if policy.fva_basis == "mpor"
        else exposure.expected_negative
    )

    def interval_value(profile: np.ndarray, i: int, j: int) -> float:
        if policy.exposure_rule == "interval_end":
            return float(profile[i + 1, j])
        return float(0.5 * (profile[i, j] + profile[i + 1, j]))

    for i in range(num_intervals):
        t0 = float(exposure.times[i])
        t1 = float(exposure.times[i + 1])
        delta = t1 - t0
        discount = discount_curve.discount_factor(t1)
        borrow_bps, lend_bps = funding_curve.spreads_bps(t1)
        own_s0 = own_curve.survival_probability(t0)
        own_s1 = own_curve.survival_probability(t1)
        own_dpd = max(own_s0 - own_s1, 0.0)

        for j, cp_id in enumerate(exposure.counterparty_ids):
            curve = counterparty_curves[cp_id]
            cp_s0 = curve.survival_probability(t0)
            cp_s1 = curve.survival_probability(t1)
            cp_dpd = max(cp_s0 - cp_s1, 0.0)

            cva_survival = own_s1 if policy.valuation_mode == "bilateral" else 1.0
            cva[i, j] = (
                discount
                * interval_value(exposure.expected_positive, i, j)
                * curve.loss_given_default
                * cp_dpd
                * cva_survival
            )

            if policy.valuation_mode == "bilateral":
                dva[i, j] = (
                    discount
                    * interval_value(exposure.expected_negative, i, j)
                    * own_curve.loss_given_default
                    * own_dpd
                    * cp_s1
                )

            survival = 1.0
            if policy.funding_survival_mode == "first_to_default":
                survival = cp_s1
                if policy.valuation_mode == "bilateral":
                    survival *= own_s1

            fca[i, j] = (
                discount
                * interval_value(positive_funding, i, j)
                * borrow_bps
                / 10000.0
                * delta
                * survival
            )
            fba[i, j] = (
                discount
                * interval_value(negative_funding, i, j)
                * lend_bps
                / 10000.0
                * delta
                * survival
            )

    return cva, dva, fca, fba


def reconcile_xva(
    exposure: XVAExposureInput,
    result: XVAResult,
    *,
    counterparty_curves: Mapping[str, CreditCurve],
    own_curve: CreditCurve,
    discount_curve: DiscountCurve,
    funding_curve: FundingCurve,
    policy: XVAIntegrationPolicy,
    tolerance: float = 1e-10,
) -> XVAReconciliation:
    """Reconcile vectorized results, legal-set sums, and component signs."""

    challenger = challenger_xva_components(
        exposure,
        counterparty_curves=counterparty_curves,
        own_curve=own_curve,
        discount_curve=discount_curve,
        funding_curve=funding_curve,
        policy=policy,
    )
    produced = (
        result.cva_by_bucket,
        result.dva_by_bucket,
        result.fca_by_bucket,
        result.fba_by_bucket,
    )
    errors = [
        float(np.max(np.abs(left - right)))
        for left, right in zip(produced, challenger, strict=True)
    ]

    set_error = max(
        float(np.max(np.abs(np.sum(bucket, axis=0) - totals)))
        for bucket, totals in zip(
            produced,
            (
                result.cva_by_netting_set,
                result.dva_by_netting_set,
                result.fca_by_netting_set,
                result.fba_by_netting_set,
            ),
            strict=True,
        )
    )

    counterparty_error = 0.0
    for cp_index, cp_id in enumerate(result.unique_counterparty_ids):
        indices = [
            index
            for index, value in enumerate(result.counterparty_ids)
            if value == cp_id
        ]
        for set_totals, cp_totals in zip(
            (
                result.cva_by_netting_set,
                result.dva_by_netting_set,
                result.fca_by_netting_set,
                result.fba_by_netting_set,
            ),
            (
                result.cva_by_counterparty,
                result.dva_by_counterparty,
                result.fca_by_counterparty,
                result.fba_by_counterparty,
            ),
            strict=True,
        ):
            counterparty_error = max(
                counterparty_error,
                abs(float(np.sum(set_totals[indices])) - float(cp_totals[cp_index])),
            )

    identity_error = abs(
        result.total_adjustment
        - (-result.cva + result.dva - result.fca + result.fba)
    )
    maximum = max(*errors, set_error, counterparty_error, identity_error)
    return XVAReconciliation(
        challenger_cva_error=errors[0],
        challenger_dva_error=errors[1],
        challenger_fca_error=errors[2],
        challenger_fba_error=errors[3],
        bucket_to_set_error=set_error,
        set_to_counterparty_error=counterparty_error,
        component_identity_error=identity_error,
        tolerance=float(tolerance),
        status="PASS" if maximum <= tolerance else "FAIL",
    )

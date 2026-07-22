"""CVA, DVA, and FVA integration for XVA Gate 5.

The module combines collateralized exposure profiles from Gate 3 with
risk-neutral counterparty and own-credit curves from Gate 4. Results are
positive component magnitudes. The clean-value adjustment is represented
as ``-CVA + DVA - FCA + FBA``.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import hashlib
import json
import math
from typing import Mapping, Sequence

import numpy as np

from .credit_curve import CreditCurve
from .pathwise_exposure import PathwiseExposureCube


_EXPOSURE_RULES = {"interval_end", "trapezoidal"}
_VALUATION_MODES = {"unilateral", "bilateral"}
_FUNDING_SURVIVAL_MODES = {"none", "first_to_default"}
_FVA_BASES = {"collateralized", "mpor"}
_CLOSEOUT_CONVENTIONS = {"risk_free"}


def _finite(value: float, name: str) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite.")
    return result


def _array(
    values: Sequence[float] | np.ndarray,
    *,
    name: str,
    ndim: int,
    non_negative: bool = False,
) -> np.ndarray:
    result = np.asarray(values, dtype=float)
    if result.ndim != ndim:
        raise ValueError(f"{name} must have {ndim} dimensions.")
    if not np.isfinite(result).all():
        raise ValueError(f"{name} must contain finite values.")
    if non_negative and np.any(result < -1e-12):
        raise ValueError(f"{name} must be non-negative.")
    result = np.maximum(result, 0.0) if non_negative else result.copy()
    result.setflags(write=False)
    return result


@dataclass(frozen=True)
class XVAExposureInput:
    """Expected exposure profiles by legal netting set."""

    times: np.ndarray
    netting_set_ids: tuple[str, ...]
    counterparty_ids: tuple[str, ...]
    expected_positive: np.ndarray
    expected_negative: np.ndarray
    mpor_expected_positive: np.ndarray
    mpor_expected_negative: np.ndarray

    def __post_init__(self) -> None:
        times = _array(self.times, name="times", ndim=1)
        if times.size < 2:
            raise ValueError("At least two exposure times are required.")
        if not np.isclose(times[0], 0.0):
            raise ValueError("times must start at zero.")
        if np.any(np.diff(times) <= 0.0):
            raise ValueError("times must be strictly increasing.")

        num_sets = len(self.netting_set_ids)
        if num_sets == 0:
            raise ValueError("At least one netting set is required.")
        if len(set(self.netting_set_ids)) != num_sets:
            raise ValueError("netting_set_ids must be unique.")
        if len(self.counterparty_ids) != num_sets:
            raise ValueError("counterparty_ids length mismatch.")
        if any(not value.strip() for value in self.netting_set_ids):
            raise ValueError("netting_set_ids must not be empty.")
        if any(not value.strip() for value in self.counterparty_ids):
            raise ValueError("counterparty_ids must not be empty.")

        expected_shape = (times.size, num_sets)
        for name in (
            "expected_positive",
            "expected_negative",
            "mpor_expected_positive",
            "mpor_expected_negative",
        ):
            values = _array(
                getattr(self, name),
                name=name,
                ndim=2,
                non_negative=True,
            )
            if values.shape != expected_shape:
                raise ValueError(f"{name} shape mismatch.")
            object.__setattr__(self, name, values)

        object.__setattr__(self, "times", times)

    @classmethod
    def from_pathwise_exposure(
        cls,
        cube: PathwiseExposureCube,
    ) -> "XVAExposureInput":
        return cls(
            times=cube.times,
            netting_set_ids=cube.netting_set_ids,
            counterparty_ids=cube.counterparty_ids,
            expected_positive=np.mean(cube.positive_exposure, axis=0),
            expected_negative=np.mean(cube.negative_exposure, axis=0),
            mpor_expected_positive=np.mean(
                cube.mpor_positive_exposure,
                axis=0,
            ),
            mpor_expected_negative=np.mean(
                cube.mpor_negative_exposure,
                axis=0,
            ),
        )


@dataclass(frozen=True)
class DiscountCurve:
    """Governed discount-factor curve with log-linear interpolation."""

    curve_id: str
    currency: str
    as_of_date: date
    times: np.ndarray
    discount_factors: np.ndarray
    extrapolation_mode: str = "flat_zero_rate"

    def __post_init__(self) -> None:
        if not self.curve_id.strip():
            raise ValueError("curve_id must not be empty.")
        if len(self.currency.strip()) != 3:
            raise ValueError("currency must be a three-letter code.")
        if self.extrapolation_mode not in {"flat_zero_rate", "forbidden"}:
            raise ValueError("Unsupported discount extrapolation mode.")

        times = _array(self.times, name="times", ndim=1)
        factors = _array(
            self.discount_factors,
            name="discount_factors",
            ndim=1,
        )
        if times.size != factors.size or times.size < 2:
            raise ValueError("Discount-curve arrays must have equal length >= 2.")
        if not np.isclose(times[0], 0.0) or np.any(np.diff(times) <= 0.0):
            raise ValueError("Discount times must start at zero and increase.")
        if not np.isclose(factors[0], 1.0):
            raise ValueError("The time-zero discount factor must equal one.")
        if np.any(factors <= 0.0):
            raise ValueError("discount_factors must be positive.")
        if np.any(np.diff(factors) > 1e-12):
            raise ValueError("discount_factors must be non-increasing.")

        object.__setattr__(self, "currency", self.currency.upper())
        object.__setattr__(self, "times", times)
        object.__setattr__(self, "discount_factors", factors)

    def discount_factor(self, time_years: float) -> float:
        value = _finite(time_years, "time_years")
        if value < 0.0:
            raise ValueError("time_years must be non-negative.")
        if value == 0.0:
            return 1.0
        last_time = float(self.times[-1])
        if value > last_time and self.extrapolation_mode == "forbidden":
            raise ValueError("Discount-curve extrapolation is forbidden.")
        if value >= last_time:
            zero_rate = -math.log(float(self.discount_factors[-1])) / last_time
            return float(math.exp(-zero_rate * value))

        index = int(np.searchsorted(self.times, value, side="right"))
        left = index - 1
        right = index
        t0 = float(self.times[left])
        t1 = float(self.times[right])
        weight = (value - t0) / (t1 - t0)
        log_df = (
            (1.0 - weight) * math.log(float(self.discount_factors[left]))
            + weight * math.log(float(self.discount_factors[right]))
        )
        return float(math.exp(log_df))

    def values(self, times: Sequence[float] | np.ndarray) -> np.ndarray:
        requested = np.asarray(times, dtype=float)
        if requested.ndim != 1 or not np.isfinite(requested).all():
            raise ValueError("times must be a finite one-dimensional array.")
        return np.asarray(
            [self.discount_factor(float(value)) for value in requested],
            dtype=float,
        )


@dataclass(frozen=True)
class FundingCurve:
    """Borrowing-cost and lending-benefit term structures."""

    curve_id: str
    currency: str
    as_of_date: date
    times: np.ndarray
    borrowing_spreads_bps: np.ndarray
    lending_spreads_bps: np.ndarray
    extrapolation_mode: str = "flat"

    def __post_init__(self) -> None:
        if not self.curve_id.strip():
            raise ValueError("curve_id must not be empty.")
        if len(self.currency.strip()) != 3:
            raise ValueError("currency must be a three-letter code.")
        if self.extrapolation_mode not in {"flat", "forbidden"}:
            raise ValueError("Unsupported funding extrapolation mode.")

        times = _array(self.times, name="times", ndim=1)
        borrowing = _array(
            self.borrowing_spreads_bps,
            name="borrowing_spreads_bps",
            ndim=1,
            non_negative=True,
        )
        lending = _array(
            self.lending_spreads_bps,
            name="lending_spreads_bps",
            ndim=1,
            non_negative=True,
        )
        if times.size != borrowing.size or times.size != lending.size:
            raise ValueError("Funding-curve arrays must have equal length.")
        if times.size < 2 or not np.isclose(times[0], 0.0):
            raise ValueError("Funding times must start at zero.")
        if np.any(np.diff(times) <= 0.0):
            raise ValueError("Funding times must be strictly increasing.")
        if np.any(lending > borrowing + 1e-12):
            raise ValueError("Lending benefit cannot exceed borrowing cost.")

        object.__setattr__(self, "currency", self.currency.upper())
        object.__setattr__(self, "times", times)
        object.__setattr__(self, "borrowing_spreads_bps", borrowing)
        object.__setattr__(self, "lending_spreads_bps", lending)

    def spreads_bps(self, time_years: float) -> tuple[float, float]:
        value = _finite(time_years, "time_years")
        if value < 0.0:
            raise ValueError("time_years must be non-negative.")
        last_time = float(self.times[-1])
        if value > last_time and self.extrapolation_mode == "forbidden":
            raise ValueError("Funding-curve extrapolation is forbidden.")
        if value >= last_time:
            return (
                float(self.borrowing_spreads_bps[-1]),
                float(self.lending_spreads_bps[-1]),
            )
        return (
            float(np.interp(value, self.times, self.borrowing_spreads_bps)),
            float(np.interp(value, self.times, self.lending_spreads_bps)),
        )


@dataclass(frozen=True)
class XVAIntegrationPolicy:
    """Controlled conventions for Gate 5 valuation adjustment."""

    valuation_currency: str = "USD"
    valuation_mode: str = "bilateral"
    exposure_rule: str = "interval_end"
    fva_basis: str = "collateralized"
    funding_survival_mode: str = "first_to_default"
    closeout_convention: str = "risk_free"
    probability_measure: str = "risk_neutral"
    require_same_as_of_date: bool = True

    def __post_init__(self) -> None:
        if len(self.valuation_currency.strip()) != 3:
            raise ValueError("valuation_currency must be a three-letter code.")
        if self.valuation_mode not in _VALUATION_MODES:
            raise ValueError("Unsupported valuation_mode.")
        if self.exposure_rule not in _EXPOSURE_RULES:
            raise ValueError("Unsupported exposure_rule.")
        if self.fva_basis not in _FVA_BASES:
            raise ValueError("Unsupported fva_basis.")
        if self.funding_survival_mode not in _FUNDING_SURVIVAL_MODES:
            raise ValueError("Unsupported funding_survival_mode.")
        if self.closeout_convention not in _CLOSEOUT_CONVENTIONS:
            raise ValueError("Only risk_free closeout is supported in Gate 5.")
        if self.probability_measure != "risk_neutral":
            raise ValueError("Gate 5 requires risk-neutral credit curves.")
        object.__setattr__(
            self,
            "valuation_currency",
            self.valuation_currency.upper(),
        )


@dataclass(frozen=True)
class XVAResult:
    """Bucket, netting-set, counterparty, and portfolio XVA attribution."""

    interval_start_times: np.ndarray
    interval_end_times: np.ndarray
    netting_set_ids: tuple[str, ...]
    counterparty_ids: tuple[str, ...]
    unique_counterparty_ids: tuple[str, ...]
    cva_by_bucket: np.ndarray
    dva_by_bucket: np.ndarray
    fca_by_bucket: np.ndarray
    fba_by_bucket: np.ndarray
    cva_by_netting_set: np.ndarray
    dva_by_netting_set: np.ndarray
    fca_by_netting_set: np.ndarray
    fba_by_netting_set: np.ndarray
    cva_by_counterparty: np.ndarray
    dva_by_counterparty: np.ndarray
    fca_by_counterparty: np.ndarray
    fba_by_counterparty: np.ndarray
    cva: float
    dva: float
    fca: float
    fba: float
    fva: float
    total_adjustment: float

    def __post_init__(self) -> None:
        starts = _array(
            self.interval_start_times,
            name="interval_start_times",
            ndim=1,
        )
        ends = _array(
            self.interval_end_times,
            name="interval_end_times",
            ndim=1,
        )
        if starts.shape != ends.shape or starts.size == 0:
            raise ValueError("Interval arrays must have equal non-zero length.")
        if np.any(ends <= starts):
            raise ValueError("Each XVA interval must have positive length.")

        bucket_shape = (starts.size, len(self.netting_set_ids))
        bucket_arrays: dict[str, np.ndarray] = {}
        for name in (
            "cva_by_bucket",
            "dva_by_bucket",
            "fca_by_bucket",
            "fba_by_bucket",
        ):
            values = _array(
                getattr(self, name),
                name=name,
                ndim=2,
                non_negative=True,
            )
            if values.shape != bucket_shape:
                raise ValueError(f"{name} shape mismatch.")
            bucket_arrays[name] = values
            object.__setattr__(self, name, values)

        if len(self.counterparty_ids) != len(self.netting_set_ids):
            raise ValueError("counterparty_ids length mismatch.")

        set_shape = (len(self.netting_set_ids),)
        for name in (
            "cva_by_netting_set",
            "dva_by_netting_set",
            "fca_by_netting_set",
            "fba_by_netting_set",
        ):
            values = _array(
                getattr(self, name),
                name=name,
                ndim=1,
                non_negative=True,
            )
            if values.shape != set_shape:
                raise ValueError(f"{name} shape mismatch.")
            object.__setattr__(self, name, values)

        cp_shape = (len(self.unique_counterparty_ids),)
        for name in (
            "cva_by_counterparty",
            "dva_by_counterparty",
            "fca_by_counterparty",
            "fba_by_counterparty",
        ):
            values = _array(
                getattr(self, name),
                name=name,
                ndim=1,
                non_negative=True,
            )
            if values.shape != cp_shape:
                raise ValueError(f"{name} shape mismatch.")
            object.__setattr__(self, name, values)

        component_values = {
            "cva": _finite(self.cva, "cva"),
            "dva": _finite(self.dva, "dva"),
            "fca": _finite(self.fca, "fca"),
            "fba": _finite(self.fba, "fba"),
        }
        if any(value < -1e-12 for value in component_values.values()):
            raise ValueError("XVA component magnitudes must be non-negative.")

        expected_fva = component_values["fca"] - component_values["fba"]
        expected_total = (
            -component_values["cva"]
            + component_values["dva"]
            - component_values["fca"]
            + component_values["fba"]
        )
        if not math.isclose(self.fva, expected_fva, abs_tol=1e-10):
            raise ValueError("fva must equal fca minus fba.")
        if not math.isclose(
            self.total_adjustment,
            expected_total,
            abs_tol=1e-10,
        ):
            raise ValueError("total_adjustment sign identity failed.")

        object.__setattr__(self, "interval_start_times", starts)
        object.__setattr__(self, "interval_end_times", ends)


def _profile_for_interval(
    profile: np.ndarray,
    rule: str,
) -> np.ndarray:
    if rule == "interval_end":
        return profile[1:, :]
    return 0.5 * (profile[:-1, :] + profile[1:, :])


def _validate_inputs(
    exposure: XVAExposureInput,
    counterparty_curves: Mapping[str, CreditCurve],
    own_curve: CreditCurve,
    discount_curve: DiscountCurve,
    funding_curve: FundingCurve,
    policy: XVAIntegrationPolicy,
) -> None:
    required_counterparties = set(exposure.counterparty_ids)
    supplied = set(counterparty_curves)
    if supplied != required_counterparties:
        raise ValueError(
            "Counterparty curve mapping must match exposure counterparties. "
            f"Missing={sorted(required_counterparties - supplied)}; "
            f"unexpected={sorted(supplied - required_counterparties)}."
        )

    dates = {discount_curve.as_of_date, funding_curve.as_of_date, own_curve.as_of_date}
    currency = policy.valuation_currency
    if discount_curve.currency != currency or funding_curve.currency != currency:
        raise ValueError("Discount and funding currencies must match valuation currency.")
    if own_curve.currency != currency:
        raise ValueError("Own-credit curve currency mismatch.")
    if own_curve.role != "own":
        raise ValueError("own_curve must have role='own'.")
    if own_curve.probability_measure != policy.probability_measure:
        raise ValueError("Own-credit probability measure mismatch.")

    for counterparty_id, curve in counterparty_curves.items():
        if curve.obligor_id != counterparty_id:
            raise ValueError("Counterparty curve obligor_id mismatch.")
        if curve.role not in {"counterparty", "proxy"}:
            raise ValueError("Counterparty curve must have counterparty or proxy role.")
        if curve.probability_measure != policy.probability_measure:
            raise ValueError("Counterparty probability measure mismatch.")
        if curve.currency != currency:
            raise ValueError("Counterparty curve currency mismatch.")
        if curve.obligor_id == own_curve.obligor_id:
            raise ValueError("Own and counterparty obligors must be distinct.")
        dates.add(curve.as_of_date)

    if policy.require_same_as_of_date and len(dates) != 1:
        raise ValueError("All Gate 5 market inputs must share one as-of date.")

    # Force governed extrapolation checks before any calculation.
    terminal = float(exposure.times[-1])
    discount_curve.discount_factor(terminal)
    funding_curve.spreads_bps(terminal)
    own_curve.survival_probability(terminal)
    for curve in counterparty_curves.values():
        curve.survival_probability(terminal)


def integrate_xva(
    exposure: XVAExposureInput,
    *,
    counterparty_curves: Mapping[str, CreditCurve],
    own_curve: CreditCurve,
    discount_curve: DiscountCurve,
    funding_curve: FundingCurve,
    policy: XVAIntegrationPolicy | None = None,
) -> XVAResult:
    """Integrate discounted CVA, DVA, FCA, and FBA by legal netting set."""

    governed_policy = policy or XVAIntegrationPolicy()
    _validate_inputs(
        exposure,
        counterparty_curves,
        own_curve,
        discount_curve,
        funding_curve,
        governed_policy,
    )

    starts = exposure.times[:-1]
    ends = exposure.times[1:]
    dt = ends - starts
    num_intervals = ends.size
    num_sets = len(exposure.netting_set_ids)

    positive_source = (
        exposure.mpor_expected_positive
        if governed_policy.fva_basis == "mpor"
        else exposure.expected_positive
    )
    negative_source = (
        exposure.mpor_expected_negative
        if governed_policy.fva_basis == "mpor"
        else exposure.expected_negative
    )

    cva_exposure = _profile_for_interval(
        exposure.expected_positive,
        governed_policy.exposure_rule,
    )
    dva_exposure = _profile_for_interval(
        exposure.expected_negative,
        governed_policy.exposure_rule,
    )
    fca_exposure = _profile_for_interval(
        positive_source,
        governed_policy.exposure_rule,
    )
    fba_exposure = _profile_for_interval(
        negative_source,
        governed_policy.exposure_rule,
    )

    discount = discount_curve.values(ends)
    borrowing = np.asarray(
        [funding_curve.spreads_bps(float(t))[0] for t in ends],
        dtype=float,
    ) / 10000.0
    lending = np.asarray(
        [funding_curve.spreads_bps(float(t))[1] for t in ends],
        dtype=float,
    ) / 10000.0

    own_survival_start = own_curve.survival_probabilities(starts)
    own_survival_end = own_curve.survival_probabilities(ends)
    own_marginal_pd = np.maximum(
        own_survival_start - own_survival_end,
        0.0,
    )

    cva = np.zeros((num_intervals, num_sets), dtype=float)
    dva = np.zeros_like(cva)
    fca = np.zeros_like(cva)
    fba = np.zeros_like(cva)

    for set_index, counterparty_id in enumerate(exposure.counterparty_ids):
        curve = counterparty_curves[counterparty_id]
        cp_survival_start = curve.survival_probabilities(starts)
        cp_survival_end = curve.survival_probabilities(ends)
        cp_marginal_pd = np.maximum(
            cp_survival_start - cp_survival_end,
            0.0,
        )

        cva_survival = (
            own_survival_end
            if governed_policy.valuation_mode == "bilateral"
            else np.ones_like(ends)
        )
        cva[:, set_index] = (
            discount
            * cva_exposure[:, set_index]
            * curve.loss_given_default
            * cp_marginal_pd
            * cva_survival
        )

        if governed_policy.valuation_mode == "bilateral":
            dva[:, set_index] = (
                discount
                * dva_exposure[:, set_index]
                * own_curve.loss_given_default
                * own_marginal_pd
                * cp_survival_end
            )

        if governed_policy.funding_survival_mode == "first_to_default":
            survival = cp_survival_end.copy()
            if governed_policy.valuation_mode == "bilateral":
                survival *= own_survival_end
        else:
            survival = np.ones_like(ends)

        fca[:, set_index] = (
            discount
            * fca_exposure[:, set_index]
            * borrowing
            * dt
            * survival
        )
        fba[:, set_index] = (
            discount
            * fba_exposure[:, set_index]
            * lending
            * dt
            * survival
        )

    component_buckets = (cva, dva, fca, fba)
    for values in component_buckets:
        if np.any(values < -1e-12) or not np.isfinite(values).all():
            raise RuntimeError("Gate 5 produced invalid component values.")

    set_totals = [np.sum(values, axis=0) for values in component_buckets]
    portfolio_totals = [float(np.sum(values)) for values in component_buckets]

    unique_counterparties = tuple(dict.fromkeys(exposure.counterparty_ids))
    cp_totals = [
        np.zeros(len(unique_counterparties), dtype=float)
        for _ in component_buckets
    ]
    for cp_index, cp_id in enumerate(unique_counterparties):
        indices = [
            index
            for index, value in enumerate(exposure.counterparty_ids)
            if value == cp_id
        ]
        for component_index, totals in enumerate(set_totals):
            cp_totals[component_index][cp_index] = float(np.sum(totals[indices]))

    cva_total, dva_total, fca_total, fba_total = portfolio_totals
    fva_total = fca_total - fba_total
    total_adjustment = -cva_total + dva_total - fca_total + fba_total

    return XVAResult(
        interval_start_times=starts,
        interval_end_times=ends,
        netting_set_ids=exposure.netting_set_ids,
        counterparty_ids=exposure.counterparty_ids,
        unique_counterparty_ids=unique_counterparties,
        cva_by_bucket=cva,
        dva_by_bucket=dva,
        fca_by_bucket=fca,
        fba_by_bucket=fba,
        cva_by_netting_set=set_totals[0],
        dva_by_netting_set=set_totals[1],
        fca_by_netting_set=set_totals[2],
        fba_by_netting_set=set_totals[3],
        cva_by_counterparty=cp_totals[0],
        dva_by_counterparty=cp_totals[1],
        fca_by_counterparty=cp_totals[2],
        fba_by_counterparty=cp_totals[3],
        cva=cva_total,
        dva=dva_total,
        fca=fca_total,
        fba=fba_total,
        fva=fva_total,
        total_adjustment=total_adjustment,
    )


def xva_manifest(
    exposure: XVAExposureInput,
    result: XVAResult,
    policy: XVAIntegrationPolicy,
) -> dict[str, object]:
    """Create deterministic, content-addressed Gate 5 calculation evidence."""

    digest = hashlib.sha256()
    for values in (
        exposure.times,
        exposure.expected_positive,
        exposure.expected_negative,
        exposure.mpor_expected_positive,
        result.cva_by_bucket,
        result.dva_by_bucket,
        result.fca_by_bucket,
        result.fba_by_bucket,
    ):
        digest.update(
            np.ascontiguousarray(values, dtype=np.float64).tobytes()
        )

    metadata = {
        "netting_set_ids": exposure.netting_set_ids,
        "counterparty_ids": exposure.counterparty_ids,
        "valuation_mode": policy.valuation_mode,
        "exposure_rule": policy.exposure_rule,
        "fva_basis": policy.fva_basis,
        "funding_survival_mode": policy.funding_survival_mode,
        "closeout_convention": policy.closeout_convention,
    }
    digest.update(json.dumps(metadata, sort_keys=True).encode("utf-8"))

    return {
        "schema_version": "1.0",
        "gate": "XVA_EXPOSURE_GATE_5",
        "num_intervals": int(result.interval_end_times.size),
        "num_netting_sets": len(result.netting_set_ids),
        "num_counterparties": len(result.unique_counterparty_ids),
        "cva": result.cva,
        "dva": result.dva,
        "fca": result.fca,
        "fba": result.fba,
        "fva": result.fva,
        "total_adjustment": result.total_adjustment,
        "calculation_sha256": digest.hexdigest(),
    }

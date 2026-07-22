"""Counterparty credit calibration and PD/LGD term structures for XVA Gate 4."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import hashlib
import json
import math
from typing import Iterable, Sequence

import numpy as np


_ALLOWED_QUOTE_TYPES = {"cds", "bond", "proxy"}
_ALLOWED_MEASURES = {"risk_neutral", "historical"}
_ALLOWED_ROLES = {"counterparty", "own", "proxy"}
_ALLOWED_EXTRAPOLATION = {"flat_hazard", "forbidden"}


def _finite(value: float, name: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{name} must be finite.")
    return number


def _immutable_float_array(
    values: Sequence[float] | np.ndarray,
    *,
    name: str,
) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    if array.ndim != 1:
        raise ValueError(f"{name} must be one-dimensional.")
    if array.size == 0:
        raise ValueError(f"{name} must not be empty.")
    if not np.isfinite(array).all():
        raise ValueError(f"{name} must contain finite values.")
    result = array.copy()
    result.setflags(write=False)
    return result


@dataclass(frozen=True)
class CreditQuote:
    """One governed credit-spread observation."""

    quote_id: str
    obligor_id: str
    tenor_years: float
    spread_bps: float
    as_of_date: date
    source_id: str
    quote_type: str = "cds"
    probability_measure: str = "risk_neutral"
    currency: str = "USD"
    seniority: str = "senior_unsecured"

    def __post_init__(self) -> None:
        for name in (
            "quote_id",
            "obligor_id",
            "source_id",
            "seniority",
        ):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} must not be empty.")

        tenor = _finite(self.tenor_years, "tenor_years")
        spread = _finite(self.spread_bps, "spread_bps")

        if tenor <= 0.0:
            raise ValueError("tenor_years must be positive.")
        if spread < 0.0:
            raise ValueError("spread_bps must be non-negative.")
        if self.quote_type not in _ALLOWED_QUOTE_TYPES:
            raise ValueError("Unsupported quote_type.")
        if self.probability_measure not in _ALLOWED_MEASURES:
            raise ValueError("Unsupported probability_measure.")
        if len(self.currency.strip()) != 3:
            raise ValueError("currency must be a three-letter code.")

        object.__setattr__(self, "tenor_years", tenor)
        object.__setattr__(self, "spread_bps", spread)
        object.__setattr__(self, "currency", self.currency.upper())


@dataclass(frozen=True)
class RecoveryAssumption:
    """Governed recovery-rate and LGD assumption."""

    obligor_id: str
    recovery_rate: float
    as_of_date: date
    source_id: str
    seniority: str = "senior_unsecured"

    def __post_init__(self) -> None:
        for name in ("obligor_id", "source_id", "seniority"):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} must not be empty.")

        recovery = _finite(self.recovery_rate, "recovery_rate")
        if not 0.0 <= recovery < 1.0:
            raise ValueError("recovery_rate must be in [0, 1).")

        object.__setattr__(self, "recovery_rate", recovery)

    @property
    def loss_given_default(self) -> float:
        return 1.0 - self.recovery_rate


@dataclass(frozen=True)
class CreditCurve:
    """Piecewise-constant hazard curve with controlled extrapolation."""

    curve_id: str
    obligor_id: str
    role: str
    probability_measure: str
    currency: str
    as_of_date: date
    recovery_rate: float
    node_times: np.ndarray
    hazard_rates: np.ndarray
    source_quote_spreads_bps: np.ndarray
    source_quote_types: tuple[str, ...]
    extrapolation_mode: str = "flat_hazard"

    def __post_init__(self) -> None:
        for name in ("curve_id", "obligor_id"):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} must not be empty.")

        if self.role not in _ALLOWED_ROLES:
            raise ValueError("Unsupported credit-curve role.")
        if self.probability_measure not in _ALLOWED_MEASURES:
            raise ValueError("Unsupported probability_measure.")
        if len(self.currency.strip()) != 3:
            raise ValueError("currency must be a three-letter code.")
        if self.extrapolation_mode not in _ALLOWED_EXTRAPOLATION:
            raise ValueError("Unsupported extrapolation_mode.")

        recovery = _finite(self.recovery_rate, "recovery_rate")
        if not 0.0 <= recovery < 1.0:
            raise ValueError("recovery_rate must be in [0, 1).")

        times = _immutable_float_array(self.node_times, name="node_times")
        hazards = _immutable_float_array(
            self.hazard_rates,
            name="hazard_rates",
        )
        spreads = _immutable_float_array(
            self.source_quote_spreads_bps,
            name="source_quote_spreads_bps",
        )

        if times.size != hazards.size or times.size != spreads.size:
            raise ValueError("Curve arrays must have equal length.")
        if np.any(times <= 0.0) or np.any(np.diff(times) <= 0.0):
            raise ValueError("node_times must be positive and strictly increasing.")
        if np.any(hazards < 0.0):
            raise ValueError("hazard_rates must be non-negative.")
        if np.any(spreads < 0.0):
            raise ValueError("source spreads must be non-negative.")
        if len(self.source_quote_types) != times.size:
            raise ValueError("source_quote_types length mismatch.")
        if any(value not in _ALLOWED_QUOTE_TYPES for value in self.source_quote_types):
            raise ValueError("Unsupported source quote type.")

        object.__setattr__(self, "currency", self.currency.upper())
        object.__setattr__(self, "recovery_rate", recovery)
        object.__setattr__(self, "node_times", times)
        object.__setattr__(self, "hazard_rates", hazards)
        object.__setattr__(self, "source_quote_spreads_bps", spreads)

    @property
    def loss_given_default(self) -> float:
        return 1.0 - self.recovery_rate

    def cumulative_hazard(self, time_years: float) -> float:
        time_value = _finite(time_years, "time_years")
        if time_value < 0.0:
            raise ValueError("time_years must be non-negative.")
        if time_value == 0.0:
            return 0.0
        if (
            time_value > float(self.node_times[-1])
            and self.extrapolation_mode == "forbidden"
        ):
            raise ValueError("Credit-curve extrapolation is forbidden.")

        total = 0.0
        previous = 0.0

        for node, hazard in zip(
            self.node_times,
            self.hazard_rates,
            strict=True,
        ):
            node_value = float(node)
            interval_end = min(time_value, node_value)
            if interval_end > previous:
                total += float(hazard) * (interval_end - previous)
            if time_value <= node_value:
                return float(total)
            previous = node_value

        total += float(self.hazard_rates[-1]) * (
            time_value - float(self.node_times[-1])
        )
        return float(total)

    def hazard_rate(self, time_years: float) -> float:
        time_value = _finite(time_years, "time_years")
        if time_value < 0.0:
            raise ValueError("time_years must be non-negative.")
        if (
            time_value > float(self.node_times[-1])
            and self.extrapolation_mode == "forbidden"
        ):
            raise ValueError("Credit-curve extrapolation is forbidden.")

        index = int(np.searchsorted(self.node_times, time_value, side="left"))
        index = min(index, self.hazard_rates.size - 1)
        return float(self.hazard_rates[index])

    def survival_probability(self, time_years: float) -> float:
        return float(math.exp(-self.cumulative_hazard(time_years)))

    def cumulative_default_probability(self, time_years: float) -> float:
        return float(1.0 - self.survival_probability(time_years))

    def survival_probabilities(
        self,
        times: Sequence[float] | np.ndarray,
    ) -> np.ndarray:
        values = np.asarray(times, dtype=float)
        if values.ndim != 1 or not np.isfinite(values).all():
            raise ValueError("times must be a finite one-dimensional array.")
        if np.any(values < 0.0):
            raise ValueError("times must be non-negative.")
        return np.asarray(
            [self.survival_probability(float(value)) for value in values],
            dtype=float,
        )

    def marginal_default_probabilities(
        self,
        times: Sequence[float] | np.ndarray | None = None,
    ) -> np.ndarray:
        requested = self.node_times if times is None else np.asarray(times, dtype=float)
        survival = self.survival_probabilities(requested)
        previous = np.concatenate(([1.0], survival[:-1]))
        marginal = previous - survival
        if np.any(marginal < -1e-12):
            raise RuntimeError("Marginal default probabilities must be non-negative.")
        return np.maximum(marginal, 0.0)


@dataclass(frozen=True)
class CreditCurveRepricing:
    """Calibration quote-repricing evidence."""

    tenors: np.ndarray
    market_spreads_bps: np.ndarray
    model_spreads_bps: np.ndarray
    errors_bps: np.ndarray
    max_abs_error_bps: float


@dataclass(frozen=True)
class CreditCurveSensitivity:
    """Controlled terminal-PD sensitivity evidence."""

    terminal_time: float
    base_terminal_pd: float
    parallel_spread_bump_bps: float
    parallel_spread_pd_delta: float
    recovery_bump: float
    recovery_pd_delta: float
    max_quote_repricing_error_bps: float


def validate_credit_quotes(
    quotes: Iterable[CreditQuote],
    *,
    as_of_date: date,
    max_age_days: int,
    required_tenors: Sequence[float] | None = None,
    expected_measure: str | None = None,
    expected_currency: str | None = None,
    allow_bond_spread_proxy: bool = False,
) -> tuple[CreditQuote, ...]:
    """Validate quote identity, age, tenor coverage, and measure consistency."""

    if max_age_days < 0:
        raise ValueError("max_age_days must be non-negative.")

    quote_list = tuple(sorted(quotes, key=lambda item: item.tenor_years))
    if not quote_list:
        raise ValueError("At least one credit quote is required.")

    obligors = {quote.obligor_id for quote in quote_list}
    measures = {quote.probability_measure for quote in quote_list}
    currencies = {quote.currency for quote in quote_list}
    seniorities = {quote.seniority for quote in quote_list}
    tenors = np.asarray([quote.tenor_years for quote in quote_list], dtype=float)

    if len(obligors) != 1:
        raise ValueError("Quotes must refer to one obligor.")
    if len(measures) != 1:
        raise ValueError("Quotes must use one probability measure.")
    if len(currencies) != 1:
        raise ValueError("Quotes must use one currency.")
    if len(seniorities) != 1:
        raise ValueError("Quotes must use one seniority class.")
    if np.any(np.diff(tenors) <= 0.0):
        raise ValueError("Quote tenors must be unique and strictly increasing.")

    quote_ids = [quote.quote_id for quote in quote_list]
    if len(quote_ids) != len(set(quote_ids)):
        raise ValueError("quote_id values must be unique.")

    for quote in quote_list:
        age = (as_of_date - quote.as_of_date).days
        if age < 0:
            raise ValueError("Future-dated credit quotes are not allowed.")
        if age > max_age_days:
            raise ValueError(f"Stale credit quote: {quote.quote_id}")
        if quote.quote_type == "bond" and not allow_bond_spread_proxy:
            raise ValueError(
                "Bond spreads require explicit proxy approval because liquidity "
                "and credit components are not separated in Gate 4."
            )

    if expected_measure is not None and measures != {expected_measure}:
        raise ValueError("Credit quotes do not match the expected probability measure.")
    if expected_currency is not None and currencies != {expected_currency.upper()}:
        raise ValueError("Credit quotes do not match the expected currency.")

    if required_tenors is not None:
        missing = [
            float(required)
            for required in required_tenors
            if not np.any(np.isclose(tenors, float(required), atol=1e-12, rtol=0.0))
        ]
        if missing:
            raise ValueError(f"Missing required credit tenors: {missing}")

    return quote_list


def validate_recovery_assumption(
    recovery: RecoveryAssumption,
    *,
    as_of_date: date,
    max_age_days: int,
    expected_obligor_id: str,
    expected_seniority: str,
) -> None:
    if max_age_days < 0:
        raise ValueError("max_age_days must be non-negative.")
    age = (as_of_date - recovery.as_of_date).days
    if age < 0:
        raise ValueError("Future-dated recovery assumptions are not allowed.")
    if age > max_age_days:
        raise ValueError("Recovery assumption is stale.")
    if recovery.obligor_id != expected_obligor_id:
        raise ValueError("Recovery obligor does not match the quote set.")
    if recovery.seniority != expected_seniority:
        raise ValueError("Recovery seniority does not match the quote set.")


def flat_hazard_from_spread(
    spread_bps: float,
    recovery_rate: float,
) -> float:
    spread = _finite(spread_bps, "spread_bps")
    recovery = _finite(recovery_rate, "recovery_rate")
    if spread < 0.0:
        raise ValueError("spread_bps must be non-negative.")
    if not 0.0 <= recovery < 1.0:
        raise ValueError("recovery_rate must be in [0, 1).")
    return spread / 10_000.0 / (1.0 - recovery)


def build_flat_credit_curve(
    *,
    curve_id: str,
    obligor_id: str,
    role: str,
    probability_measure: str,
    currency: str,
    as_of_date: date,
    recovery_rate: float,
    spread_bps: float,
    node_times: Sequence[float],
    extrapolation_mode: str = "flat_hazard",
) -> CreditCurve:
    times = np.asarray(node_times, dtype=float)
    hazard = flat_hazard_from_spread(spread_bps, recovery_rate)
    return CreditCurve(
        curve_id=curve_id,
        obligor_id=obligor_id,
        role=role,
        probability_measure=probability_measure,
        currency=currency,
        as_of_date=as_of_date,
        recovery_rate=recovery_rate,
        node_times=times,
        hazard_rates=np.full(times.shape, hazard, dtype=float),
        source_quote_spreads_bps=np.full(times.shape, float(spread_bps), dtype=float),
        source_quote_types=tuple("proxy" for _ in times),
        extrapolation_mode=extrapolation_mode,
    )


def _payment_schedule(maturity: float, payment_frequency: int) -> np.ndarray:
    if maturity <= 0.0:
        raise ValueError("maturity must be positive.")
    if payment_frequency <= 0:
        raise ValueError("payment_frequency must be positive.")
    step = 1.0 / float(payment_frequency)
    count = int(math.floor(maturity / step + 1e-12))
    values = [step * index for index in range(1, count + 1)]
    if not values or values[-1] < maturity - 1e-12:
        values.append(float(maturity))
    else:
        values[-1] = float(maturity)
    return np.asarray(values, dtype=float)


def cds_legs(
    curve: CreditCurve,
    maturity_years: float,
    *,
    discount_rate: float = 0.0,
    payment_frequency: int = 4,
    accrual_on_default: bool = True,
) -> tuple[float, float]:
    """Return risky premium annuity and protection leg for a CDS maturity."""

    maturity = _finite(maturity_years, "maturity_years")
    rate = _finite(discount_rate, "discount_rate")
    schedule = _payment_schedule(maturity, payment_frequency)

    premium_annuity = 0.0
    protection_leg = 0.0
    previous_time = 0.0
    previous_survival = 1.0

    for payment_time in schedule:
        current_time = float(payment_time)
        survival = curve.survival_probability(current_time)
        discount = math.exp(-rate * current_time)
        interval = current_time - previous_time
        default_probability = previous_survival - survival
        premium_annuity += discount * survival * interval
        if accrual_on_default:
            premium_annuity += discount * 0.5 * interval * default_probability
        protection_leg += discount * curve.loss_given_default * default_probability
        previous_time = current_time
        previous_survival = survival

    return float(premium_annuity), float(protection_leg)


def par_spread_bps(
    curve: CreditCurve,
    maturity_years: float,
    *,
    discount_rate: float = 0.0,
    payment_frequency: int = 4,
    accrual_on_default: bool = True,
) -> float:
    premium, protection = cds_legs(
        curve,
        maturity_years,
        discount_rate=discount_rate,
        payment_frequency=payment_frequency,
        accrual_on_default=accrual_on_default,
    )
    if premium <= 0.0:
        raise RuntimeError("CDS premium annuity must be positive.")
    return float(10_000.0 * protection / premium)


def _candidate_curve(
    *,
    curve_id: str,
    obligor_id: str,
    role: str,
    probability_measure: str,
    currency: str,
    as_of_date: date,
    recovery_rate: float,
    node_times: Sequence[float],
    hazard_rates: Sequence[float],
    spreads: Sequence[float],
    quote_types: Sequence[str],
    extrapolation_mode: str,
) -> CreditCurve:
    return CreditCurve(
        curve_id=curve_id,
        obligor_id=obligor_id,
        role=role,
        probability_measure=probability_measure,
        currency=currency,
        as_of_date=as_of_date,
        recovery_rate=recovery_rate,
        node_times=np.asarray(node_times, dtype=float),
        hazard_rates=np.asarray(hazard_rates, dtype=float),
        source_quote_spreads_bps=np.asarray(spreads, dtype=float),
        source_quote_types=tuple(quote_types),
        extrapolation_mode=extrapolation_mode,
    )


def calibrate_piecewise_credit_curve(
    quotes: Iterable[CreditQuote],
    recovery: RecoveryAssumption,
    *,
    curve_id: str,
    role: str,
    as_of_date: date,
    max_quote_age_days: int = 5,
    max_recovery_age_days: int = 365,
    required_tenors: Sequence[float] | None = None,
    discount_rate: float = 0.0,
    payment_frequency: int = 4,
    accrual_on_default: bool = True,
    extrapolation_mode: str = "flat_hazard",
    allow_bond_spread_proxy: bool = False,
    calibration_tolerance_bps: float = 1e-9,
) -> CreditCurve:
    """Sequentially calibrate non-negative piecewise-constant hazards."""

    validated = validate_credit_quotes(
        quotes,
        as_of_date=as_of_date,
        max_age_days=max_quote_age_days,
        required_tenors=required_tenors,
        allow_bond_spread_proxy=allow_bond_spread_proxy,
    )

    first = validated[0]
    validate_recovery_assumption(
        recovery,
        as_of_date=as_of_date,
        max_age_days=max_recovery_age_days,
        expected_obligor_id=first.obligor_id,
        expected_seniority=first.seniority,
    )

    hazards: list[float] = []
    tenors: list[float] = []
    spreads: list[float] = []
    quote_types: list[str] = []

    for quote in validated:
        tenors.append(quote.tenor_years)
        spreads.append(quote.spread_bps)
        quote_types.append(quote.quote_type)

        def model_spread(candidate_hazard: float) -> float:
            curve = _candidate_curve(
                curve_id=curve_id,
                obligor_id=first.obligor_id,
                role=role,
                probability_measure=first.probability_measure,
                currency=first.currency,
                as_of_date=as_of_date,
                recovery_rate=recovery.recovery_rate,
                node_times=tenors,
                hazard_rates=[*hazards, candidate_hazard],
                spreads=spreads,
                quote_types=quote_types,
                extrapolation_mode=extrapolation_mode,
            )
            return par_spread_bps(
                curve,
                quote.tenor_years,
                discount_rate=discount_rate,
                payment_frequency=payment_frequency,
                accrual_on_default=accrual_on_default,
            )

        target = quote.spread_bps
        low = 0.0
        low_value = model_spread(low)

        if low_value > target + calibration_tolerance_bps:
            raise ValueError(
                "Quote term structure requires a negative incremental hazard; "
                f"tenor={quote.tenor_years}, floor_spread={low_value:.10f}, "
                f"target_spread={target:.10f}."
            )

        if abs(low_value - target) <= calibration_tolerance_bps:
            hazards.append(0.0)
            continue

        high = max(
            0.10,
            flat_hazard_from_spread(target, recovery.recovery_rate) * 4.0 + 0.05,
        )
        high_value = model_spread(high)

        while high_value < target and high < 100.0:
            high *= 2.0
            high_value = model_spread(high)

        if high_value < target:
            raise RuntimeError("Could not bracket the hazard-rate calibration root.")

        for _ in range(200):
            midpoint = 0.5 * (low + high)
            midpoint_value = model_spread(midpoint)
            if abs(midpoint_value - target) <= calibration_tolerance_bps:
                low = high = midpoint
                break
            if midpoint_value < target:
                low = midpoint
            else:
                high = midpoint

        hazards.append(0.5 * (low + high))

    curve = _candidate_curve(
        curve_id=curve_id,
        obligor_id=first.obligor_id,
        role=role,
        probability_measure=first.probability_measure,
        currency=first.currency,
        as_of_date=as_of_date,
        recovery_rate=recovery.recovery_rate,
        node_times=tenors,
        hazard_rates=hazards,
        spreads=spreads,
        quote_types=quote_types,
        extrapolation_mode=extrapolation_mode,
    )

    repricing = reprice_credit_quotes(
        curve,
        validated,
        discount_rate=discount_rate,
        payment_frequency=payment_frequency,
        accrual_on_default=accrual_on_default,
    )

    if repricing.max_abs_error_bps > max(calibration_tolerance_bps * 10.0, 1e-7):
        raise RuntimeError("Calibrated credit curve does not reprice source quotes.")

    return curve


def reprice_credit_quotes(
    curve: CreditCurve,
    quotes: Iterable[CreditQuote],
    *,
    discount_rate: float = 0.0,
    payment_frequency: int = 4,
    accrual_on_default: bool = True,
) -> CreditCurveRepricing:
    quote_list = tuple(sorted(quotes, key=lambda item: item.tenor_years))
    tenors = np.asarray([quote.tenor_years for quote in quote_list], dtype=float)
    market = np.asarray([quote.spread_bps for quote in quote_list], dtype=float)
    model = np.asarray(
        [
            par_spread_bps(
                curve,
                quote.tenor_years,
                discount_rate=discount_rate,
                payment_frequency=payment_frequency,
                accrual_on_default=accrual_on_default,
            )
            for quote in quote_list
        ],
        dtype=float,
    )
    errors = model - market
    for array in (tenors, market, model, errors):
        array.setflags(write=False)
    return CreditCurveRepricing(
        tenors=tenors,
        market_spreads_bps=market,
        model_spreads_bps=model,
        errors_bps=errors,
        max_abs_error_bps=float(np.max(np.abs(errors))),
    )


def credit_curve_sensitivity(
    quotes: Iterable[CreditQuote],
    recovery: RecoveryAssumption,
    *,
    curve_id: str,
    role: str,
    as_of_date: date,
    parallel_spread_bump_bps: float = 1.0,
    recovery_bump: float = 0.01,
    **calibration_kwargs: object,
) -> CreditCurveSensitivity:
    quote_list = tuple(quotes)
    if not quote_list:
        raise ValueError("At least one quote is required.")
    if parallel_spread_bump_bps <= 0.0:
        raise ValueError("parallel_spread_bump_bps must be positive.")
    if recovery_bump <= 0.0:
        raise ValueError("recovery_bump must be positive.")
    if recovery.recovery_rate + recovery_bump >= 1.0:
        raise ValueError("Recovery bump must keep recovery below one.")

    base = calibrate_piecewise_credit_curve(
        quote_list,
        recovery,
        curve_id=curve_id,
        role=role,
        as_of_date=as_of_date,
        **calibration_kwargs,
    )

    bumped_quotes = tuple(
        CreditQuote(
            quote_id=f"{quote.quote_id}-BUMP",
            obligor_id=quote.obligor_id,
            tenor_years=quote.tenor_years,
            spread_bps=quote.spread_bps + parallel_spread_bump_bps,
            as_of_date=quote.as_of_date,
            source_id=quote.source_id,
            quote_type=quote.quote_type,
            probability_measure=quote.probability_measure,
            currency=quote.currency,
            seniority=quote.seniority,
        )
        for quote in quote_list
    )

    spread_bumped = calibrate_piecewise_credit_curve(
        bumped_quotes,
        recovery,
        curve_id=f"{curve_id}-SPREAD-BUMP",
        role=role,
        as_of_date=as_of_date,
        **calibration_kwargs,
    )

    bumped_recovery = RecoveryAssumption(
        obligor_id=recovery.obligor_id,
        recovery_rate=recovery.recovery_rate + recovery_bump,
        as_of_date=recovery.as_of_date,
        source_id=recovery.source_id,
        seniority=recovery.seniority,
    )

    recovery_bumped = calibrate_piecewise_credit_curve(
        quote_list,
        bumped_recovery,
        curve_id=f"{curve_id}-RECOVERY-BUMP",
        role=role,
        as_of_date=as_of_date,
        **calibration_kwargs,
    )

    terminal = max(quote.tenor_years for quote in quote_list)
    base_pd = base.cumulative_default_probability(terminal)
    repricing = reprice_credit_quotes(base, quote_list)

    return CreditCurveSensitivity(
        terminal_time=float(terminal),
        base_terminal_pd=base_pd,
        parallel_spread_bump_bps=float(parallel_spread_bump_bps),
        parallel_spread_pd_delta=(
            spread_bumped.cumulative_default_probability(terminal) - base_pd
        ),
        recovery_bump=float(recovery_bump),
        recovery_pd_delta=(
            recovery_bumped.cumulative_default_probability(terminal) - base_pd
        ),
        max_quote_repricing_error_bps=repricing.max_abs_error_bps,
    )


def credit_curve_manifest(curve: CreditCurve) -> dict[str, object]:
    payload = {
        "curve_id": curve.curve_id,
        "obligor_id": curve.obligor_id,
        "role": curve.role,
        "probability_measure": curve.probability_measure,
        "currency": curve.currency,
        "as_of_date": curve.as_of_date.isoformat(),
        "recovery_rate": curve.recovery_rate,
        "node_times": curve.node_times.tolist(),
        "hazard_rates": curve.hazard_rates.tolist(),
        "source_quote_spreads_bps": curve.source_quote_spreads_bps.tolist(),
        "source_quote_types": list(curve.source_quote_types),
        "extrapolation_mode": curve.extrapolation_mode,
    }
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    payload["credit_curve_sha256"] = hashlib.sha256(
        serialized.encode("utf-8")
    ).hexdigest()
    return payload

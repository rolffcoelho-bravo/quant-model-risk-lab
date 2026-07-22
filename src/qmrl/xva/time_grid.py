"""Deterministic exposure and margin time-grid construction."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta


_ALLOWED_BUSINESS_DAY_CONVENTIONS = {
    "following",
    "preceding",
    "unadjusted",
}


def year_fraction_act_365(start: date, end: date) -> float:
    """Return a non-negative ACT/365 year fraction."""

    if end < start:
        raise ValueError("end must not precede start.")

    return (end - start).days / 365.0


def adjust_business_day(
    value: date,
    convention: str = "following",
) -> date:
    """Adjust weekends using a transparent business-day convention."""

    normalized = convention.strip().lower()

    if normalized not in _ALLOWED_BUSINESS_DAY_CONVENTIONS:
        raise ValueError(
            "business_day_convention must be following, "
            "preceding, or unadjusted."
        )

    if normalized == "unadjusted" or value.weekday() < 5:
        return value

    step = 1 if normalized == "following" else -1
    adjusted = value

    while adjusted.weekday() >= 5:
        adjusted += timedelta(days=step)

    return adjusted


@dataclass(frozen=True)
class TimeGridSpec:
    """Governed parameters for the Gate 1 time grid."""

    valuation_date: date
    maturity_date: date
    exposure_interval_days: int = 30
    margin_call_interval_days: int = 1
    settlement_lag_days: int = 2
    margin_period_of_risk_days: int = 10
    business_day_convention: str = "following"
    day_count_basis: float = 365.0

    def __post_init__(self) -> None:
        if self.maturity_date <= self.valuation_date:
            raise ValueError(
                "maturity_date must be after valuation_date."
            )

        for name in (
            "exposure_interval_days",
            "margin_call_interval_days",
        ):
            if getattr(self, name) <= 0:
                raise ValueError(f"{name} must be positive.")

        for name in (
            "settlement_lag_days",
            "margin_period_of_risk_days",
        ):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} must be non-negative.")

        if self.day_count_basis <= 0:
            raise ValueError("day_count_basis must be positive.")

        normalized = self.business_day_convention.strip().lower()

        if normalized not in _ALLOWED_BUSINESS_DAY_CONVENTIONS:
            raise ValueError(
                "Unsupported business_day_convention."
            )


@dataclass(frozen=True)
class TimeGridPoint:
    """One auditable date on the unified exposure time grid."""

    index: int
    date: date
    year_fraction: float
    is_exposure_date: bool
    is_margin_call_date: bool
    is_settlement_date: bool
    is_mpor_end_date: bool
    is_maturity_date: bool


def _regular_dates(
    start: date,
    end: date,
    interval_days: int,
) -> list[date]:
    values = [start]
    current = start

    while current < end:
        current = min(
            current + timedelta(days=interval_days),
            end,
        )

        if current != values[-1]:
            values.append(current)

    return values


def _adjusted_set(
    values: list[date],
    convention: str,
) -> set[date]:
    return {
        adjust_business_day(value, convention)
        for value in values
    }


def build_time_grid(
    spec: TimeGridSpec,
) -> tuple[TimeGridPoint, ...]:
    """Build a sorted union of exposure, margin, settlement, and MPOR dates."""

    convention = spec.business_day_convention

    exposure_dates = _adjusted_set(
        _regular_dates(
            spec.valuation_date,
            spec.maturity_date,
            spec.exposure_interval_days,
        ),
        convention,
    )

    margin_call_dates = _adjusted_set(
        _regular_dates(
            spec.valuation_date,
            spec.maturity_date,
            spec.margin_call_interval_days,
        ),
        convention,
    )

    adjusted_maturity = adjust_business_day(
        spec.maturity_date,
        convention,
    )

    settlement_dates: set[date] = set()
    mpor_end_dates: set[date] = set()

    for call_date in margin_call_dates:
        settlement_date = adjust_business_day(
            call_date
            + timedelta(days=spec.settlement_lag_days),
            convention,
        )

        if settlement_date <= adjusted_maturity:
            settlement_dates.add(settlement_date)

        mpor_end_date = adjust_business_day(
            settlement_date
            + timedelta(
                days=spec.margin_period_of_risk_days
            ),
            convention,
        )

        if mpor_end_date <= adjusted_maturity:
            mpor_end_dates.add(mpor_end_date)

    all_dates = sorted(
        exposure_dates
        | margin_call_dates
        | settlement_dates
        | mpor_end_dates
        | {
            adjust_business_day(
                spec.valuation_date,
                convention,
            ),
            adjusted_maturity,
        }
    )

    if len(all_dates) != len(set(all_dates)):
        raise RuntimeError("Time-grid dates must be unique.")

    points: list[TimeGridPoint] = []

    for index, point_date in enumerate(all_dates):
        year_fraction = (
            point_date
            - adjust_business_day(
                spec.valuation_date,
                convention,
            )
        ).days / spec.day_count_basis

        points.append(
            TimeGridPoint(
                index=index,
                date=point_date,
                year_fraction=max(year_fraction, 0.0),
                is_exposure_date=(
                    point_date in exposure_dates
                ),
                is_margin_call_date=(
                    point_date in margin_call_dates
                ),
                is_settlement_date=(
                    point_date in settlement_dates
                ),
                is_mpor_end_date=(
                    point_date in mpor_end_dates
                ),
                is_maturity_date=(
                    point_date == adjusted_maturity
                ),
            )
        )

    if not points:
        raise RuntimeError("Time-grid construction returned no dates.")

    if points[-1].date != adjusted_maturity:
        raise RuntimeError(
            "The adjusted maturity date is missing."
        )

    return tuple(points)

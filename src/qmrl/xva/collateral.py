"""Collateral agreement controls and state-process simulation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
import math
from typing import Sequence

import numpy as np


_ALLOWED_DIRECTIONS = {
    "two_way",
    "receive_only",
    "post_only",
}


@dataclass(frozen=True)
class CollateralAgreement:
    """Public Gate 1 collateral agreement representation."""

    agreement_id: str
    collateral_currency: str = "USD"
    threshold_received: float = 0.0
    threshold_posted: float = 0.0
    minimum_transfer_amount: float = 0.0
    independent_amount_received: float = 0.0
    independent_amount_posted: float = 0.0
    initial_margin_received: float = 0.0
    initial_margin_posted: float = 0.0
    haircut: float = 0.0
    rounding: float = 0.01
    call_frequency_days: int = 1
    settlement_lag_days: int = 0
    margin_period_of_risk_days: int = 10
    remuneration_rate: float = 0.0
    rehypothecation_allowed: bool = False
    direction: str = "two_way"

    def __post_init__(self) -> None:
        if not self.agreement_id.strip():
            raise ValueError(
                "agreement_id must not be empty."
            )

        if len(self.collateral_currency.strip()) != 3:
            raise ValueError(
                "collateral_currency must be a "
                "three-letter code."
            )

        for name in (
            "threshold_received",
            "threshold_posted",
            "minimum_transfer_amount",
            "independent_amount_received",
            "independent_amount_posted",
            "initial_margin_received",
            "initial_margin_posted",
            "rounding",
        ):
            if getattr(self, name) < 0:
                raise ValueError(
                    f"{name} must be non-negative."
                )

        if not 0.0 <= self.haircut < 1.0:
            raise ValueError("haircut must be in [0, 1).")

        if self.call_frequency_days <= 0:
            raise ValueError(
                "call_frequency_days must be positive."
            )

        for name in (
            "settlement_lag_days",
            "margin_period_of_risk_days",
        ):
            if getattr(self, name) < 0:
                raise ValueError(
                    f"{name} must be non-negative."
                )

        if self.direction not in _ALLOWED_DIRECTIONS:
            raise ValueError(
                "direction must be two_way, receive_only, "
                "or post_only."
            )


@dataclass(frozen=True)
class CollateralPoint:
    """Collateral state observed on one grid date."""

    date: date
    clean_value: float
    required_effective_collateral: float
    face_balance: float
    effective_balance: float
    transfer_called: float
    pending_face_balance: float


def effective_collateral(
    face_balance: float,
    agreement: CollateralAgreement,
) -> float:
    """Convert signed collateral face value to effective value."""

    return float(face_balance) * (1.0 - agreement.haircut)


def required_effective_collateral(
    clean_value: float,
    agreement: CollateralAgreement,
) -> float:
    """Return signed effective collateral required by the agreement."""

    value = float(clean_value)

    if value >= 0.0:
        if agreement.direction == "post_only":
            return 0.0

        unsecured = max(
            value - agreement.threshold_received,
            0.0,
        )

        if unsecured == 0.0:
            return 0.0

        return float(
            unsecured
            + agreement.independent_amount_received
            + agreement.initial_margin_received
        )

    if agreement.direction == "receive_only":
        return 0.0

    unsecured = max(
        -value - agreement.threshold_posted,
        0.0,
    )

    if unsecured == 0.0:
        return 0.0

    return float(
        -(
            unsecured
            + agreement.independent_amount_posted
            + agreement.initial_margin_posted
        )
    )


def _target_face_amount(
    required_effective: float,
    agreement: CollateralAgreement,
) -> float:
    if required_effective == 0.0:
        return 0.0

    return (
        float(required_effective)
        / (1.0 - agreement.haircut)
    )


def _round_transfer(
    amount: float,
    increment: float,
) -> float:
    if increment == 0.0:
        return float(amount)

    units = math.floor(
        abs(float(amount)) / increment + 0.5
    )

    return math.copysign(
        units * increment,
        float(amount),
    )


def _following_weekday(value: date) -> date:
    adjusted = value

    while adjusted.weekday() >= 5:
        adjusted += timedelta(days=1)

    return adjusted


def simulate_collateral_path(
    dates: Sequence[date],
    clean_values: Sequence[float],
    agreement: CollateralAgreement,
    *,
    call_dates: Sequence[date] | None = None,
) -> tuple[CollateralPoint, ...]:
    """Simulate collateral calls, pending transfers, and settlement."""

    if len(dates) != len(clean_values):
        raise ValueError(
            "dates and clean_values must have equal length."
        )

    if not dates:
        raise ValueError(
            "At least one collateral observation is required."
        )

    normalized_dates = list(dates)

    if normalized_dates != sorted(normalized_dates):
        raise ValueError("dates must be sorted.")

    if len(normalized_dates) != len(set(normalized_dates)):
        raise ValueError("dates must be unique.")

    value_array = np.asarray(
        clean_values,
        dtype=float,
    )

    if not np.isfinite(value_array).all():
        raise ValueError(
            "clean_values must be finite."
        )

    governed_call_dates = (
        set(call_dates)
        if call_dates is not None
        else {
            point_date
            for point_date in normalized_dates
            if (
                point_date - normalized_dates[0]
            ).days
            % agreement.call_frequency_days
            == 0
        }
    )

    face_balance = 0.0
    pending: list[tuple[date, float]] = []
    points: list[CollateralPoint] = []

    for point_date, clean_value in zip(
        normalized_dates,
        value_array,
        strict=True,
    ):
        settled_amount = 0.0
        remaining_pending: list[
            tuple[date, float]
        ] = []

        for settlement_date, transfer in pending:
            if settlement_date <= point_date:
                settled_amount += transfer
            else:
                remaining_pending.append(
                    (settlement_date, transfer)
                )

        face_balance += settled_amount
        pending = remaining_pending
        transfer_called = 0.0

        required = required_effective_collateral(
            float(clean_value),
            agreement,
        )

        if point_date in governed_call_dates:
            target_face = _target_face_amount(
                required,
                agreement,
            )

            committed_face = (
                face_balance
                + sum(
                    transfer
                    for _, transfer in pending
                )
            )

            proposed_transfer = (
                target_face - committed_face
            )

            if (
                abs(proposed_transfer)
                >= agreement.minimum_transfer_amount
            ):
                transfer_called = _round_transfer(
                    proposed_transfer,
                    agreement.rounding,
                )

                settlement_date = _following_weekday(
                    point_date
                    + timedelta(
                        days=agreement.settlement_lag_days
                    )
                )

                if settlement_date <= point_date:
                    face_balance += transfer_called
                else:
                    pending.append(
                        (
                            settlement_date,
                            transfer_called,
                        )
                    )

        points.append(
            CollateralPoint(
                date=point_date,
                clean_value=float(clean_value),
                required_effective_collateral=required,
                face_balance=float(face_balance),
                effective_balance=effective_collateral(
                    face_balance,
                    agreement,
                ),
                transfer_called=float(transfer_called),
                pending_face_balance=float(
                    sum(
                        transfer
                        for _, transfer in pending
                    )
                ),
            )
        )

    return tuple(points)

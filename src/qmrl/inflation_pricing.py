"""Inflation derivatives validation utilities.

This module provides transparent validation functions for a standardized
zero-coupon inflation-linked validation instrument.

The goal is not to reproduce a proprietary inflation-swap desk model. The goal
is to create public model-risk evidence: input mapping, payoff logic, discounting,
shock sensitivity, inflation DV01 and validation thresholds.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class InflationValidationResult:
    fixed_rate_percent: float
    market_rate_percent: float
    nominal_discount_rate_percent: float
    maturity_years: float
    notional: float
    value: float
    value_percent_notional: float
    inflation_dv01: float


def validate_inflation_inputs(
    fixed_rate_percent: float,
    market_rate_percent: float,
    nominal_discount_rate_percent: float,
    maturity_years: float,
    notional: float,
) -> None:
    if maturity_years <= 0:
        raise ValueError("Maturity must be positive.")

    if notional <= 0:
        raise ValueError("Notional must be positive.")

    for name, value in {
        "fixed_rate_percent": fixed_rate_percent,
        "market_rate_percent": market_rate_percent,
        "nominal_discount_rate_percent": nominal_discount_rate_percent,
    }.items():
        if not math.isfinite(value):
            raise ValueError(f"{name} must be finite.")


def compounded_inflation_factor(rate_percent: float, maturity_years: float) -> float:
    if maturity_years <= 0:
        raise ValueError("Maturity must be positive.")

    return float((1.0 + rate_percent / 100.0) ** maturity_years)


def nominal_discount_factor(rate_percent: float, maturity_years: float) -> float:
    if maturity_years <= 0:
        raise ValueError("Maturity must be positive.")

    return float(math.exp(-(rate_percent / 100.0) * maturity_years))


def zero_coupon_inflation_value(
    fixed_rate_percent: float,
    market_rate_percent: float,
    nominal_discount_rate_percent: float,
    maturity_years: float = 10.0,
    notional: float = 1_000_000.0,
) -> float:
    validate_inflation_inputs(
        fixed_rate_percent=fixed_rate_percent,
        market_rate_percent=market_rate_percent,
        nominal_discount_rate_percent=nominal_discount_rate_percent,
        maturity_years=maturity_years,
        notional=notional,
    )

    fixed_factor = compounded_inflation_factor(fixed_rate_percent, maturity_years)
    market_factor = compounded_inflation_factor(market_rate_percent, maturity_years)
    discount_factor = nominal_discount_factor(nominal_discount_rate_percent, maturity_years)

    return float(notional * (market_factor - fixed_factor) * discount_factor)


def inflation_dv01(
    fixed_rate_percent: float,
    market_rate_percent: float,
    nominal_discount_rate_percent: float,
    maturity_years: float = 10.0,
    notional: float = 1_000_000.0,
) -> float:
    value_up = zero_coupon_inflation_value(
        fixed_rate_percent=fixed_rate_percent,
        market_rate_percent=market_rate_percent + 0.01,
        nominal_discount_rate_percent=nominal_discount_rate_percent,
        maturity_years=maturity_years,
        notional=notional,
    )

    value_down = zero_coupon_inflation_value(
        fixed_rate_percent=fixed_rate_percent,
        market_rate_percent=market_rate_percent - 0.01,
        nominal_discount_rate_percent=nominal_discount_rate_percent,
        maturity_years=maturity_years,
        notional=notional,
    )

    return float((value_up - value_down) / 2.0)


def build_inflation_shock_table(
    fixed_rate_percent: float,
    base_market_rate_percent: float,
    nominal_discount_rate_percent: float,
    maturity_years: float = 10.0,
    notional: float = 1_000_000.0,
    shock_basis_points: list[float] | None = None,
) -> pd.DataFrame:
    if shock_basis_points is None:
        shock_basis_points = [-150.0, -100.0, -50.0, -25.0, 0.0, 25.0, 50.0, 100.0, 150.0]

    rows = []

    for shock_bp in shock_basis_points:
        shocked_market_rate = base_market_rate_percent + shock_bp / 100.0
        value = zero_coupon_inflation_value(
            fixed_rate_percent=fixed_rate_percent,
            market_rate_percent=shocked_market_rate,
            nominal_discount_rate_percent=nominal_discount_rate_percent,
            maturity_years=maturity_years,
            notional=notional,
        )

        rows.append(
            {
                "inflation_shock_bp": shock_bp,
                "fixed_rate_percent": fixed_rate_percent,
                "market_rate_percent": shocked_market_rate,
                "nominal_discount_rate_percent": nominal_discount_rate_percent,
                "maturity_years": maturity_years,
                "notional": notional,
                "value": value,
                "value_percent_notional": value / notional * 100.0,
            }
        )

    return pd.DataFrame(rows)


def build_inflation_validation_result(
    fixed_rate_percent: float,
    market_rate_percent: float,
    nominal_discount_rate_percent: float,
    maturity_years: float = 10.0,
    notional: float = 1_000_000.0,
) -> InflationValidationResult:
    value = zero_coupon_inflation_value(
        fixed_rate_percent=fixed_rate_percent,
        market_rate_percent=market_rate_percent,
        nominal_discount_rate_percent=nominal_discount_rate_percent,
        maturity_years=maturity_years,
        notional=notional,
    )

    dv01 = inflation_dv01(
        fixed_rate_percent=fixed_rate_percent,
        market_rate_percent=market_rate_percent,
        nominal_discount_rate_percent=nominal_discount_rate_percent,
        maturity_years=maturity_years,
        notional=notional,
    )

    return InflationValidationResult(
        fixed_rate_percent=fixed_rate_percent,
        market_rate_percent=market_rate_percent,
        nominal_discount_rate_percent=nominal_discount_rate_percent,
        maturity_years=maturity_years,
        notional=notional,
        value=value,
        value_percent_notional=value / notional * 100.0,
        inflation_dv01=dv01,
    )

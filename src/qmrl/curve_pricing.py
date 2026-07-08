"""Curve pricing validation utilities.

This module provides simple transparent pricing checks for public model-risk
evidence. It is not a production pricing library. The goal is to show how a
reviewer can validate curve inputs, interpolation, discount factors, bond
valuation and interest-rate sensitivity from official public data.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class BondPricingResult:
    price: float
    dv01: float
    base_yield_shift_bp: float
    maturity_years: float
    coupon_rate: float
    face_value: float
    frequency: int


def validate_curve_inputs(maturities_years: list[float], yields_percent: list[float]) -> None:
    if len(maturities_years) != len(yields_percent):
        raise ValueError("maturities_years and yields_percent must have the same length.")

    if len(maturities_years) < 2:
        raise ValueError("At least two curve nodes are required.")

    if any(maturity <= 0 for maturity in maturities_years):
        raise ValueError("Curve maturities must be positive.")

    if any(not np.isfinite(rate) for rate in yields_percent):
        raise ValueError("Curve yields must be finite numbers.")

    if sorted(maturities_years) != list(maturities_years):
        raise ValueError("Curve maturities must be sorted in ascending order.")


def interpolate_zero_rate(
    maturities_years: list[float],
    yields_percent: list[float],
    target_maturity_years: float,
) -> float:
    validate_curve_inputs(maturities_years, yields_percent)

    if target_maturity_years <= 0:
        raise ValueError("Target maturity must be positive.")

    return float(
        np.interp(
            target_maturity_years,
            maturities_years,
            yields_percent,
            left=yields_percent[0],
            right=yields_percent[-1],
        )
    )


def discount_factor_continuous(rate_percent: float, maturity_years: float) -> float:
    if maturity_years <= 0:
        raise ValueError("Maturity must be positive.")

    rate_decimal = rate_percent / 100.0
    return float(math.exp(-rate_decimal * maturity_years))


def build_discount_curve(
    maturities_years: list[float],
    yields_percent: list[float],
    target_maturities_years: list[float],
) -> pd.DataFrame:
    rows = []

    for maturity in target_maturities_years:
        rate = interpolate_zero_rate(maturities_years, yields_percent, maturity)
        rows.append(
            {
                "maturity_years": maturity,
                "interpolated_zero_rate_percent": rate,
                "discount_factor_continuous": discount_factor_continuous(rate, maturity),
            }
        )

    return pd.DataFrame(rows)


def fixed_rate_bond_cashflows(
    maturity_years: float,
    coupon_rate: float,
    face_value: float = 100.0,
    frequency: int = 2,
) -> pd.DataFrame:
    if maturity_years <= 0:
        raise ValueError("Bond maturity must be positive.")

    if frequency <= 0:
        raise ValueError("Coupon frequency must be positive.")

    number_of_payments = int(round(maturity_years * frequency))
    coupon_payment = face_value * coupon_rate / frequency

    rows = []
    for payment_number in range(1, number_of_payments + 1):
        payment_time = payment_number / frequency
        cashflow = coupon_payment
        if payment_number == number_of_payments:
            cashflow += face_value

        rows.append(
            {
                "payment_number": payment_number,
                "payment_time_years": payment_time,
                "cashflow": cashflow,
            }
        )

    return pd.DataFrame(rows)


def price_fixed_rate_bond_from_curve(
    maturities_years: list[float],
    yields_percent: list[float],
    maturity_years: float,
    coupon_rate: float,
    face_value: float = 100.0,
    frequency: int = 2,
    parallel_shift_bp: float = 0.0,
) -> float:
    cashflows = fixed_rate_bond_cashflows(
        maturity_years=maturity_years,
        coupon_rate=coupon_rate,
        face_value=face_value,
        frequency=frequency,
    )

    shifted_yields = [rate + parallel_shift_bp / 100.0 for rate in yields_percent]

    price = 0.0
    for _, row in cashflows.iterrows():
        payment_time = float(row["payment_time_years"])
        zero_rate = interpolate_zero_rate(maturities_years, shifted_yields, payment_time)
        discount_factor = discount_factor_continuous(zero_rate, payment_time)
        price += float(row["cashflow"]) * discount_factor

    return float(price)


def bond_dv01_from_curve(
    maturities_years: list[float],
    yields_percent: list[float],
    maturity_years: float,
    coupon_rate: float,
    face_value: float = 100.0,
    frequency: int = 2,
) -> float:
    price_down = price_fixed_rate_bond_from_curve(
        maturities_years=maturities_years,
        yields_percent=yields_percent,
        maturity_years=maturity_years,
        coupon_rate=coupon_rate,
        face_value=face_value,
        frequency=frequency,
        parallel_shift_bp=-1.0,
    )

    price_up = price_fixed_rate_bond_from_curve(
        maturities_years=maturities_years,
        yields_percent=yields_percent,
        maturity_years=maturity_years,
        coupon_rate=coupon_rate,
        face_value=face_value,
        frequency=frequency,
        parallel_shift_bp=1.0,
    )

    return float((price_down - price_up) / 2.0)


def build_parallel_shock_table(
    maturities_years: list[float],
    yields_percent: list[float],
    maturity_years: float,
    coupon_rate: float,
    face_value: float = 100.0,
    frequency: int = 2,
    shock_basis_points: list[float] | None = None,
) -> pd.DataFrame:
    if shock_basis_points is None:
        shock_basis_points = [-100.0, -50.0, -25.0, 0.0, 25.0, 50.0, 100.0]

    base_price = price_fixed_rate_bond_from_curve(
        maturities_years=maturities_years,
        yields_percent=yields_percent,
        maturity_years=maturity_years,
        coupon_rate=coupon_rate,
        face_value=face_value,
        frequency=frequency,
        parallel_shift_bp=0.0,
    )

    rows = []
    for shock in shock_basis_points:
        shocked_price = price_fixed_rate_bond_from_curve(
            maturities_years=maturities_years,
            yields_percent=yields_percent,
            maturity_years=maturity_years,
            coupon_rate=coupon_rate,
            face_value=face_value,
            frequency=frequency,
            parallel_shift_bp=shock,
        )

        rows.append(
            {
                "parallel_shift_bp": shock,
                "bond_price": shocked_price,
                "price_change": shocked_price - base_price,
                "price_change_percent": (shocked_price / base_price - 1.0) * 100.0,
            }
        )

    return pd.DataFrame(rows)


def build_curve_pricing_result(
    maturities_years: list[float],
    yields_percent: list[float],
    maturity_years: float,
    coupon_rate: float,
    face_value: float = 100.0,
    frequency: int = 2,
) -> BondPricingResult:
    price = price_fixed_rate_bond_from_curve(
        maturities_years=maturities_years,
        yields_percent=yields_percent,
        maturity_years=maturity_years,
        coupon_rate=coupon_rate,
        face_value=face_value,
        frequency=frequency,
    )

    dv01 = bond_dv01_from_curve(
        maturities_years=maturities_years,
        yields_percent=yields_percent,
        maturity_years=maturity_years,
        coupon_rate=coupon_rate,
        face_value=face_value,
        frequency=frequency,
    )

    return BondPricingResult(
        price=price,
        dv01=dv01,
        base_yield_shift_bp=0.0,
        maturity_years=maturity_years,
        coupon_rate=coupon_rate,
        face_value=face_value,
        frequency=frequency,
    )

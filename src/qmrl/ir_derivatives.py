"""Interest-rate derivatives pricing validation utilities.

This module implements transparent fixed-for-floating swap valuation controls:
payment schedule, discount factors, par swap rate, fixed leg PV, floating leg PV,
payer/receiver NPV, DV01 and parallel curve-shock sensitivity.

The scope is deterministic single-curve validation. Multi-curve CSA discounting,
basis curves, XVA and optionality require separate validation layers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class SwapValuationResult:
    """Container for fixed-for-floating swap valuation results."""

    notional: float
    fixed_rate: float
    par_rate: float
    maturity_years: float
    payment_frequency: int
    fixed_leg_pv: float
    floating_leg_pv: float
    payer_swap_npv: float
    receiver_swap_npv: float
    annuity: float
    final_discount_factor: float


def payment_times(maturity_years: float, payment_frequency: int = 2) -> np.ndarray:
    """Return cash-flow payment times in years."""

    if maturity_years <= 0:
        raise ValueError("maturity_years must be positive.")
    if payment_frequency <= 0:
        raise ValueError("payment_frequency must be positive.")

    number_of_payments = int(round(maturity_years * payment_frequency))
    if number_of_payments <= 0:
        raise ValueError("payment schedule has no payments.")

    return np.arange(1, number_of_payments + 1, dtype=float) / float(payment_frequency)


def validate_zero_curve(tenor_years: Iterable[float], zero_rates: Iterable[float]) -> tuple[np.ndarray, np.ndarray]:
    """Validate and sort zero-curve tenors and decimal zero rates."""

    tenors = np.asarray(list(tenor_years), dtype=float)
    rates = np.asarray(list(zero_rates), dtype=float)

    if tenors.ndim != 1 or rates.ndim != 1:
        raise ValueError("tenor_years and zero_rates must be one-dimensional.")
    if len(tenors) != len(rates):
        raise ValueError("tenor_years and zero_rates must have the same length.")
    if len(tenors) < 2:
        raise ValueError("at least two curve points are required.")
    if np.any(tenors <= 0):
        raise ValueError("curve tenors must be positive.")
    if np.any(~np.isfinite(rates)):
        raise ValueError("zero rates must be finite.")

    order = np.argsort(tenors)
    tenors = tenors[order]
    rates = rates[order]

    if np.any(np.diff(tenors) <= 0):
        raise ValueError("curve tenors must be unique.")

    return tenors, rates


def interpolate_zero_rates(
    times: Iterable[float],
    tenor_years: Iterable[float],
    zero_rates: Iterable[float],
    parallel_shift_bp: float = 0.0,
) -> np.ndarray:
    """Interpolate decimal zero rates and apply a parallel shift in basis points."""

    cashflow_times = np.asarray(list(times), dtype=float)
    if np.any(cashflow_times <= 0):
        raise ValueError("cash-flow times must be positive.")

    tenors, rates = validate_zero_curve(tenor_years, zero_rates)
    interpolated = np.interp(cashflow_times, tenors, rates, left=rates[0], right=rates[-1])
    return interpolated + float(parallel_shift_bp) / 10000.0


def discount_factors_from_zero_rates(
    times: Iterable[float],
    tenor_years: Iterable[float],
    zero_rates: Iterable[float],
    parallel_shift_bp: float = 0.0,
) -> np.ndarray:
    """Build continuously compounded discount factors from zero rates."""

    cashflow_times = np.asarray(list(times), dtype=float)
    shifted_rates = interpolate_zero_rates(cashflow_times, tenor_years, zero_rates, parallel_shift_bp)
    discount_factors = np.exp(-shifted_rates * cashflow_times)

    if np.any(discount_factors <= 0):
        raise ValueError("discount factors must be positive.")
    return discount_factors


def swap_annuity(discount_factors: Iterable[float], payment_frequency: int = 2) -> float:
    """Return fixed-leg annuity for a standard swap."""

    dfs = np.asarray(list(discount_factors), dtype=float)
    if np.any(dfs <= 0):
        raise ValueError("discount factors must be positive.")
    return float(np.sum(dfs) / float(payment_frequency))


def par_swap_rate(discount_factors: Iterable[float], payment_frequency: int = 2) -> float:
    """Return the fixed rate that makes a par fixed-for-floating swap worth zero."""

    dfs = np.asarray(list(discount_factors), dtype=float)
    annuity_value = swap_annuity(dfs, payment_frequency)
    if annuity_value <= 0:
        raise ValueError("swap annuity must be positive.")
    return float((1.0 - dfs[-1]) / annuity_value)


def price_fixed_float_swap(
    notional: float,
    fixed_rate: float | None,
    maturity_years: float,
    payment_frequency: int,
    tenor_years: Iterable[float],
    zero_rates: Iterable[float],
    parallel_shift_bp: float = 0.0,
) -> SwapValuationResult:
    """Price a vanilla fixed-for-floating interest-rate swap.

    Payer swap NPV is floating-leg PV minus fixed-leg PV.
    Receiver swap NPV is fixed-leg PV minus floating-leg PV.
    """

    if notional <= 0:
        raise ValueError("notional must be positive.")

    times = payment_times(maturity_years, payment_frequency)
    dfs = discount_factors_from_zero_rates(times, tenor_years, zero_rates, parallel_shift_bp)
    annuity_value = swap_annuity(dfs, payment_frequency)
    par_rate = par_swap_rate(dfs, payment_frequency)

    coupon_rate = par_rate if fixed_rate is None else float(fixed_rate)

    fixed_leg_pv = float(notional * coupon_rate * annuity_value)
    floating_leg_pv = float(notional * (1.0 - dfs[-1]))
    payer_npv = float(floating_leg_pv - fixed_leg_pv)
    receiver_npv = float(fixed_leg_pv - floating_leg_pv)

    return SwapValuationResult(
        notional=float(notional),
        fixed_rate=coupon_rate,
        par_rate=par_rate,
        maturity_years=float(maturity_years),
        payment_frequency=int(payment_frequency),
        fixed_leg_pv=fixed_leg_pv,
        floating_leg_pv=floating_leg_pv,
        payer_swap_npv=payer_npv,
        receiver_swap_npv=receiver_npv,
        annuity=annuity_value,
        final_discount_factor=float(dfs[-1]),
    )


def parallel_shift_table(
    notional: float,
    fixed_rate: float,
    maturity_years: float,
    payment_frequency: int,
    tenor_years: Iterable[float],
    zero_rates: Iterable[float],
    shocks_bp: Iterable[float],
) -> pd.DataFrame:
    """Return swap valuation table under parallel curve shocks."""

    rows = []
    base = price_fixed_float_swap(
        notional=notional,
        fixed_rate=fixed_rate,
        maturity_years=maturity_years,
        payment_frequency=payment_frequency,
        tenor_years=tenor_years,
        zero_rates=zero_rates,
        parallel_shift_bp=0.0,
    )

    for shock in shocks_bp:
        result = price_fixed_float_swap(
            notional=notional,
            fixed_rate=fixed_rate,
            maturity_years=maturity_years,
            payment_frequency=payment_frequency,
            tenor_years=tenor_years,
            zero_rates=zero_rates,
            parallel_shift_bp=float(shock),
        )
        rows.append(
            {
                "curve_shift_bp": float(shock),
                "par_swap_rate": result.par_rate,
                "fixed_leg_pv": result.fixed_leg_pv,
                "floating_leg_pv": result.floating_leg_pv,
                "payer_swap_npv": result.payer_swap_npv,
                "receiver_swap_npv": result.receiver_swap_npv,
                "payer_npv_change": result.payer_swap_npv - base.payer_swap_npv,
                "receiver_npv_change": result.receiver_swap_npv - base.receiver_swap_npv,
            }
        )

    return pd.DataFrame(rows)


def parallel_shift_dv01(
    notional: float,
    fixed_rate: float,
    maturity_years: float,
    payment_frequency: int,
    tenor_years: Iterable[float],
    zero_rates: Iterable[float],
) -> dict[str, float]:
    """Return central-difference one-basis-point sensitivity."""

    up = price_fixed_float_swap(
        notional=notional,
        fixed_rate=fixed_rate,
        maturity_years=maturity_years,
        payment_frequency=payment_frequency,
        tenor_years=tenor_years,
        zero_rates=zero_rates,
        parallel_shift_bp=1.0,
    )
    down = price_fixed_float_swap(
        notional=notional,
        fixed_rate=fixed_rate,
        maturity_years=maturity_years,
        payment_frequency=payment_frequency,
        tenor_years=tenor_years,
        zero_rates=zero_rates,
        parallel_shift_bp=-1.0,
    )

    return {
        "payer_dv01": float((up.payer_swap_npv - down.payer_swap_npv) / 2.0),
        "receiver_dv01": float((up.receiver_swap_npv - down.receiver_swap_npv) / 2.0),
    }

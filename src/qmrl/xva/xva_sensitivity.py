"""Controlled XVA sensitivities for Gate 5."""

from __future__ import annotations

from dataclasses import dataclass
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


@dataclass(frozen=True)
class XVASensitivityReport:
    """Standard parallel sensitivity deltas against the Gate 5 base result."""

    credit_spread_bump_bps: float
    recovery_bump: float
    funding_spread_bump_bps: float
    discount_rate_bump_bps: float
    counterparty_spread_cva_delta: float
    own_spread_dva_delta: float
    counterparty_recovery_cva_delta: float
    own_recovery_dva_delta: float
    funding_cost_fca_delta: float
    funding_benefit_fba_delta: float
    discount_cva_delta: float
    discount_dva_delta: float


def shift_credit_curve(
    curve: CreditCurve,
    *,
    spread_bump_bps: float = 0.0,
    recovery_bump: float = 0.0,
) -> CreditCurve:
    """Apply a controlled spread/LGD approximation to piecewise hazards."""

    bump = float(spread_bump_bps)
    new_recovery = curve.recovery_rate + float(recovery_bump)
    if not 0.0 <= new_recovery < 1.0:
        raise ValueError("Shifted recovery_rate must remain in [0, 1).")
    old_lgd = curve.loss_given_default
    new_lgd = 1.0 - new_recovery
    hazards = curve.hazard_rates * old_lgd / new_lgd
    hazards = hazards + bump / 10000.0 / new_lgd
    if np.any(hazards < -1e-14):
        raise ValueError("The requested spread bump implies negative hazards.")
    hazards = np.maximum(hazards, 0.0)
    spreads = curve.source_quote_spreads_bps + bump
    if np.any(spreads < -1e-12):
        raise ValueError("The requested spread bump implies negative spreads.")

    return CreditCurve(
        curve_id=curve.curve_id + "-SHIFT",
        obligor_id=curve.obligor_id,
        role=curve.role,
        probability_measure=curve.probability_measure,
        currency=curve.currency,
        as_of_date=curve.as_of_date,
        recovery_rate=new_recovery,
        node_times=curve.node_times,
        hazard_rates=hazards,
        source_quote_spreads_bps=np.maximum(spreads, 0.0),
        source_quote_types=curve.source_quote_types,
        extrapolation_mode=curve.extrapolation_mode,
    )


def shift_discount_curve(
    curve: DiscountCurve,
    *,
    rate_bump_bps: float,
) -> DiscountCurve:
    bump = float(rate_bump_bps) / 10000.0
    factors = curve.discount_factors * np.exp(-bump * curve.times)
    return DiscountCurve(
        curve_id=curve.curve_id + "-SHIFT",
        currency=curve.currency,
        as_of_date=curve.as_of_date,
        times=curve.times,
        discount_factors=factors,
        extrapolation_mode=curve.extrapolation_mode,
    )


def shift_funding_curve(
    curve: FundingCurve,
    *,
    borrowing_bump_bps: float = 0.0,
    lending_bump_bps: float = 0.0,
) -> FundingCurve:
    return FundingCurve(
        curve_id=curve.curve_id + "-SHIFT",
        currency=curve.currency,
        as_of_date=curve.as_of_date,
        times=curve.times,
        borrowing_spreads_bps=(
            curve.borrowing_spreads_bps + float(borrowing_bump_bps)
        ),
        lending_spreads_bps=(
            curve.lending_spreads_bps + float(lending_bump_bps)
        ),
        extrapolation_mode=curve.extrapolation_mode,
    )


def run_standard_xva_sensitivities(
    exposure: XVAExposureInput,
    *,
    counterparty_curves: Mapping[str, CreditCurve],
    own_curve: CreditCurve,
    discount_curve: DiscountCurve,
    funding_curve: FundingCurve,
    policy: XVAIntegrationPolicy,
    credit_spread_bump_bps: float = 10.0,
    recovery_bump: float = 0.01,
    funding_spread_bump_bps: float = 10.0,
    discount_rate_bump_bps: float = 10.0,
) -> XVASensitivityReport:
    """Calculate standard one-factor-at-a-time Gate 5 sensitivity evidence."""

    base = integrate_xva(
        exposure,
        counterparty_curves=counterparty_curves,
        own_curve=own_curve,
        discount_curve=discount_curve,
        funding_curve=funding_curve,
        policy=policy,
    )

    cp_spread_curves = {
        key: shift_credit_curve(value, spread_bump_bps=credit_spread_bump_bps)
        for key, value in counterparty_curves.items()
    }
    cp_spread = integrate_xva(
        exposure,
        counterparty_curves=cp_spread_curves,
        own_curve=own_curve,
        discount_curve=discount_curve,
        funding_curve=funding_curve,
        policy=policy,
    )
    own_spread = integrate_xva(
        exposure,
        counterparty_curves=counterparty_curves,
        own_curve=shift_credit_curve(
            own_curve,
            spread_bump_bps=credit_spread_bump_bps,
        ),
        discount_curve=discount_curve,
        funding_curve=funding_curve,
        policy=policy,
    )
    cp_recovery = integrate_xva(
        exposure,
        counterparty_curves={
            key: shift_credit_curve(value, recovery_bump=recovery_bump)
            for key, value in counterparty_curves.items()
        },
        own_curve=own_curve,
        discount_curve=discount_curve,
        funding_curve=funding_curve,
        policy=policy,
    )
    own_recovery = integrate_xva(
        exposure,
        counterparty_curves=counterparty_curves,
        own_curve=shift_credit_curve(own_curve, recovery_bump=recovery_bump),
        discount_curve=discount_curve,
        funding_curve=funding_curve,
        policy=policy,
    )
    funding_cost = integrate_xva(
        exposure,
        counterparty_curves=counterparty_curves,
        own_curve=own_curve,
        discount_curve=discount_curve,
        funding_curve=shift_funding_curve(
            funding_curve,
            borrowing_bump_bps=funding_spread_bump_bps,
        ),
        policy=policy,
    )
    funding_benefit = integrate_xva(
        exposure,
        counterparty_curves=counterparty_curves,
        own_curve=own_curve,
        discount_curve=discount_curve,
        funding_curve=shift_funding_curve(
            funding_curve,
            lending_bump_bps=funding_spread_bump_bps,
        ),
        policy=policy,
    )
    discount = integrate_xva(
        exposure,
        counterparty_curves=counterparty_curves,
        own_curve=own_curve,
        discount_curve=shift_discount_curve(
            discount_curve,
            rate_bump_bps=discount_rate_bump_bps,
        ),
        funding_curve=funding_curve,
        policy=policy,
    )

    return XVASensitivityReport(
        credit_spread_bump_bps=float(credit_spread_bump_bps),
        recovery_bump=float(recovery_bump),
        funding_spread_bump_bps=float(funding_spread_bump_bps),
        discount_rate_bump_bps=float(discount_rate_bump_bps),
        counterparty_spread_cva_delta=cp_spread.cva - base.cva,
        own_spread_dva_delta=own_spread.dva - base.dva,
        counterparty_recovery_cva_delta=cp_recovery.cva - base.cva,
        own_recovery_dva_delta=own_recovery.dva - base.dva,
        funding_cost_fca_delta=funding_cost.fca - base.fca,
        funding_benefit_fba_delta=funding_benefit.fba - base.fba,
        discount_cva_delta=discount.cva - base.cva,
        discount_dva_delta=discount.dva - base.dva,
    )

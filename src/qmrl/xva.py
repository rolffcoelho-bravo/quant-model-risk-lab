from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np


@dataclass(frozen=True)
class XVAAssumptions:
    counterparty_spread_bps: float = 100.0
    own_spread_bps: float = 80.0
    funding_spread_bps: float = 50.0
    recovery_rate: float = 0.40
    horizon_years: float = 5.0


def validate_recovery_rate(recovery_rate: float) -> None:
    if not 0.0 <= recovery_rate < 1.0:
        raise ValueError("recovery_rate must be in [0, 1).")


def spread_bps_to_decimal(spread_bps: float) -> float:
    return float(spread_bps) / 10_000.0


def hazard_rate_from_spread(spread_bps: float, recovery_rate: float) -> float:
    validate_recovery_rate(recovery_rate)
    loss_given_default = 1.0 - recovery_rate
    return spread_bps_to_decimal(spread_bps) / loss_given_default


def cumulative_default_probability(spread_bps: float, recovery_rate: float, horizon_years: float) -> float:
    if horizon_years <= 0:
        raise ValueError("horizon_years must be positive.")
    hazard = hazard_rate_from_spread(spread_bps, recovery_rate)
    return 1.0 - math.exp(-hazard * horizon_years)


def scenario_exposures(clean_values: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    values = np.asarray(clean_values, dtype=float)
    positive_exposure = np.maximum(values, 0.0)
    negative_exposure = np.maximum(-values, 0.0)
    return positive_exposure, negative_exposure


def compute_xva_from_clean_values(
    clean_values: np.ndarray,
    clean_value_at_base: float,
    discount_rate: float,
    assumptions: XVAAssumptions,
) -> dict[str, float]:
    validate_recovery_rate(assumptions.recovery_rate)

    if assumptions.horizon_years <= 0:
        raise ValueError("horizon_years must be positive.")

    positive_exposure, negative_exposure = scenario_exposures(clean_values)

    expected_exposure = float(np.mean(positive_exposure))
    expected_negative_exposure = float(np.mean(negative_exposure))
    pfe_95 = float(np.quantile(positive_exposure, 0.95))

    loss_given_default = 1.0 - assumptions.recovery_rate
    counterparty_pd = cumulative_default_probability(
        assumptions.counterparty_spread_bps,
        assumptions.recovery_rate,
        assumptions.horizon_years,
    )
    own_pd = cumulative_default_probability(
        assumptions.own_spread_bps,
        assumptions.recovery_rate,
        assumptions.horizon_years,
    )

    discount_factor = math.exp(-float(discount_rate) * assumptions.horizon_years)
    funding_spread_decimal = spread_bps_to_decimal(assumptions.funding_spread_bps)

    cva = expected_exposure * loss_given_default * counterparty_pd * discount_factor
    dva = expected_negative_exposure * loss_given_default * own_pd * discount_factor
    fva = expected_exposure * funding_spread_decimal * assumptions.horizon_years * discount_factor

    xva_reserve = cva - dva + fva
    xva_adjusted_value = float(clean_value_at_base) - xva_reserve

    return {
        "expected_exposure": expected_exposure,
        "expected_negative_exposure": expected_negative_exposure,
        "pfe_95": pfe_95,
        "counterparty_pd": counterparty_pd,
        "own_pd": own_pd,
        "discount_factor": discount_factor,
        "cva": cva,
        "dva": dva,
        "fva": fva,
        "xva_reserve": xva_reserve,
        "xva_adjusted_value": xva_adjusted_value,
        "loss_given_default": loss_given_default,
    }

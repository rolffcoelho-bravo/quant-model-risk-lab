"""Independent FX-option challenger and numerical Greek controls."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Callable


@dataclass(frozen=True)
class NumericalGreeks:
    delta: float
    gamma: float
    vega: float


def normal_cdf(value: float) -> float:
    return 0.5 * (
        1.0
        + math.erf(
            float(value) / math.sqrt(2.0)
        )
    )


def black76_fx_price(
    option_type: str,
    spot_rate: float,
    strike_rate: float,
    domestic_rate: float,
    foreign_rate: float,
    volatility: float,
    maturity_years: float,
    notional_foreign: float,
) -> float:
    """Price an FX option through the forward-form Black-76 identity."""
    option = option_type.lower().strip()

    if option not in {"call", "put"}:
        raise ValueError(
            "option_type must be call or put."
        )

    values = {
        "spot_rate": spot_rate,
        "strike_rate": strike_rate,
        "volatility": volatility,
        "maturity_years": maturity_years,
        "notional_foreign": notional_foreign,
    }

    for name, value in values.items():
        if float(value) <= 0.0:
            raise ValueError(
                f"{name} must be positive."
            )

    maturity = float(maturity_years)
    sigma = float(volatility)

    forward = float(spot_rate) * math.exp(
        (
            float(domestic_rate)
            - float(foreign_rate)
        )
        * maturity
    )

    discount = math.exp(
        -float(domestic_rate) * maturity
    )

    sigma_sqrt_t = sigma * math.sqrt(
        maturity
    )

    d1 = (
        math.log(
            forward / float(strike_rate)
        )
        + 0.5 * sigma * sigma * maturity
    ) / sigma_sqrt_t

    d2 = d1 - sigma_sqrt_t

    if option == "call":
        unit_price = discount * (
            forward * normal_cdf(d1)
            - float(strike_rate) * normal_cdf(d2)
        )
    else:
        unit_price = discount * (
            float(strike_rate) * normal_cdf(-d2)
            - forward * normal_cdf(-d1)
        )

    return unit_price * float(
        notional_foreign
    )


def finite_difference_greeks(
    pricing_function: Callable[..., float],
    *,
    option_type: str,
    spot_rate: float,
    strike_rate: float,
    domestic_rate: float,
    foreign_rate: float,
    volatility: float,
    maturity_years: float,
    notional_foreign: float,
    spot_bump_relative: float = 1.0e-4,
    volatility_bump_absolute: float = 1.0e-5,
) -> NumericalGreeks:
    """Calculate independent central-difference Greeks."""
    spot_bump = max(
        abs(float(spot_rate))
        * float(spot_bump_relative),
        1.0e-7,
    )

    volatility_bump = max(
        float(volatility_bump_absolute),
        1.0e-7,
    )

    common = {
        "option_type": option_type,
        "strike_rate": strike_rate,
        "domestic_rate": domestic_rate,
        "foreign_rate": foreign_rate,
        "maturity_years": maturity_years,
        "notional_foreign": notional_foreign,
    }

    base = pricing_function(
        spot_rate=spot_rate,
        volatility=volatility,
        **common,
    )

    spot_up = pricing_function(
        spot_rate=spot_rate + spot_bump,
        volatility=volatility,
        **common,
    )

    spot_down = pricing_function(
        spot_rate=spot_rate - spot_bump,
        volatility=volatility,
        **common,
    )

    vol_up = pricing_function(
        spot_rate=spot_rate,
        volatility=volatility + volatility_bump,
        **common,
    )

    vol_down = pricing_function(
        spot_rate=spot_rate,
        volatility=volatility - volatility_bump,
        **common,
    )

    delta = (
        spot_up - spot_down
    ) / (
        2.0 * spot_bump
    )

    gamma = (
        spot_up
        - 2.0 * base
        + spot_down
    ) / (
        spot_bump * spot_bump
    )

    vega = (
        vol_up - vol_down
    ) / (
        2.0 * volatility_bump
    )

    return NumericalGreeks(
        delta=delta,
        gamma=gamma,
        vega=vega,
    )


def relative_error(
    observed: float,
    benchmark: float,
) -> float:
    scale = max(
        abs(float(benchmark)),
        1.0e-12,
    )

    return abs(
        float(observed)
        - float(benchmark)
    ) / scale
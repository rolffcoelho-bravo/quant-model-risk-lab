from __future__ import annotations

from dataclasses import dataclass
import math

import pandas as pd


@dataclass(frozen=True)
class FXOptionValuation:
    option_type: str
    spot_rate: float
    strike_rate: float
    domestic_rate: float
    foreign_rate: float
    volatility: float
    maturity_years: float
    notional_foreign: float
    premium_domestic: float
    unit_premium_domestic: float
    delta: float
    gamma: float
    vega: float
    rho_domestic: float
    rho_foreign: float
    intrinsic_value: float
    time_value: float
    d1: float
    d2: float


def validate_positive(value: float, name: str) -> None:
    if float(value) <= 0.0:
        raise ValueError(f"{name} must be positive.")


def validate_option_type(option_type: str) -> str:
    option = option_type.lower().strip()
    if option not in {"call", "put"}:
        raise ValueError("option_type must be 'call' or 'put'.")
    return option


def normal_cdf(value: float) -> float:
    return 0.5 * (1.0 + math.erf(float(value) / math.sqrt(2.0)))


def normal_pdf(value: float) -> float:
    return math.exp(-0.5 * float(value) ** 2) / math.sqrt(2.0 * math.pi)


def discounted_spot(spot_rate: float, foreign_rate: float, maturity_years: float) -> float:
    return float(spot_rate) * math.exp(-float(foreign_rate) * float(maturity_years))


def discounted_strike(strike_rate: float, domestic_rate: float, maturity_years: float) -> float:
    return float(strike_rate) * math.exp(-float(domestic_rate) * float(maturity_years))


def forward_rate(spot_rate: float, domestic_rate: float, foreign_rate: float, maturity_years: float) -> float:
    validate_positive(spot_rate, "spot_rate")
    validate_positive(maturity_years, "maturity_years")
    return float(spot_rate) * math.exp((float(domestic_rate) - float(foreign_rate)) * float(maturity_years))


def d1_d2(
    spot_rate: float,
    strike_rate: float,
    domestic_rate: float,
    foreign_rate: float,
    volatility: float,
    maturity_years: float,
) -> tuple[float, float]:
    validate_positive(spot_rate, "spot_rate")
    validate_positive(strike_rate, "strike_rate")
    validate_positive(volatility, "volatility")
    validate_positive(maturity_years, "maturity_years")

    sigma_sqrt_t = float(volatility) * math.sqrt(float(maturity_years))
    d1 = (
        math.log(float(spot_rate) / float(strike_rate))
        + (float(domestic_rate) - float(foreign_rate) + 0.5 * float(volatility) ** 2) * float(maturity_years)
    ) / sigma_sqrt_t
    d2 = d1 - sigma_sqrt_t
    return d1, d2


def garman_kohlhagen_price(
    option_type: str,
    spot_rate: float,
    strike_rate: float,
    domestic_rate: float,
    foreign_rate: float,
    volatility: float,
    maturity_years: float,
    notional_foreign: float,
) -> FXOptionValuation:
    option = validate_option_type(option_type)
    validate_positive(notional_foreign, "notional_foreign")

    d1, d2 = d1_d2(
        spot_rate=spot_rate,
        strike_rate=strike_rate,
        domestic_rate=domestic_rate,
        foreign_rate=foreign_rate,
        volatility=volatility,
        maturity_years=maturity_years,
    )

    s_disc = discounted_spot(spot_rate, foreign_rate, maturity_years)
    k_disc = discounted_strike(strike_rate, domestic_rate, maturity_years)

    if option == "call":
        unit_price = s_disc * normal_cdf(d1) - k_disc * normal_cdf(d2)
        unit_delta = math.exp(-foreign_rate * maturity_years) * normal_cdf(d1)
        intrinsic = max(float(spot_rate) - float(strike_rate), 0.0)
        rho_domestic = float(strike_rate) * float(maturity_years) * math.exp(-domestic_rate * maturity_years) * normal_cdf(d2)
        rho_foreign = -float(spot_rate) * float(maturity_years) * math.exp(-foreign_rate * maturity_years) * normal_cdf(d1)
    else:
        unit_price = k_disc * normal_cdf(-d2) - s_disc * normal_cdf(-d1)
        unit_delta = math.exp(-foreign_rate * maturity_years) * (normal_cdf(d1) - 1.0)
        intrinsic = max(float(strike_rate) - float(spot_rate), 0.0)
        rho_domestic = -float(strike_rate) * float(maturity_years) * math.exp(-domestic_rate * maturity_years) * normal_cdf(-d2)
        rho_foreign = float(spot_rate) * float(maturity_years) * math.exp(-foreign_rate * maturity_years) * normal_cdf(-d1)

    unit_gamma = math.exp(-foreign_rate * maturity_years) * normal_pdf(d1) / (
        float(spot_rate) * float(volatility) * math.sqrt(float(maturity_years))
    )
    unit_vega = float(spot_rate) * math.exp(-foreign_rate * maturity_years) * normal_pdf(d1) * math.sqrt(float(maturity_years))

    premium = unit_price * float(notional_foreign)
    intrinsic_value = intrinsic * math.exp(-domestic_rate * maturity_years) * float(notional_foreign)
    time_value = premium - intrinsic_value

    return FXOptionValuation(
        option_type=option,
        spot_rate=float(spot_rate),
        strike_rate=float(strike_rate),
        domestic_rate=float(domestic_rate),
        foreign_rate=float(foreign_rate),
        volatility=float(volatility),
        maturity_years=float(maturity_years),
        notional_foreign=float(notional_foreign),
        premium_domestic=premium,
        unit_premium_domestic=unit_price,
        delta=unit_delta * float(notional_foreign),
        gamma=unit_gamma * float(notional_foreign),
        vega=unit_vega * float(notional_foreign),
        rho_domestic=rho_domestic * float(notional_foreign),
        rho_foreign=rho_foreign * float(notional_foreign),
        intrinsic_value=intrinsic_value,
        time_value=time_value,
        d1=d1,
        d2=d2,
    )


def put_call_parity_gap(
    call_value: float,
    put_value: float,
    spot_rate: float,
    strike_rate: float,
    domestic_rate: float,
    foreign_rate: float,
    maturity_years: float,
    notional_foreign: float,
) -> float:
    theoretical = float(notional_foreign) * (
        discounted_spot(spot_rate, foreign_rate, maturity_years)
        - discounted_strike(strike_rate, domestic_rate, maturity_years)
    )
    return float(call_value) - float(put_value) - theoretical


def spot_vol_surface(
    spot_rate: float,
    strike_rate: float,
    domestic_rate: float,
    foreign_rate: float,
    base_volatility: float,
    maturity_years: float,
    notional_foreign: float,
    spot_shocks: list[float] | None = None,
    vol_shocks: list[float] | None = None,
) -> pd.DataFrame:
    if spot_shocks is None:
        spot_shocks = [-10.0, -5.0, 0.0, 5.0, 10.0]
    if vol_shocks is None:
        vol_shocks = [-0.05, 0.0, 0.05]

    rows = []
    for spot_shock in spot_shocks:
        shocked_spot = float(spot_rate) * (1.0 + float(spot_shock) / 100.0)

        for vol_shock in vol_shocks:
            shocked_vol = max(float(base_volatility) + float(vol_shock), 0.01)

            call = garman_kohlhagen_price(
                "call",
                shocked_spot,
                strike_rate,
                domestic_rate,
                foreign_rate,
                shocked_vol,
                maturity_years,
                notional_foreign,
            )
            put = garman_kohlhagen_price(
                "put",
                shocked_spot,
                strike_rate,
                domestic_rate,
                foreign_rate,
                shocked_vol,
                maturity_years,
                notional_foreign,
            )

            rows.append(
                {
                    "spot_shock_pct": float(spot_shock),
                    "vol_shock_abs": float(vol_shock),
                    "shocked_spot_rate": shocked_spot,
                    "volatility": shocked_vol,
                    "call_value_domestic": call.premium_domestic,
                    "put_value_domestic": put.premium_domestic,
                    "call_delta": call.delta,
                    "put_delta": put.delta,
                    "call_vega": call.vega,
                    "put_vega": put.vega,
                    "put_call_parity_gap": put_call_parity_gap(
                        call.premium_domestic,
                        put.premium_domestic,
                        shocked_spot,
                        strike_rate,
                        domestic_rate,
                        foreign_rate,
                        maturity_years,
                        notional_foreign,
                    ),
                }
            )

    return pd.DataFrame(rows)

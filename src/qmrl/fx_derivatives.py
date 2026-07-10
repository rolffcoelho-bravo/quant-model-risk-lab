from __future__ import annotations

from dataclasses import dataclass
import math

import pandas as pd


@dataclass(frozen=True)
class FXForwardValuation:
    spot_rate: float
    domestic_rate: float
    foreign_rate: float
    maturity_years: float
    model_forward_rate: float
    contract_forward_rate: float
    notional_foreign: float
    domestic_discount_factor: float
    long_foreign_forward_value: float
    short_foreign_forward_value: float
    fx_delta: float
    carry_basis: float


def validate_positive_number(value: float, name: str) -> None:
    if float(value) <= 0.0:
        raise ValueError(f"{name} must be positive.")


def normalise_rate(value: float) -> float:
    value = float(value)
    if abs(value) > 1.0:
        return value / 100.0
    return value


def domestic_discount_factor(domestic_rate: float, maturity_years: float) -> float:
    validate_positive_number(maturity_years, "maturity_years")
    return math.exp(-float(domestic_rate) * float(maturity_years))


def fx_forward_rate(
    spot_rate: float,
    domestic_rate: float,
    foreign_rate: float,
    maturity_years: float,
) -> float:
    validate_positive_number(spot_rate, "spot_rate")
    validate_positive_number(maturity_years, "maturity_years")
    return float(spot_rate) * math.exp((float(domestic_rate) - float(foreign_rate)) * float(maturity_years))


def price_fx_forward(
    spot_rate: float,
    domestic_rate: float,
    foreign_rate: float,
    maturity_years: float,
    contract_forward_rate: float,
    notional_foreign: float,
) -> FXForwardValuation:
    validate_positive_number(spot_rate, "spot_rate")
    validate_positive_number(maturity_years, "maturity_years")
    validate_positive_number(notional_foreign, "notional_foreign")
    validate_positive_number(contract_forward_rate, "contract_forward_rate")

    model_forward = fx_forward_rate(
        spot_rate=spot_rate,
        domestic_rate=domestic_rate,
        foreign_rate=foreign_rate,
        maturity_years=maturity_years,
    )
    discount = domestic_discount_factor(domestic_rate, maturity_years)

    long_value = float(notional_foreign) * (model_forward - float(contract_forward_rate)) * discount
    short_value = -long_value

    fx_delta = float(notional_foreign) * math.exp((float(domestic_rate) - float(foreign_rate)) * float(maturity_years)) * discount
    carry_basis = model_forward - float(spot_rate)

    return FXForwardValuation(
        spot_rate=float(spot_rate),
        domestic_rate=float(domestic_rate),
        foreign_rate=float(foreign_rate),
        maturity_years=float(maturity_years),
        model_forward_rate=model_forward,
        contract_forward_rate=float(contract_forward_rate),
        notional_foreign=float(notional_foreign),
        domestic_discount_factor=discount,
        long_foreign_forward_value=long_value,
        short_foreign_forward_value=short_value,
        fx_delta=fx_delta,
        carry_basis=carry_basis,
    )


def spot_shock_table(
    spot_rate: float,
    domestic_rate: float,
    foreign_rate: float,
    maturity_years: float,
    contract_forward_rate: float,
    notional_foreign: float,
    shock_percents: list[float] | None = None,
) -> pd.DataFrame:
    if shock_percents is None:
        shock_percents = [-10.0, -5.0, 0.0, 5.0, 10.0]

    base = price_fx_forward(
        spot_rate=spot_rate,
        domestic_rate=domestic_rate,
        foreign_rate=foreign_rate,
        maturity_years=maturity_years,
        contract_forward_rate=contract_forward_rate,
        notional_foreign=notional_foreign,
    )

    rows = []
    for shock_pct in shock_percents:
        shocked_spot = float(spot_rate) * (1.0 + float(shock_pct) / 100.0)
        valuation = price_fx_forward(
            spot_rate=shocked_spot,
            domestic_rate=domestic_rate,
            foreign_rate=foreign_rate,
            maturity_years=maturity_years,
            contract_forward_rate=contract_forward_rate,
            notional_foreign=notional_foreign,
        )
        rows.append(
            {
                "spot_shock_pct": float(shock_pct),
                "shocked_spot_rate": shocked_spot,
                "model_forward_rate": valuation.model_forward_rate,
                "long_foreign_forward_value": valuation.long_foreign_forward_value,
                "short_foreign_forward_value": valuation.short_foreign_forward_value,
                "long_foreign_forward_pnl": valuation.long_foreign_forward_value - base.long_foreign_forward_value,
                "fx_delta": valuation.fx_delta,
            }
        )

    return pd.DataFrame(rows)

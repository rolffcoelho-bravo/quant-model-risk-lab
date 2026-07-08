"""Black-Scholes option-pricing utilities for model validation examples."""

from __future__ import annotations

from dataclasses import dataclass
from math import erf, exp, log, pi, sqrt


@dataclass(frozen=True)
class OptionInputs:
    spot: float
    strike: float
    rate: float
    volatility: float
    maturity: float
    option_type: str = "call"


def _norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + erf(x / sqrt(2.0)))


def _norm_pdf(x: float) -> float:
    return exp(-0.5 * x * x) / sqrt(2.0 * pi)


def validate_inputs(inputs: OptionInputs) -> None:
    if inputs.spot <= 0:
        raise ValueError("Spot must be positive.")
    if inputs.strike <= 0:
        raise ValueError("Strike must be positive.")
    if inputs.volatility <= 0:
        raise ValueError("Volatility must be positive.")
    if inputs.maturity <= 0:
        raise ValueError("Maturity must be positive.")
    if inputs.option_type not in {"call", "put"}:
        raise ValueError("option_type must be 'call' or 'put'.")


def d1_d2(inputs: OptionInputs) -> tuple[float, float]:
    validate_inputs(inputs)
    d1 = (
        log(inputs.spot / inputs.strike)
        + (inputs.rate + 0.5 * inputs.volatility**2) * inputs.maturity
    ) / (inputs.volatility * sqrt(inputs.maturity))
    d2 = d1 - inputs.volatility * sqrt(inputs.maturity)
    return d1, d2


def black_scholes_price(inputs: OptionInputs) -> float:
    d1, d2 = d1_d2(inputs)

    if inputs.option_type == "call":
        return inputs.spot * _norm_cdf(d1) - inputs.strike * exp(-inputs.rate * inputs.maturity) * _norm_cdf(d2)

    return inputs.strike * exp(-inputs.rate * inputs.maturity) * _norm_cdf(-d2) - inputs.spot * _norm_cdf(-d1)


def delta(inputs: OptionInputs) -> float:
    d1, _ = d1_d2(inputs)
    if inputs.option_type == "call":
        return _norm_cdf(d1)
    return _norm_cdf(d1) - 1.0


def vega(inputs: OptionInputs) -> float:
    d1, _ = d1_d2(inputs)
    return inputs.spot * _norm_pdf(d1) * sqrt(inputs.maturity)

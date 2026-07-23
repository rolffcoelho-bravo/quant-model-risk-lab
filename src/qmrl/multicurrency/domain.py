"""Domain objects for v1.4 Gate 2 multi-currency exposure and collateral."""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Mapping


def _currency(code: str) -> str:
    normalized = code.strip().upper()
    if len(normalized) != 3 or not normalized.isalpha():
        raise ValueError(f"Invalid ISO-style currency code: {code!r}.")
    return normalized


def _times(values: tuple[float, ...]) -> tuple[float, ...]:
    if not values:
        raise ValueError("A non-empty time grid is required.")
    result = tuple(float(value) for value in values)
    if result[0] < 0.0:
        raise ValueError("Time grid cannot start before zero.")
    if any(not math.isfinite(value) for value in result):
        raise ValueError("Time grid must contain finite values.")
    if any(right <= left for left, right in zip(result, result[1:])):
        raise ValueError("Time grid must be strictly increasing.")
    return result


def _matrix(
    values: tuple[tuple[float, ...], ...],
    width: int,
    *,
    positive: bool = False,
) -> tuple[tuple[float, ...], ...]:
    if not values:
        raise ValueError("At least one scenario path is required.")
    result: list[tuple[float, ...]] = []
    for row in values:
        converted = tuple(float(value) for value in row)
        if len(converted) != width:
            raise ValueError("Every scenario path must match the time grid.")
        if any(not math.isfinite(value) for value in converted):
            raise ValueError("Scenario values must be finite.")
        if positive and any(value <= 0.0 for value in converted):
            raise ValueError("FX rates must be strictly positive.")
        result.append(converted)
    return tuple(result)


@dataclass(frozen=True)
class PathwiseSeries:
    currency: str
    times: tuple[float, ...]
    values: tuple[tuple[float, ...], ...]

    def __post_init__(self) -> None:
        times = _times(self.times)
        object.__setattr__(self, "currency", _currency(self.currency))
        object.__setattr__(self, "times", times)
        object.__setattr__(
            self,
            "values",
            _matrix(self.values, len(times)),
        )

    @property
    def path_count(self) -> int:
        return len(self.values)


@dataclass(frozen=True)
class FXQuote:
    source_currency: str
    target_currency: str
    times: tuple[float, ...]
    values: tuple[tuple[float, ...], ...]

    def __post_init__(self) -> None:
        source = _currency(self.source_currency)
        target = _currency(self.target_currency)
        if source == target:
            raise ValueError("An FX quote requires two distinct currencies.")
        times = _times(self.times)
        object.__setattr__(self, "source_currency", source)
        object.__setattr__(self, "target_currency", target)
        object.__setattr__(self, "times", times)
        object.__setattr__(
            self,
            "values",
            _matrix(self.values, len(times), positive=True),
        )

    @property
    def path_count(self) -> int:
        return len(self.values)


@dataclass(frozen=True)
class CollateralProfile:
    collateral_set_id: str
    currency: str
    times: tuple[float, ...]
    balances: tuple[tuple[float, ...], ...]
    remuneration_rates: tuple[float, ...] | None = None

    def __post_init__(self) -> None:
        if not self.collateral_set_id.strip():
            raise ValueError("collateral_set_id cannot be empty.")
        times = _times(self.times)
        rates = self.remuneration_rates
        if rates is not None:
            rates = tuple(float(value) for value in rates)
            if len(rates) != len(times):
                raise ValueError(
                    "Collateral remuneration rates must match the time grid."
                )
            if any(not math.isfinite(value) for value in rates):
                raise ValueError("Collateral remuneration rates must be finite.")
        object.__setattr__(self, "currency", _currency(self.currency))
        object.__setattr__(self, "times", times)
        object.__setattr__(
            self,
            "balances",
            _matrix(self.balances, len(times)),
        )
        object.__setattr__(self, "remuneration_rates", rates)

    @property
    def path_count(self) -> int:
        return len(self.balances)


@dataclass(frozen=True)
class MultiCurrencyPolicy:
    reporting_currency: str
    triangulation_currency: str | None = None
    fx_extrapolation: str = "forbidden"
    discount_extrapolation: str = "flat"
    collateral_sign: str = "held_positive"
    conversion_order: str = "trade_then_netting"

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "reporting_currency",
            _currency(self.reporting_currency),
        )
        if self.triangulation_currency is not None:
            object.__setattr__(
                self,
                "triangulation_currency",
                _currency(self.triangulation_currency),
            )
        if self.fx_extrapolation not in {"forbidden"}:
            raise ValueError("Only forbidden FX extrapolation is approved.")
        if self.discount_extrapolation not in {"flat", "forbidden"}:
            raise ValueError("Unsupported discount extrapolation policy.")
        if self.collateral_sign != "held_positive":
            raise ValueError("Only held-positive collateral convention is approved.")
        if self.conversion_order != "trade_then_netting":
            raise ValueError("Currency conversion must occur before netting.")


@dataclass(frozen=True)
class MultiCurrencyExposureResult:
    netting_set_id: str
    reporting_currency: str
    times: tuple[float, ...]
    net_values: tuple[tuple[float, ...], ...]
    collateral_values: tuple[tuple[float, ...], ...]
    positive_exposure: tuple[tuple[float, ...], ...]
    negative_exposure: tuple[tuple[float, ...], ...]
    expected_positive_exposure: tuple[float, ...]
    expected_negative_exposure: tuple[float, ...]
    discounted_expected_positive_exposure: tuple[float, ...]
    discounted_expected_negative_exposure: tuple[float, ...]
    currency_contributions: Mapping[str, tuple[float, ...]] = field(
        default_factory=dict
    )
    policy_hash: str = ""

    def __post_init__(self) -> None:
        if not self.netting_set_id.strip():
            raise ValueError("netting_set_id cannot be empty.")
        times = _times(self.times)
        width = len(times)
        net = _matrix(self.net_values, width)
        collateral = _matrix(self.collateral_values, width)
        positive = _matrix(self.positive_exposure, width)
        negative = _matrix(self.negative_exposure, width)
        if not (
            len(net) == len(collateral) == len(positive) == len(negative)
        ):
            raise ValueError("Result matrices must have the same path count.")
        for profile in (
            self.expected_positive_exposure,
            self.expected_negative_exposure,
            self.discounted_expected_positive_exposure,
            self.discounted_expected_negative_exposure,
        ):
            if len(profile) != width:
                raise ValueError("Expected profiles must match the time grid.")
        object.__setattr__(self, "reporting_currency", _currency(self.reporting_currency))
        object.__setattr__(self, "times", times)
        object.__setattr__(self, "net_values", net)
        object.__setattr__(self, "collateral_values", collateral)
        object.__setattr__(self, "positive_exposure", positive)
        object.__setattr__(self, "negative_exposure", negative)

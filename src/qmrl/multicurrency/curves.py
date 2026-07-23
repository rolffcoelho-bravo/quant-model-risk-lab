"""Currency-specific discount, funding, and collateral remuneration curves."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable


@dataclass(frozen=True)
class TermCurve:
    curve_id: str
    currency: str
    kind: str
    times: tuple[float, ...]
    values: tuple[float, ...]
    extrapolation: str = "flat"

    def __post_init__(self) -> None:
        if not self.curve_id.strip():
            raise ValueError("curve_id cannot be empty.")
        currency = self.currency.strip().upper()
        if len(currency) != 3 or not currency.isalpha():
            raise ValueError("Invalid curve currency.")
        if self.kind not in {
            "discount",
            "funding",
            "collateral_remuneration",
        }:
            raise ValueError("Unsupported curve kind.")
        times = tuple(float(value) for value in self.times)
        values = tuple(float(value) for value in self.values)
        if not times or len(times) != len(values):
            raise ValueError("Curve times and values must be non-empty and aligned.")
        if times[0] < 0.0 or any(
            right <= left for left, right in zip(times, times[1:])
        ):
            raise ValueError("Curve times must be strictly increasing.")
        if any(not math.isfinite(value) for value in values):
            raise ValueError("Curve values must be finite.")
        if self.kind == "discount" and any(value <= 0.0 for value in values):
            raise ValueError("Discount factors must be strictly positive.")
        if self.extrapolation not in {"flat", "forbidden"}:
            raise ValueError("Unsupported curve extrapolation policy.")
        object.__setattr__(self, "currency", currency)
        object.__setattr__(self, "times", times)
        object.__setattr__(self, "values", values)

    def value(self, time: float) -> float:
        point = float(time)
        if point < self.times[0]:
            if self.extrapolation == "forbidden":
                raise ValueError("Curve extrapolation below the first point is forbidden.")
            return self.values[0]
        if point > self.times[-1]:
            if self.extrapolation == "forbidden":
                raise ValueError("Curve extrapolation above the final point is forbidden.")
            return self.values[-1]
        for index, right in enumerate(self.times):
            if point == right:
                return self.values[index]
            if point < right:
                left_time = self.times[index - 1]
                right_time = right
                weight = (point - left_time) / (right_time - left_time)
                return self.values[index - 1] + weight * (
                    self.values[index] - self.values[index - 1]
                )
        return self.values[-1]


class CurrencyCurveSet:
    def __init__(self, curves: Iterable[TermCurve]) -> None:
        self._curves: dict[tuple[str, str], TermCurve] = {}
        for curve in curves:
            key = (curve.currency, curve.kind)
            if key in self._curves:
                raise ValueError(f"Duplicate currency curve: {key}.")
            self._curves[key] = curve

    def curve(self, currency: str, kind: str) -> TermCurve:
        key = (currency.upper(), kind)
        try:
            return self._curves[key]
        except KeyError as exc:
            raise KeyError(f"Missing curve for {key}.") from exc

    def discount_factor(self, currency: str, time: float) -> float:
        return self.curve(currency, "discount").value(time)

    def funding_spread(self, currency: str, time: float) -> float:
        return self.curve(currency, "funding").value(time)

    def collateral_rate(self, currency: str, time: float) -> float:
        return self.curve(currency, "collateral_remuneration").value(time)

    def currencies(self) -> tuple[str, ...]:
        return tuple(sorted({currency for currency, _ in self._curves}))

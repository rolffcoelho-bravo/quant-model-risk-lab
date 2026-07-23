"""Governed FX scenario conversion and triangulation controls."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable

from .domain import FXQuote, PathwiseSeries


@dataclass(frozen=True)
class FXTriangulationReport:
    source_currency: str
    target_currency: str
    pivot_currency: str
    maximum_absolute_error: float
    tolerance: float
    passed: bool


class FXScenarioMarket:
    """Pathwise FX market using target units per one source unit."""

    def __init__(
        self,
        quotes: Iterable[FXQuote] = (),
        *,
        triangulation_currency: str | None = None,
    ) -> None:
        self._quotes: dict[tuple[str, str], FXQuote] = {}
        self.triangulation_currency = (
            triangulation_currency.upper()
            if triangulation_currency is not None
            else None
        )
        for quote in quotes:
            key = (quote.source_currency, quote.target_currency)
            if key in self._quotes:
                raise ValueError(f"Duplicate FX quote: {key}.")
            self._quotes[key] = quote
        grids = {
            (quote.times, quote.path_count)
            for quote in self._quotes.values()
        }
        if len(grids) > 1:
            raise ValueError("All FX quotes must share time and path dimensions.")

    @property
    def quote_count(self) -> int:
        return len(self._quotes)

    def _direct_rate(
        self,
        source: str,
        target: str,
        path_index: int,
        time_index: int,
    ) -> float | None:
        direct = self._quotes.get((source, target))
        if direct is not None:
            return direct.values[path_index][time_index]
        inverse = self._quotes.get((target, source))
        if inverse is not None:
            return 1.0 / inverse.values[path_index][time_index]
        return None

    def rate(
        self,
        source_currency: str,
        target_currency: str,
        path_index: int,
        time_index: int,
        *,
        pivot_currency: str | None = None,
    ) -> float:
        source = source_currency.upper()
        target = target_currency.upper()
        if source == target:
            return 1.0

        direct = self._direct_rate(source, target, path_index, time_index)
        if direct is not None:
            return direct

        pivot = (
            pivot_currency.upper()
            if pivot_currency is not None
            else self.triangulation_currency
        )
        if pivot is None or pivot in {source, target}:
            raise KeyError(
                f"No governed FX conversion path for {source}->{target}."
            )
        first = self._direct_rate(source, pivot, path_index, time_index)
        second = self._direct_rate(pivot, target, path_index, time_index)
        if first is None or second is None:
            raise KeyError(
                f"No governed triangular FX path for {source}->{target} via {pivot}."
            )
        return first * second

    def convert_series(
        self,
        series: PathwiseSeries,
        target_currency: str,
        *,
        pivot_currency: str | None = None,
    ) -> PathwiseSeries:
        target = target_currency.upper()
        converted = tuple(
            tuple(
                value
                * self.rate(
                    series.currency,
                    target,
                    path_index,
                    time_index,
                    pivot_currency=pivot_currency,
                )
                for time_index, value in enumerate(path)
            )
            for path_index, path in enumerate(series.values)
        )
        return PathwiseSeries(
            currency=target,
            times=series.times,
            values=converted,
        )

    def triangulation_report(
        self,
        source_currency: str,
        target_currency: str,
        pivot_currency: str,
        *,
        tolerance: float = 1.0e-10,
    ) -> FXTriangulationReport:
        source = source_currency.upper()
        target = target_currency.upper()
        pivot = pivot_currency.upper()
        direct = self._quotes.get((source, target))
        invert_direct = False
        if direct is None:
            direct = self._quotes.get((target, source))
            invert_direct = direct is not None
        if direct is None:
            raise KeyError("A direct quote is required for triangulation challenge.")

        errors: list[float] = []
        for path_index in range(direct.path_count):
            for time_index in range(len(direct.times)):
                observed = direct.values[path_index][time_index]
                if invert_direct:
                    observed = 1.0 / observed
                first = self._direct_rate(source, pivot, path_index, time_index)
                second = self._direct_rate(pivot, target, path_index, time_index)
                if first is None or second is None:
                    raise KeyError("Triangular legs are incomplete.")
                errors.append(abs(observed - first * second))

        maximum = max(errors, default=0.0)
        return FXTriangulationReport(
            source_currency=source,
            target_currency=target,
            pivot_currency=pivot,
            maximum_absolute_error=maximum,
            tolerance=tolerance,
            passed=maximum <= tolerance,
        )

    def currencies(self) -> tuple[str, ...]:
        values = {
            currency
            for pair in self._quotes
            for currency in pair
        }
        return tuple(sorted(values))

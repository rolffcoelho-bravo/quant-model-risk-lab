"""Currency attribution, switch impacts, and reconciliation diagnostics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from .domain import MultiCurrencyExposureResult


@dataclass(frozen=True)
class CurrencyAttribution:
    netting_set_id: str
    times: tuple[float, ...]
    contributions: Mapping[str, tuple[float, ...]]
    expected_net_value: tuple[float, ...]
    residual: tuple[float, ...]
    maximum_absolute_residual: float
    tolerance: float
    reconciled: bool


@dataclass(frozen=True)
class CollateralSwitchImpact:
    netting_set_id: str
    epe_change: tuple[float, ...]
    ene_change: tuple[float, ...]
    maximum_absolute_change: float


def build_currency_attribution(
    result: MultiCurrencyExposureResult,
    *,
    tolerance: float = 1.0e-10,
) -> CurrencyAttribution:
    path_count = len(result.net_values)
    expected_net = tuple(
        sum(path[index] for path in result.net_values) / path_count
        for index in range(len(result.times))
    )
    attributed = tuple(
        sum(
            profile[index]
            for profile in result.currency_contributions.values()
        )
        for index in range(len(result.times))
    )
    residual = tuple(
        observed - explained
        for observed, explained in zip(
            expected_net,
            attributed,
        )
    )
    maximum = max(
        (abs(value) for value in residual),
        default=0.0,
    )
    return CurrencyAttribution(
        netting_set_id=result.netting_set_id,
        times=result.times,
        contributions=result.currency_contributions,
        expected_net_value=expected_net,
        residual=residual,
        maximum_absolute_residual=maximum,
        tolerance=tolerance,
        reconciled=maximum <= tolerance,
    )


def collateral_switch_impact(
    base: MultiCurrencyExposureResult,
    switched: MultiCurrencyExposureResult,
) -> CollateralSwitchImpact:
    if (
        base.netting_set_id != switched.netting_set_id
        or base.times != switched.times
    ):
        raise ValueError("Collateral switch results are not aligned.")
    epe_change = tuple(
        right - left
        for left, right in zip(
            base.expected_positive_exposure,
            switched.expected_positive_exposure,
        )
    )
    ene_change = tuple(
        right - left
        for left, right in zip(
            base.expected_negative_exposure,
            switched.expected_negative_exposure,
        )
    )
    maximum = max(
        [
            abs(value)
            for value in (*epe_change, *ene_change)
        ],
        default=0.0,
    )
    return CollateralSwitchImpact(
        netting_set_id=base.netting_set_id,
        epe_change=epe_change,
        ene_change=ene_change,
        maximum_absolute_change=maximum,
    )


def aggregate_expected_profiles(
    results: Sequence[MultiCurrencyExposureResult],
) -> dict[str, tuple[float, ...]]:
    if not results:
        return {
            "expected_positive_exposure": (),
            "expected_negative_exposure": (),
        }
    times = results[0].times
    if any(item.times != times for item in results):
        raise ValueError("Portfolio exposure results must share a time grid.")
    return {
        "expected_positive_exposure": tuple(
            sum(item.expected_positive_exposure[index] for item in results)
            for index in range(len(times))
        ),
        "expected_negative_exposure": tuple(
            sum(item.expected_negative_exposure[index] for item in results)
            for index in range(len(times))
        ),
    }

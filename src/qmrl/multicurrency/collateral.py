"""Collateral remuneration, conversion, and currency-switch controls."""

from __future__ import annotations

import math

from .domain import CollateralProfile, PathwiseSeries
from .fx import FXScenarioMarket


def accrue_collateral(
    initial_balance: float,
    times: tuple[float, ...],
    annual_rates: tuple[float, ...],
) -> tuple[float, ...]:
    if len(times) != len(annual_rates) or not times:
        raise ValueError("Collateral times and rates must be aligned.")
    if any(right <= left for left, right in zip(times, times[1:])):
        raise ValueError("Collateral time grid must be strictly increasing.")
    result = [float(initial_balance)]
    for index in range(1, len(times)):
        delta = times[index] - times[index - 1]
        result.append(
            result[-1] * math.exp(annual_rates[index - 1] * delta)
        )
    return tuple(result)


def remunerate_collateral_profile(
    profile: CollateralProfile,
) -> CollateralProfile:
    if profile.remuneration_rates is None:
        return profile
    balances = tuple(
        accrue_collateral(
            path[0],
            profile.times,
            profile.remuneration_rates,
        )
        for path in profile.balances
    )
    return CollateralProfile(
        collateral_set_id=profile.collateral_set_id,
        currency=profile.currency,
        times=profile.times,
        balances=balances,
        remuneration_rates=profile.remuneration_rates,
    )


def collateral_as_series(
    profile: CollateralProfile,
) -> PathwiseSeries:
    return PathwiseSeries(
        currency=profile.currency,
        times=profile.times,
        values=profile.balances,
    )


def convert_collateral_profile(
    profile: CollateralProfile,
    target_currency: str,
    market: FXScenarioMarket,
    *,
    pivot_currency: str | None = None,
) -> CollateralProfile:
    converted = market.convert_series(
        collateral_as_series(profile),
        target_currency,
        pivot_currency=pivot_currency,
    )
    return CollateralProfile(
        collateral_set_id=profile.collateral_set_id,
        currency=converted.currency,
        times=converted.times,
        balances=converted.values,
        remuneration_rates=profile.remuneration_rates,
    )


def switch_collateral_currency(
    profile: CollateralProfile,
    new_currency: str,
    market: FXScenarioMarket,
    *,
    pivot_currency: str | None = None,
) -> CollateralProfile:
    """Convert balances so the scenario value is preserved at every point."""

    return convert_collateral_profile(
        profile,
        new_currency,
        market,
        pivot_currency=pivot_currency,
    )

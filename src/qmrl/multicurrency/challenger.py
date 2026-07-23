"""Independent loop challenger for Gate 2 multi-currency exposure."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from qmrl.portfolio import PortfolioSnapshot

from .curves import CurrencyCurveSet
from .domain import (
    CollateralProfile,
    MultiCurrencyExposureResult,
    MultiCurrencyPolicy,
    PathwiseSeries,
)
from .fx import FXScenarioMarket


@dataclass(frozen=True)
class MultiCurrencyChallengeReport:
    compared_netting_sets: int
    component_maximum_errors: Mapping[str, float]
    maximum_absolute_error: float
    tolerance: float
    passed: bool


def independent_multicurrency_profiles(
    snapshot: PortfolioSnapshot,
    trade_values: Mapping[str, PathwiseSeries],
    collateral_profiles: Mapping[str, CollateralProfile],
    market: FXScenarioMarket,
    curves: CurrencyCurveSet,
    policy: MultiCurrencyPolicy,
) -> dict[str, dict[str, tuple[float, ...]]]:
    if not trade_values:
        raise ValueError("Independent challenger requires trade values.")
    first = next(iter(trade_values.values()))
    times = first.times
    path_count = first.path_count
    result: dict[str, dict[str, tuple[float, ...]]] = {}

    for netting_set in snapshot.netting_sets:
        positive_sums = [0.0] * len(times)
        negative_sums = [0.0] * len(times)

        for path_index in range(path_count):
            for time_index, time in enumerate(times):
                total = 0.0
                for trade in snapshot.trades:
                    if trade.netting_set_id != netting_set.netting_set_id:
                        continue
                    series = trade_values[trade.trade_id]
                    total += (
                        series.values[path_index][time_index]
                        * market.rate(
                            series.currency,
                            policy.reporting_currency,
                            path_index,
                            time_index,
                            pivot_currency=policy.triangulation_currency,
                        )
                    )

                for collateral_set in snapshot.collateral_sets:
                    if collateral_set.netting_set_id != netting_set.netting_set_id:
                        continue
                    profile = collateral_profiles.get(
                        collateral_set.collateral_set_id
                    )
                    if profile is None:
                        continue
                    total -= (
                        profile.balances[path_index][time_index]
                        * market.rate(
                            profile.currency,
                            policy.reporting_currency,
                            path_index,
                            time_index,
                            pivot_currency=policy.triangulation_currency,
                        )
                    )

                positive_sums[time_index] += max(total, 0.0)
                negative_sums[time_index] += max(-total, 0.0)

        epe = tuple(value / path_count for value in positive_sums)
        ene = tuple(value / path_count for value in negative_sums)
        discounts = tuple(
            curves.discount_factor(policy.reporting_currency, time)
            for time in times
        )
        result[netting_set.netting_set_id] = {
            "expected_positive_exposure": epe,
            "expected_negative_exposure": ene,
            "discounted_expected_positive_exposure": tuple(
                value * discount
                for value, discount in zip(epe, discounts)
            ),
            "discounted_expected_negative_exposure": tuple(
                value * discount
                for value, discount in zip(ene, discounts)
            ),
        }

    return result


def challenge_multicurrency_exposure(
    snapshot: PortfolioSnapshot,
    trade_values: Mapping[str, PathwiseSeries],
    collateral_profiles: Mapping[str, CollateralProfile],
    market: FXScenarioMarket,
    curves: CurrencyCurveSet,
    policy: MultiCurrencyPolicy,
    engine_results: tuple[MultiCurrencyExposureResult, ...],
    *,
    tolerance: float = 1.0e-10,
) -> MultiCurrencyChallengeReport:
    independent = independent_multicurrency_profiles(
        snapshot,
        trade_values,
        collateral_profiles,
        market,
        curves,
        policy,
    )
    fields = (
        "expected_positive_exposure",
        "expected_negative_exposure",
        "discounted_expected_positive_exposure",
        "discounted_expected_negative_exposure",
    )
    errors = {field: 0.0 for field in fields}
    for result in engine_results:
        expected = independent[result.netting_set_id]
        for field in fields:
            observed_profile = getattr(result, field)
            expected_profile = expected[field]
            errors[field] = max(
                errors[field],
                max(
                    (
                        abs(observed - target)
                        for observed, target in zip(
                            observed_profile,
                            expected_profile,
                        )
                    ),
                    default=0.0,
                ),
            )
    maximum = max(errors.values(), default=0.0)
    return MultiCurrencyChallengeReport(
        compared_netting_sets=len(engine_results),
        component_maximum_errors=errors,
        maximum_absolute_error=maximum,
        tolerance=tolerance,
        passed=maximum <= tolerance,
    )

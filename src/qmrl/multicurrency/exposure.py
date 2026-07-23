"""Multi-currency conversion-before-netting exposure calculation."""

from __future__ import annotations

import hashlib
import json
from typing import Mapping, Sequence

from qmrl.portfolio import PortfolioSnapshot

from .collateral import remunerate_collateral_profile
from .curves import CurrencyCurveSet
from .domain import (
    CollateralProfile,
    MultiCurrencyExposureResult,
    MultiCurrencyPolicy,
    PathwiseSeries,
)
from .fx import FXScenarioMarket


def _policy_hash(policy: MultiCurrencyPolicy) -> str:
    payload = {
        "reporting_currency": policy.reporting_currency,
        "triangulation_currency": policy.triangulation_currency,
        "fx_extrapolation": policy.fx_extrapolation,
        "discount_extrapolation": policy.discount_extrapolation,
        "collateral_sign": policy.collateral_sign,
        "conversion_order": policy.conversion_order,
    }
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _mean_columns(
    matrix: Sequence[Sequence[float]],
) -> tuple[float, ...]:
    if not matrix:
        return ()
    path_count = len(matrix)
    return tuple(
        sum(path[index] for path in matrix) / path_count
        for index in range(len(matrix[0]))
    )


def _zero_matrix(
    path_count: int,
    width: int,
) -> list[list[float]]:
    return [
        [0.0 for _ in range(width)]
        for _ in range(path_count)
    ]


def _validate_dimensions(
    series: Sequence[PathwiseSeries],
) -> tuple[tuple[float, ...], int]:
    if not series:
        raise ValueError("At least one pathwise trade series is required.")
    times = series[0].times
    path_count = series[0].path_count
    for item in series[1:]:
        if item.times != times or item.path_count != path_count:
            raise ValueError(
                "Trade and collateral scenario dimensions must be aligned."
            )
    return times, path_count


def calculate_multicurrency_exposure(
    snapshot: PortfolioSnapshot,
    trade_values: Mapping[str, PathwiseSeries],
    collateral_profiles: Mapping[str, CollateralProfile],
    fx_market: FXScenarioMarket,
    curve_set: CurrencyCurveSet,
    policy: MultiCurrencyPolicy,
    *,
    apply_collateral_remuneration: bool = False,
) -> tuple[MultiCurrencyExposureResult, ...]:
    if snapshot.reporting_currency != policy.reporting_currency:
        raise ValueError(
            "Portfolio and policy reporting currencies must agree."
        )

    expected_trade_ids = {trade.trade_id for trade in snapshot.trades}
    if set(trade_values) != expected_trade_ids:
        missing = sorted(expected_trade_ids - set(trade_values))
        extra = sorted(set(trade_values) - expected_trade_ids)
        raise ValueError(
            f"Trade-value mapping is incomplete: missing={missing}, extra={extra}."
        )

    all_series = list(trade_values.values())
    all_series.extend(
        PathwiseSeries(
            currency=profile.currency,
            times=profile.times,
            values=profile.balances,
        )
        for profile in collateral_profiles.values()
    )
    times, path_count = _validate_dimensions(all_series)
    width = len(times)

    trade_by_netting: dict[str, list[object]] = {}
    for trade in snapshot.trades:
        trade_by_netting.setdefault(
            trade.netting_set_id,
            [],
        ).append(trade)

    collateral_sets = {
        item.collateral_set_id: item
        for item in snapshot.collateral_sets
    }

    results: list[MultiCurrencyExposureResult] = []

    for netting_set in snapshot.netting_sets:
        trades = trade_by_netting.get(
            netting_set.netting_set_id,
            [],
        )
        net_values = _zero_matrix(path_count, width)
        collateral_values = _zero_matrix(path_count, width)
        contributions: dict[str, list[float]] = {}

        for trade in trades:
            series = trade_values[trade.trade_id]
            if series.currency != trade.trade_currency:
                raise ValueError(
                    f"Trade {trade.trade_id} value currency does not match its contract."
                )
            converted = fx_market.convert_series(
                series,
                policy.reporting_currency,
                pivot_currency=policy.triangulation_currency,
            )
            contribution = contributions.setdefault(
                series.currency,
                [0.0] * width,
            )
            for path_index, path in enumerate(converted.values):
                for time_index, value in enumerate(path):
                    net_values[path_index][time_index] += value
                    contribution[time_index] += value / path_count

        relevant_collateral_ids = [
            item.collateral_set_id
            for item in snapshot.collateral_sets
            if item.netting_set_id == netting_set.netting_set_id
        ]

        for collateral_id in relevant_collateral_ids:
            if collateral_id not in collateral_profiles:
                continue
            profile = collateral_profiles[collateral_id]
            contract = collateral_sets[collateral_id]
            if profile.currency not in contract.eligible_currencies:
                raise ValueError(
                    f"Collateral currency {profile.currency} is not eligible "
                    f"for {collateral_id}."
                )
            effective = (
                remunerate_collateral_profile(profile)
                if apply_collateral_remuneration
                else profile
            )
            converted = fx_market.convert_series(
                PathwiseSeries(
                    currency=effective.currency,
                    times=effective.times,
                    values=effective.balances,
                ),
                policy.reporting_currency,
                pivot_currency=policy.triangulation_currency,
            )
            contribution = contributions.setdefault(
                effective.currency,
                [0.0] * width,
            )
            for path_index, path in enumerate(converted.values):
                for time_index, value in enumerate(path):
                    collateral_values[path_index][time_index] += value
                    net_values[path_index][time_index] -= value
                    contribution[time_index] -= value / path_count

        positive = tuple(
            tuple(max(value, 0.0) for value in path)
            for path in net_values
        )
        negative = tuple(
            tuple(max(-value, 0.0) for value in path)
            for path in net_values
        )
        expected_positive = _mean_columns(positive)
        expected_negative = _mean_columns(negative)
        discounts = tuple(
            curve_set.discount_factor(
                policy.reporting_currency,
                time,
            )
            for time in times
        )

        results.append(
            MultiCurrencyExposureResult(
                netting_set_id=netting_set.netting_set_id,
                reporting_currency=policy.reporting_currency,
                times=times,
                net_values=tuple(tuple(path) for path in net_values),
                collateral_values=tuple(
                    tuple(path) for path in collateral_values
                ),
                positive_exposure=positive,
                negative_exposure=negative,
                expected_positive_exposure=expected_positive,
                expected_negative_exposure=expected_negative,
                discounted_expected_positive_exposure=tuple(
                    value * discount
                    for value, discount in zip(
                        expected_positive,
                        discounts,
                    )
                ),
                discounted_expected_negative_exposure=tuple(
                    value * discount
                    for value, discount in zip(
                        expected_negative,
                        discounts,
                    )
                ),
                currency_contributions={
                    currency: tuple(values)
                    for currency, values in sorted(contributions.items())
                },
                policy_hash=_policy_hash(policy),
            )
        )

    return tuple(results)

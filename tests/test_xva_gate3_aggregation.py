from __future__ import annotations

from datetime import date

import numpy as np
import pytest

from qmrl.xva import (
    FutureValueCube,
    NettingSet,
    aggregate_pathwise_exposure,
    allocate_future_values,
    build_pathwise_exposure_cube,
    simulate_pathwise_collateral,
)


def _exposure_cube():
    values = np.array(
        [
            [
                [0.0, 0.0],
                [100.0, 20.0],
                [-20.0, 40.0],
            ],
            [
                [0.0, 0.0],
                [50.0, 30.0],
                [-40.0, 10.0],
            ],
        ]
    )

    future = FutureValueCube(
        times=np.array([0.0, 0.5, 1.0]),
        trade_ids=("T1", "T2"),
        values=values,
        portfolio_values=np.sum(values, axis=2),
    )

    netting_sets = (
        NettingSet(
            netting_set_id="NS1",
            counterparty_id="CP1",
            agreement_id="ISDA1",
            settlement_currency="USD",
            trade_ids=("T1",),
        ),
        NettingSet(
            netting_set_id="NS2",
            counterparty_id="CP1",
            agreement_id="ISDA2",
            settlement_currency="USD",
            trade_ids=("T2",),
        ),
    )

    netting = allocate_future_values(
        future,
        netting_sets,
        (
            date(2026, 1, 5),
            date(2026, 7, 5),
            date(2027, 1, 5),
        ),
    )

    collateral = simulate_pathwise_collateral(
        netting,
        {},
    )

    return build_pathwise_exposure_cube(
        netting,
        collateral,
        {},
    )


def test_aggregation_preserves_legal_set_boundaries() -> None:
    aggregation = aggregate_pathwise_exposure(
        _exposure_cube(),
        quantile=0.95,
    )

    assert aggregation.expected_positive_by_netting_set[
        1
    ].tolist() == [75.0, 25.0]

    assert aggregation.portfolio_expected_positive[
        1
    ] == 100.0


def test_counterparty_aggregation_sums_without_cross_netting() -> None:
    aggregation = aggregate_pathwise_exposure(
        _exposure_cube(),
        quantile=0.95,
    )

    assert aggregation.counterparty_ids == ("CP1",)
    assert aggregation.counterparty_expected_positive[
        1,
        0,
    ] == 100.0


def test_pfe_is_computed_on_pathwise_portfolio_exposure() -> None:
    aggregation = aggregate_pathwise_exposure(
        _exposure_cube(),
        quantile=0.50,
    )

    assert aggregation.portfolio_pfe[
        1
    ] == 100.0


def test_invalid_quantile_is_rejected() -> None:
    with pytest.raises(ValueError):
        aggregate_pathwise_exposure(
            _exposure_cube(),
            quantile=1.0,
        )

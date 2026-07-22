from __future__ import annotations

from datetime import date

import numpy as np
import pytest

from qmrl.xva import (
    FutureValueCube,
    NettingSet,
    allocate_future_values,
)


def _future_values() -> FutureValueCube:
    values = np.array(
        [
            [
                [100.0, -90.0, 25.0],
                [80.0, -70.0, 20.0],
            ],
            [
                [60.0, -40.0, -10.0],
                [50.0, -30.0, -5.0],
            ],
        ]
    )

    return FutureValueCube(
        times=np.array([0.0, 1.0]),
        trade_ids=("T1", "T2", "T3"),
        values=values,
        portfolio_values=np.sum(values, axis=2),
    )


def _dates() -> tuple[date, ...]:
    return (
        date(2026, 1, 5),
        date(2027, 1, 5),
    )


def test_trade_values_are_allocated_to_legal_sets() -> None:
    sets = (
        NettingSet(
            netting_set_id="NS1",
            counterparty_id="CP1",
            agreement_id="ISDA1",
            settlement_currency="USD",
            trade_ids=("T1", "T2"),
        ),
        NettingSet(
            netting_set_id="NS2",
            counterparty_id="CP2",
            agreement_id="ISDA2",
            settlement_currency="USD",
            trade_ids=("T3",),
        ),
    )

    cube = allocate_future_values(
        _future_values(),
        sets,
        _dates(),
    )

    assert cube.clean_values.shape == (2, 2, 2)
    assert cube.clean_values[0, 0].tolist() == [
        10.0,
        25.0,
    ]
    assert cube.gross_positive_values[0, 0].tolist() == [
        100.0,
        25.0,
    ]
    assert cube.gross_negative_values[0, 0].tolist() == [
        90.0,
        0.0,
    ]


def test_every_trade_must_be_allocated_once() -> None:
    sets = (
        NettingSet(
            netting_set_id="NS1",
            counterparty_id="CP1",
            agreement_id="ISDA1",
            settlement_currency="USD",
            trade_ids=("T1", "T2"),
        ),
    )

    with pytest.raises(ValueError):
        allocate_future_values(
            _future_values(),
            sets,
            _dates(),
        )


def test_unknown_trade_in_contract_is_rejected() -> None:
    sets = (
        NettingSet(
            netting_set_id="NS1",
            counterparty_id="CP1",
            agreement_id="ISDA1",
            settlement_currency="USD",
            trade_ids=("T1", "T2", "UNKNOWN"),
        ),
    )

    with pytest.raises(ValueError):
        allocate_future_values(
            _future_values(),
            sets,
            _dates(),
        )


def test_duplicate_cross_set_membership_is_rejected() -> None:
    sets = (
        NettingSet(
            netting_set_id="NS1",
            counterparty_id="CP1",
            agreement_id="ISDA1",
            settlement_currency="USD",
            trade_ids=("T1", "T2"),
        ),
        NettingSet(
            netting_set_id="NS2",
            counterparty_id="CP2",
            agreement_id="ISDA2",
            settlement_currency="USD",
            trade_ids=("T2", "T3"),
        ),
    )

    with pytest.raises(ValueError):
        allocate_future_values(
            _future_values(),
            sets,
            _dates(),
        )


def test_netting_cube_arrays_are_immutable() -> None:
    sets = (
        NettingSet(
            netting_set_id="NS1",
            counterparty_id="CP1",
            agreement_id="ISDA1",
            settlement_currency="USD",
            trade_ids=("T1", "T2", "T3"),
        ),
    )

    cube = allocate_future_values(
        _future_values(),
        sets,
        _dates(),
    )

    assert not cube.clean_values.flags.writeable
    assert not cube.netting_eligible.flags.writeable

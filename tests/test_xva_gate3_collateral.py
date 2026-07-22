from __future__ import annotations

from datetime import date

import numpy as np
import pytest

from qmrl.xva import (
    CollateralAgreement,
    FutureValueCube,
    NettingSet,
    allocate_future_values,
    simulate_pathwise_collateral,
)


def _future_values(values: list[float]) -> FutureValueCube:
    array = np.asarray(values, dtype=float).reshape(
        1,
        len(values),
        1,
    )

    return FutureValueCube(
        times=np.linspace(
            0.0,
            1.0,
            len(values),
        ),
        trade_ids=("T1",),
        values=array,
        portfolio_values=array[:, :, 0],
    )


def _netting_set(
    agreement_id: str | None,
) -> NettingSet:
    return NettingSet(
        netting_set_id="NS1",
        counterparty_id="CP1",
        agreement_id="ISDA1",
        settlement_currency="USD",
        trade_ids=("T1",),
        collateral_agreement_id=agreement_id,
    )


def test_no_agreement_produces_zero_collateral() -> None:
    dates = (
        date(2026, 1, 5),
        date(2026, 1, 6),
    )

    netting = allocate_future_values(
        _future_values([10.0, 20.0]),
        (_netting_set(None),),
        dates,
    )

    collateral = simulate_pathwise_collateral(
        netting,
        {},
    )

    assert np.allclose(
        collateral.effective_balances,
        0.0,
    )


def test_perfect_collateralization_runs_by_path() -> None:
    dates = (
        date(2026, 1, 5),
        date(2026, 1, 6),
    )

    agreement = CollateralAgreement(
        agreement_id="CSA1",
        settlement_lag_days=0,
        margin_period_of_risk_days=0,
    )

    netting = allocate_future_values(
        _future_values([10.0, 20.0]),
        (_netting_set("CSA1"),),
        dates,
    )

    collateral = simulate_pathwise_collateral(
        netting,
        {"CSA1": agreement},
    )

    assert collateral.effective_balances[
        0,
        :,
        0,
    ].tolist() == [10.0, 20.0]


def test_settlement_lag_preserves_pending_transfer() -> None:
    dates = (
        date(2026, 1, 5),
        date(2026, 1, 6),
        date(2026, 1, 7),
    )

    agreement = CollateralAgreement(
        agreement_id="CSA1",
        settlement_lag_days=1,
        margin_period_of_risk_days=0,
    )

    netting = allocate_future_values(
        _future_values([0.0, 100.0, 100.0]),
        (_netting_set("CSA1"),),
        dates,
    )

    collateral = simulate_pathwise_collateral(
        netting,
        {"CSA1": agreement},
    )

    assert collateral.effective_balances[
        0,
        :,
        0,
    ].tolist() == [0.0, 0.0, 100.0]

    assert collateral.pending_face_balances[
        0,
        1,
        0,
    ] == pytest.approx(100.0)


def test_missing_agreement_is_fail_closed() -> None:
    dates = (
        date(2026, 1, 5),
        date(2026, 1, 6),
    )

    netting = allocate_future_values(
        _future_values([10.0, 20.0]),
        (_netting_set("MISSING"),),
        dates,
    )

    with pytest.raises(KeyError):
        simulate_pathwise_collateral(
            netting,
            {},
        )


def test_multi_trade_noneligible_set_cannot_be_collateralized() -> None:
    values = np.array(
        [
            [
                [100.0, -90.0],
                [80.0, -70.0],
            ]
        ]
    )

    future = FutureValueCube(
        times=np.array([0.0, 1.0]),
        trade_ids=("T1", "T2"),
        values=values,
        portfolio_values=np.sum(values, axis=2),
    )

    netting_set = NettingSet(
        netting_set_id="NS1",
        counterparty_id="CP1",
        agreement_id="ISDA1",
        settlement_currency="USD",
        trade_ids=("T1", "T2"),
        netting_eligible=False,
        collateral_agreement_id="CSA1",
    )

    netting = allocate_future_values(
        future,
        (netting_set,),
        (
            date(2026, 1, 5),
            date(2027, 1, 5),
        ),
    )

    with pytest.raises(ValueError):
        simulate_pathwise_collateral(
            netting,
            {
                "CSA1": CollateralAgreement(
                    agreement_id="CSA1"
                )
            },
        )

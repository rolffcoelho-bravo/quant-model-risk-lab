from __future__ import annotations

from datetime import date

import numpy as np

from qmrl.xva import (
    CollateralAgreement,
    FutureValueCube,
    NettingSet,
    allocate_future_values,
    build_pathwise_exposure_cube,
    simulate_pathwise_collateral,
)


def _pipeline(
    trade_values: np.ndarray,
    *,
    netting_eligible: bool = True,
    agreement: CollateralAgreement | None = None,
):
    values = np.asarray(
        trade_values,
        dtype=float,
    )

    trade_ids = tuple(
        f"T{index + 1}"
        for index in range(values.shape[2])
    )

    future = FutureValueCube(
        times=np.arange(
            values.shape[1],
            dtype=float,
        ),
        trade_ids=trade_ids,
        values=values,
        portfolio_values=np.sum(values, axis=2),
    )

    netting_set = NettingSet(
        netting_set_id="NS1",
        counterparty_id="CP1",
        agreement_id="ISDA1",
        settlement_currency="USD",
        trade_ids=trade_ids,
        netting_eligible=netting_eligible,
        collateral_agreement_id=(
            agreement.agreement_id
            if agreement is not None
            else None
        ),
    )

    dates = tuple(
        date(2026, 1, 5 + index)
        for index in range(values.shape[1])
    )

    netting = allocate_future_values(
        future,
        (netting_set,),
        dates,
    )

    agreements = (
        {agreement.agreement_id: agreement}
        if agreement is not None
        else {}
    )

    collateral = simulate_pathwise_collateral(
        netting,
        agreements,
    )

    exposure = build_pathwise_exposure_cube(
        netting,
        collateral,
        agreements,
    )

    return netting, collateral, exposure


def test_collateralized_positive_and_negative_exposure() -> None:
    agreement = CollateralAgreement(
        agreement_id="CSA1",
        threshold_received=20.0,
        threshold_posted=10.0,
        settlement_lag_days=0,
        margin_period_of_risk_days=0,
    )

    _, _, exposure = _pipeline(
        np.array(
            [
                [
                    [100.0],
                    [-80.0],
                ]
            ]
        ),
        agreement=agreement,
    )

    assert exposure.positive_exposure[
        0,
        0,
        0,
    ] == 20.0

    assert exposure.negative_exposure[
        0,
        1,
        0,
    ] == 10.0


def test_noneligible_set_preserves_gross_exposure() -> None:
    _, _, exposure = _pipeline(
        np.array(
            [
                [
                    [100.0, -90.0],
                    [80.0, -70.0],
                ]
            ]
        ),
        netting_eligible=False,
    )

    assert exposure.positive_exposure[
        0,
        0,
        0,
    ] == 100.0

    assert exposure.negative_exposure[
        0,
        0,
        0,
    ] == 90.0

    assert exposure.net_values[
        0,
        0,
        0,
    ] == 10.0


def test_mpor_uses_future_clean_value_with_current_collateral() -> None:
    agreement = CollateralAgreement(
        agreement_id="CSA1",
        settlement_lag_days=0,
        margin_period_of_risk_days=1,
    )

    _, _, exposure = _pipeline(
        np.array(
            [
                [
                    [0.0],
                    [50.0],
                    [100.0],
                ]
            ]
        ),
        agreement=agreement,
    )

    assert exposure.mpor_positive_exposure[
        0,
        :,
        0,
    ].tolist() == [50.0, 50.0, 0.0]


def test_mpor_target_indices_are_date_based() -> None:
    agreement = CollateralAgreement(
        agreement_id="CSA1",
        settlement_lag_days=0,
        margin_period_of_risk_days=2,
    )

    _, _, exposure = _pipeline(
        np.array(
            [
                [
                    [0.0],
                    [25.0],
                    [50.0],
                ]
            ]
        ),
        agreement=agreement,
    )

    assert exposure.mpor_target_indices[
        :,
        0,
    ].tolist() == [2, 2, 2]


def test_exposure_cube_is_immutable() -> None:
    _, _, exposure = _pipeline(
        np.array(
            [
                [
                    [10.0],
                    [20.0],
                ]
            ]
        )
    )

    assert not exposure.positive_exposure.flags.writeable
    assert not exposure.mpor_target_indices.flags.writeable

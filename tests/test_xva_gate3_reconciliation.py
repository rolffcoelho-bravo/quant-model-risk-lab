from __future__ import annotations

from datetime import date

import numpy as np

from qmrl.xva import (
    CollateralAgreement,
    FutureValueCube,
    NettingSet,
    aggregate_pathwise_exposure,
    allocate_future_values,
    build_pathwise_exposure_cube,
    exposure_manifest,
    reconcile_pathwise_exposure,
    simulate_pathwise_collateral,
)


def _pipeline():
    values = np.array(
        [
            [
                [0.0, 0.0],
                [100.0, -40.0],
                [80.0, -20.0],
            ],
            [
                [0.0, 0.0],
                [50.0, -10.0],
                [40.0, -5.0],
            ],
        ]
    )

    future = FutureValueCube(
        times=np.array([0.0, 0.5, 1.0]),
        trade_ids=("T1", "T2"),
        values=values,
        portfolio_values=np.sum(values, axis=2),
    )

    sets = (
        NettingSet(
            netting_set_id="NS1",
            counterparty_id="CP1",
            agreement_id="ISDA1",
            settlement_currency="USD",
            trade_ids=("T1", "T2"),
            collateral_agreement_id="CSA1",
        ),
    )

    agreement = CollateralAgreement(
        agreement_id="CSA1",
        threshold_received=10.0,
        threshold_posted=10.0,
        settlement_lag_days=0,
        margin_period_of_risk_days=0,
    )

    dates = (
        date(2026, 1, 5),
        date(2026, 7, 5),
        date(2027, 1, 5),
    )

    netting = allocate_future_values(
        future,
        sets,
        dates,
    )

    collateral = simulate_pathwise_collateral(
        netting,
        {"CSA1": agreement},
    )

    exposure = build_pathwise_exposure_cube(
        netting,
        collateral,
        {"CSA1": agreement},
    )

    aggregation = aggregate_pathwise_exposure(
        exposure,
    )

    return (
        future,
        netting,
        collateral,
        exposure,
        aggregation,
    )


def test_all_reconciliation_controls_pass() -> None:
    future, netting, collateral, exposure, _ = _pipeline()

    result = reconcile_pathwise_exposure(
        future,
        netting,
        collateral,
        exposure,
    )

    assert result.status == "PASS"
    assert result.trade_to_netting_max_abs_error == 0.0
    assert result.challenger_positive_max_abs_error == 0.0


def test_manifest_is_deterministic_and_content_addressed() -> None:
    _, netting, collateral, exposure, aggregation = _pipeline()

    first = exposure_manifest(
        netting,
        collateral,
        exposure,
        aggregation,
    )

    second = exposure_manifest(
        netting,
        collateral,
        exposure,
        aggregation,
    )

    assert first == second
    assert len(first["exposure_sha256"]) == 64


def test_manifest_contains_exposure_dimensions() -> None:
    _, netting, collateral, exposure, aggregation = _pipeline()

    manifest = exposure_manifest(
        netting,
        collateral,
        exposure,
        aggregation,
    )

    assert manifest["gate"] == "XVA_EXPOSURE_GATE_3"
    assert manifest["num_paths"] == 2
    assert manifest["num_netting_sets"] == 1

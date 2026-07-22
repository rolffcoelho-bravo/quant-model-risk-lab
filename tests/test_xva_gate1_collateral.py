from __future__ import annotations

from datetime import date

import pytest

from qmrl.xva import (
    CollateralAgreement,
    effective_collateral,
    simulate_collateral_path,
)


def test_perfect_collateralization_settles_immediately() -> None:
    agreement = CollateralAgreement(
        agreement_id="CSA-PERFECT",
        settlement_lag_days=0,
        margin_period_of_risk_days=0,
    )

    points = simulate_collateral_path(
        [date(2026, 1, 5)],
        [100.0],
        agreement,
    )

    assert points[0].effective_balance == pytest.approx(
        100.0
    )


def test_threshold_leaves_governed_unsecured_amount() -> None:
    agreement = CollateralAgreement(
        agreement_id="CSA-THRESHOLD",
        threshold_received=20.0,
        settlement_lag_days=0,
    )

    points = simulate_collateral_path(
        [date(2026, 1, 5)],
        [100.0],
        agreement,
    )

    assert points[0].effective_balance == pytest.approx(
        80.0
    )


def test_mta_prevents_small_transfer() -> None:
    agreement = CollateralAgreement(
        agreement_id="CSA-MTA",
        minimum_transfer_amount=5.0,
        settlement_lag_days=0,
    )

    points = simulate_collateral_path(
        [
            date(2026, 1, 5),
            date(2026, 1, 6),
        ],
        [0.0, 4.0],
        agreement,
    )

    assert points[-1].effective_balance == 0.0
    assert points[-1].transfer_called == 0.0


def test_settlement_lag_creates_temporary_exposure() -> None:
    agreement = CollateralAgreement(
        agreement_id="CSA-LAG",
        settlement_lag_days=1,
    )

    points = simulate_collateral_path(
        [
            date(2026, 1, 5),
            date(2026, 1, 6),
            date(2026, 1, 7),
        ],
        [0.0, 100.0, 100.0],
        agreement,
    )

    assert points[1].effective_balance == 0.0
    assert points[1].pending_face_balance == pytest.approx(
        100.0
    )
    assert points[2].effective_balance == pytest.approx(
        100.0
    )


def test_haircut_reduces_effective_collateral() -> None:
    agreement = CollateralAgreement(
        agreement_id="CSA-HAIRCUT",
        haircut=0.10,
    )

    assert effective_collateral(
        100.0,
        agreement,
    ) == pytest.approx(90.0)

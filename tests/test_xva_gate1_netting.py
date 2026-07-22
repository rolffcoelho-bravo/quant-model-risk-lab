from __future__ import annotations

import pytest

from qmrl.xva import (
    NettingSet,
    Trade,
    aggregate_netting_set,
    validate_trade_membership,
)


def _trades() -> list[Trade]:
    return [
        Trade(
            trade_id="T1",
            counterparty_id="CP1",
            netting_set_id="NS1",
            currency="USD",
            clean_value=100.0,
        ),
        Trade(
            trade_id="T2",
            counterparty_id="CP1",
            netting_set_id="NS1",
            currency="USD",
            clean_value=-90.0,
        ),
    ]


def _netting_set(
    eligible: bool,
) -> NettingSet:
    return NettingSet(
        netting_set_id="NS1",
        counterparty_id="CP1",
        agreement_id="ISDA-1",
        settlement_currency="USD",
        trade_ids=("T1", "T2"),
        netting_eligible=eligible,
    )


def test_eligible_netting_offsets_trade_values() -> None:
    result = aggregate_netting_set(
        _trades(),
        _netting_set(True),
    )

    assert result.clean_value == 10.0
    assert result.positive_exposure == 10.0
    assert result.negative_exposure == 0.0


def test_noneligible_set_preserves_gross_exposure() -> None:
    result = aggregate_netting_set(
        _trades(),
        _netting_set(False),
    )

    assert result.clean_value == 10.0
    assert result.positive_exposure == 100.0
    assert result.negative_exposure == 90.0


def test_duplicate_membership_is_rejected() -> None:
    first = _netting_set(True)
    second = NettingSet(
        netting_set_id="NS2",
        counterparty_id="CP1",
        agreement_id="ISDA-2",
        settlement_currency="USD",
        trade_ids=("T2",),
    )

    with pytest.raises(ValueError):
        validate_trade_membership(
            [first, second]
        )


def test_counterparty_mismatch_is_rejected() -> None:
    trades = _trades()
    trades[0] = Trade(
        trade_id="T1",
        counterparty_id="OTHER",
        netting_set_id="NS1",
        currency="USD",
        clean_value=100.0,
    )

    with pytest.raises(ValueError):
        aggregate_netting_set(
            trades,
            _netting_set(True),
        )

"""Tests for governed USD/BRL market-input identity and units."""

from __future__ import annotations

from datetime import date

import pytest

from qmrl.fx_market_inputs import (
    FXMarketInputSnapshot,
    validate_market_input_snapshot,
)


def valid_snapshot() -> FXMarketInputSnapshot:
    return FXMarketInputSnapshot(
        as_of_date=date(2026, 7, 6),
        currency_pair="USD/BRL",
        quote_convention="BRL per USD",
        spot_rate_brl_per_usd=5.0,
        domestic_rate_brl=0.15,
        foreign_rate_usd=0.04,
        spot_source_id="BCB_SGS_1",
        domestic_rate_source_id="BCB_SGS_432",
        foreign_rate_source_id="FRED_DGS1",
        spot_observation_date=date(2026, 7, 6),
        domestic_rate_observation_date=date(2026, 7, 6),
        foreign_rate_observation_date=date(2026, 7, 6),
        input_contract_status="PASS",
    )


def test_valid_market_input_snapshot_passes() -> None:
    validate_market_input_snapshot(
        valid_snapshot()
    )


def test_jpy_cannot_be_used_as_brl_rate_source() -> None:
    source = valid_snapshot()

    invalid = FXMarketInputSnapshot(
        **{
            **source.__dict__,
            "domestic_rate_source_id": "ECB_JPY",
            "domestic_rate_brl": 1.8509,
        }
    )

    with pytest.raises(
        ValueError,
        match="BCB SGS series 432",
    ):
        validate_market_input_snapshot(invalid)


def test_rate_above_decimal_contract_is_rejected() -> None:
    source = valid_snapshot()

    invalid = FXMarketInputSnapshot(
        **{
            **source.__dict__,
            "domestic_rate_brl": 1.8509,
        }
    )

    with pytest.raises(
        ValueError,
        match="annual decimal",
    ):
        validate_market_input_snapshot(invalid)


def test_wrong_quote_convention_is_rejected() -> None:
    source = valid_snapshot()

    invalid = FXMarketInputSnapshot(
        **{
            **source.__dict__,
            "quote_convention": "USD per BRL",
        }
    )

    with pytest.raises(
        ValueError,
        match="BRL per USD",
    ):
        validate_market_input_snapshot(invalid)
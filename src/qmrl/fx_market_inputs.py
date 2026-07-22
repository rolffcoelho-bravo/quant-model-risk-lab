"""Governed market-input contract for the USD/BRL validation layers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pandas as pd


EXPECTED_CURRENCY_PAIR = "USD/BRL"
EXPECTED_QUOTE_CONVENTION = "BRL per USD"
EXPECTED_SPOT_SOURCE = "BCB_SGS_1"
EXPECTED_DOMESTIC_RATE_SOURCE = "BCB_SGS_432"
EXPECTED_FOREIGN_RATE_SOURCE = "FRED_DGS1"


@dataclass(frozen=True)
class FXMarketInputSnapshot:
    """Validated and traceable market inputs for USD/BRL valuation."""

    as_of_date: date
    currency_pair: str
    quote_convention: str
    spot_rate_brl_per_usd: float
    domestic_rate_brl: float
    foreign_rate_usd: float
    spot_source_id: str
    domestic_rate_source_id: str
    foreign_rate_source_id: str
    spot_observation_date: date
    domestic_rate_observation_date: date
    foreign_rate_observation_date: date
    input_contract_status: str


def _parse_date(value: object, field_name: str) -> date:
    parsed = pd.to_datetime(value, errors="coerce")

    if pd.isna(parsed):
        raise ValueError(f"{field_name} is not a valid date.")

    return parsed.date()


def validate_market_input_snapshot(
    snapshot: FXMarketInputSnapshot,
) -> None:
    """Fail closed when source identity, units or economic scale are invalid."""
    if snapshot.currency_pair != EXPECTED_CURRENCY_PAIR:
        raise ValueError(
            "The market-input currency pair must be USD/BRL."
        )

    if snapshot.quote_convention != EXPECTED_QUOTE_CONVENTION:
        raise ValueError(
            "The spot quote must use BRL per USD."
        )

    if snapshot.spot_source_id != EXPECTED_SPOT_SOURCE:
        raise ValueError(
            "USD/BRL spot must originate from BCB SGS series 1."
        )

    if (
        snapshot.domestic_rate_source_id
        != EXPECTED_DOMESTIC_RATE_SOURCE
    ):
        raise ValueError(
            "The BRL domestic-rate proxy must originate from "
            "BCB SGS series 432."
        )

    if (
        snapshot.foreign_rate_source_id
        != EXPECTED_FOREIGN_RATE_SOURCE
    ):
        raise ValueError(
            "The USD foreign-rate proxy must originate from FRED DGS1."
        )

    spot = float(snapshot.spot_rate_brl_per_usd)
    domestic_rate = float(snapshot.domestic_rate_brl)
    foreign_rate = float(snapshot.foreign_rate_usd)

    if not 1.0 < spot < 20.0:
        raise ValueError(
            "USD/BRL spot is outside the governed validation range."
        )

    if not 0.0 <= domestic_rate < 1.0:
        raise ValueError(
            "BRL domestic rate must be an annual decimal below one."
        )

    if not -0.10 < foreign_rate < 0.30:
        raise ValueError(
            "USD foreign rate is outside the governed validation range."
        )

    for observation_date in (
        snapshot.spot_observation_date,
        snapshot.domestic_rate_observation_date,
        snapshot.foreign_rate_observation_date,
    ):
        if observation_date > snapshot.as_of_date:
            raise ValueError(
                "A source observation occurs after the governed as-of date."
            )

        staleness = (
            snapshot.as_of_date - observation_date
        ).days

        if staleness > 14:
            raise ValueError(
                "A market input is more than fourteen calendar days stale."
            )

    if snapshot.input_contract_status != "PASS":
        raise ValueError(
            "The market-input contract status must be PASS."
        )


def load_market_input_snapshot(
    path: str | Path,
) -> FXMarketInputSnapshot:
    """Load and validate the governed market-input snapshot."""
    frame = pd.read_csv(path)

    if len(frame) != 1:
        raise ValueError(
            "The market-input snapshot must contain exactly one record."
        )

    row = frame.iloc[0]

    snapshot = FXMarketInputSnapshot(
        as_of_date=_parse_date(
            row["as_of_date"],
            "as_of_date",
        ),
        currency_pair=str(row["currency_pair"]),
        quote_convention=str(row["quote_convention"]),
        spot_rate_brl_per_usd=float(
            row["spot_rate_brl_per_usd"]
        ),
        domestic_rate_brl=float(
            row["domestic_rate_brl"]
        ),
        foreign_rate_usd=float(
            row["foreign_rate_usd"]
        ),
        spot_source_id=str(row["spot_source_id"]),
        domestic_rate_source_id=str(
            row["domestic_rate_source_id"]
        ),
        foreign_rate_source_id=str(
            row["foreign_rate_source_id"]
        ),
        spot_observation_date=_parse_date(
            row["spot_observation_date"],
            "spot_observation_date",
        ),
        domestic_rate_observation_date=_parse_date(
            row["domestic_rate_observation_date"],
            "domestic_rate_observation_date",
        ),
        foreign_rate_observation_date=_parse_date(
            row["foreign_rate_observation_date"],
            "foreign_rate_observation_date",
        ),
        input_contract_status=str(
            row["input_contract_status"]
        ),
    )

    validate_market_input_snapshot(snapshot)
    return snapshot
"""Netting-set representation and deterministic aggregation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable


@dataclass(frozen=True)
class Trade:
    """Minimal Gate 1 trade reference used for netting validation."""

    trade_id: str
    counterparty_id: str
    netting_set_id: str
    currency: str
    clean_value: float

    def __post_init__(self) -> None:
        for name in (
            "trade_id",
            "counterparty_id",
            "netting_set_id",
        ):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} must not be empty.")

        if len(self.currency.strip()) != 3:
            raise ValueError(
                "currency must be a three-letter code."
            )


@dataclass(frozen=True)
class NettingSet:
    """Governed legal and operational netting-set metadata."""

    netting_set_id: str
    counterparty_id: str
    agreement_id: str
    settlement_currency: str
    trade_ids: tuple[str, ...]
    netting_eligible: bool = True
    collateral_agreement_id: str | None = None
    close_out_convention: str = "replacement_cost"
    wrong_way_risk_classification: str = "none"
    effective_date: date | None = None
    review_date: date | None = None

    def __post_init__(self) -> None:
        for name in (
            "netting_set_id",
            "counterparty_id",
            "agreement_id",
            "close_out_convention",
            "wrong_way_risk_classification",
        ):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} must not be empty.")

        if len(self.settlement_currency.strip()) != 3:
            raise ValueError(
                "settlement_currency must be a "
                "three-letter code."
            )

        if not self.trade_ids:
            raise ValueError(
                "A netting set must contain at least one trade."
            )

        if len(self.trade_ids) != len(set(self.trade_ids)):
            raise ValueError(
                "trade_ids must be unique within a netting set."
            )

        if (
            self.effective_date is not None
            and self.review_date is not None
            and self.review_date < self.effective_date
        ):
            raise ValueError(
                "review_date must not precede effective_date."
            )


@dataclass(frozen=True)
class NettingResult:
    """Transparent netting aggregation result."""

    netting_set_id: str
    clean_value: float
    positive_exposure: float
    negative_exposure: float
    trade_count: int
    netting_eligible: bool


def validate_trade_membership(
    netting_sets: Iterable[NettingSet],
) -> dict[str, str]:
    """Reject silent allocation of one trade to multiple netting sets."""

    membership: dict[str, str] = {}

    for netting_set in netting_sets:
        for trade_id in netting_set.trade_ids:
            existing = membership.get(trade_id)

            if (
                existing is not None
                and existing != netting_set.netting_set_id
            ):
                raise ValueError(
                    f"Trade {trade_id!r} belongs to "
                    f"multiple netting sets: "
                    f"{existing!r} and "
                    f"{netting_set.netting_set_id!r}."
                )

            membership[trade_id] = (
                netting_set.netting_set_id
            )

    return membership


def aggregate_netting_set(
    trades: Iterable[Trade],
    netting_set: NettingSet,
) -> NettingResult:
    """Aggregate clean values under eligible or gross treatment."""

    trade_list = list(trades)
    trade_map = {
        trade.trade_id: trade
        for trade in trade_list
    }

    if len(trade_map) != len(trade_list):
        raise ValueError("Trade identifiers must be unique.")

    expected_ids = set(netting_set.trade_ids)
    actual_ids = set(trade_map)

    if expected_ids != actual_ids:
        missing = sorted(expected_ids - actual_ids)
        unexpected = sorted(actual_ids - expected_ids)

        raise ValueError(
            "Trade membership mismatch. "
            f"Missing={missing}; unexpected={unexpected}."
        )

    settlement_currency = (
        netting_set.settlement_currency.upper()
    )

    for trade in trade_list:
        if (
            trade.counterparty_id
            != netting_set.counterparty_id
        ):
            raise ValueError(
                "All trades must match the netting-set "
                "counterparty."
            )

        if trade.netting_set_id != netting_set.netting_set_id:
            raise ValueError(
                "Trade netting_set_id does not match "
                "the governed netting set."
            )

        if trade.currency.upper() != settlement_currency:
            raise ValueError(
                "Gate 1 requires trade currency to match "
                "the settlement currency."
            )

    values = [
        float(trade.clean_value)
        for trade in trade_list
    ]

    clean_value = float(sum(values))

    if netting_set.netting_eligible:
        positive = max(clean_value, 0.0)
        negative = max(-clean_value, 0.0)
    else:
        positive = float(
            sum(max(value, 0.0) for value in values)
        )
        negative = float(
            sum(max(-value, 0.0) for value in values)
        )

    return NettingResult(
        netting_set_id=netting_set.netting_set_id,
        clean_value=clean_value,
        positive_exposure=positive,
        negative_exposure=negative,
        trade_count=len(trade_list),
        netting_eligible=netting_set.netting_eligible,
    )

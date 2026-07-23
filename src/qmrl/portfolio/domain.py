"""Canonical portfolio domain model for the v1.4 Gate 1 ingestion layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class CurrencyDefinition:
    code: str
    decimals: int = 2


@dataclass(frozen=True)
class LegalEntity:
    legal_entity_id: str
    name: str
    reporting_currency: str


@dataclass(frozen=True)
class Counterparty:
    counterparty_id: str
    name: str
    parent_counterparty_id: str | None = None
    credit_curve_id: str | None = None


@dataclass(frozen=True)
class AgreementTerms:
    agreement_id: str
    threshold: float = 0.0
    minimum_transfer_amount: float = 0.0
    margin_frequency_days: int = 1
    margin_period_of_risk_days: int = 10
    eligible_collateral_currencies: tuple[str, ...] = ()


@dataclass(frozen=True)
class NettingSet:
    netting_set_id: str
    counterparty_id: str
    legal_entity_id: str
    agreement_id: str


@dataclass(frozen=True)
class CollateralSet:
    collateral_set_id: str
    netting_set_id: str
    agreement_id: str
    eligible_currencies: tuple[str, ...] = ()


@dataclass(frozen=True)
class TradeRecord:
    trade_id: str
    product_type: str
    legal_entity_id: str
    counterparty_id: str
    netting_set_id: str
    collateral_set_id: str | None
    trade_currency: str
    settlement_currency: str
    notional: float
    effective_date: str
    maturity_date: str
    attributes: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PortfolioSnapshot:
    snapshot_id: str
    valuation_date: str
    reporting_currency: str
    currencies: tuple[CurrencyDefinition, ...]
    legal_entities: tuple[LegalEntity, ...]
    counterparties: tuple[Counterparty, ...]
    agreements: tuple[AgreementTerms, ...]
    netting_sets: tuple[NettingSet, ...]
    collateral_sets: tuple[CollateralSet, ...]
    trades: tuple[TradeRecord, ...]
    schema_version: str = "1.0"

    def counts(self) -> dict[str, int]:
        return {
            "currencies": len(self.currencies),
            "legal_entities": len(self.legal_entities),
            "counterparties": len(self.counterparties),
            "agreements": len(self.agreements),
            "netting_sets": len(self.netting_sets),
            "collateral_sets": len(self.collateral_sets),
            "trades": len(self.trades),
        }

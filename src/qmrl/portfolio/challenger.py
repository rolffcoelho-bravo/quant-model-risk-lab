"""Independent portfolio parser and mapping challenger."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, Mapping

from .domain import PortfolioSnapshot
from .ingestion import portfolio_to_mapping


@dataclass(frozen=True)
class ParserChallengerReport:
    status: str
    discrepancies: tuple[str, ...]
    primary_counts: dict[str, int]
    challenger_counts: dict[str, int]


def independent_raw_counts(
    payload: Mapping[str, Any],
) -> dict[str, int]:
    keys = (
        "currencies",
        "legal_entities",
        "counterparties",
        "agreements",
        "netting_sets",
        "collateral_sets",
        "trades",
    )
    counts: dict[str, int] = {}
    for key in keys:
        value = payload.get(key)
        counts[key] = len(value) if isinstance(value, list) else -1
    return counts


def _independent_relationship_discrepancies(
    payload: Mapping[str, Any],
) -> list[str]:
    discrepancies: list[str] = []
    netting = {
        item.get("netting_set_id"): item
        for item in payload.get("netting_sets", [])
        if isinstance(item, dict)
    }
    collateral = {
        item.get("collateral_set_id"): item
        for item in payload.get("collateral_sets", [])
        if isinstance(item, dict)
    }
    for trade in payload.get("trades", []):
        if not isinstance(trade, dict):
            discrepancies.append("non_object_trade")
            continue
        trade_id = trade.get("trade_id", "<missing>")
        netting_item = netting.get(trade.get("netting_set_id"))
        if netting_item is None:
            discrepancies.append(f"{trade_id}:missing_netting_set")
            continue
        if netting_item.get("counterparty_id") != trade.get("counterparty_id"):
            discrepancies.append(f"{trade_id}:counterparty_mismatch")
        if netting_item.get("legal_entity_id") != trade.get("legal_entity_id"):
            discrepancies.append(f"{trade_id}:legal_entity_mismatch")
        collateral_id = trade.get("collateral_set_id")
        if collateral_id is not None:
            collateral_item = collateral.get(collateral_id)
            if collateral_item is None:
                discrepancies.append(f"{trade_id}:missing_collateral_set")
            elif collateral_item.get("netting_set_id") != trade.get("netting_set_id"):
                discrepancies.append(f"{trade_id}:collateral_mapping_mismatch")
    return discrepancies


def challenge_portfolio_parser(
    snapshot: PortfolioSnapshot,
    source_payload: Mapping[str, Any] | str,
) -> ParserChallengerReport:
    if isinstance(source_payload, str):
        decoded = json.loads(source_payload)
        if not isinstance(decoded, dict):
            raise ValueError("Challenger source must decode to an object.")
        payload = decoded
    else:
        payload = dict(source_payload)

    primary = snapshot.counts()
    challenger = independent_raw_counts(payload)
    discrepancies = _independent_relationship_discrepancies(payload)

    for key in sorted(primary):
        if primary[key] != challenger.get(key):
            discrepancies.append(
                f"count:{key}:{primary[key]}!={challenger.get(key)}"
            )

    canonical = portfolio_to_mapping(snapshot)
    primary_trade_ids = sorted(
        item["trade_id"] for item in canonical["trades"]
    )
    challenger_trade_ids = sorted(
        item.get("trade_id")
        for item in payload.get("trades", [])
        if isinstance(item, dict)
    )
    if primary_trade_ids != challenger_trade_ids:
        discrepancies.append("trade_identifier_set_mismatch")

    unique = tuple(sorted(set(discrepancies)))
    return ParserChallengerReport(
        status="PASS" if not unique else "BLOCK",
        discrepancies=unique,
        primary_counts=primary,
        challenger_counts=challenger,
    )

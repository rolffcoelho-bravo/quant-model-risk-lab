from __future__ import annotations

import copy
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from qmrl.portfolio import (
    PortfolioIngestionError,
    PortfolioSchemaError,
    build_data_quality_report,
    canonical_portfolio_hash,
    ingest_portfolio_mapping,
    load_portfolio_snapshot,
    portfolio_from_mapping,
    portfolio_to_json,
    portfolio_to_mapping,
)

VALID = ROOT / "data" / "portfolio" / "fixtures" / "valid_reference_portfolio.json"


def raw_valid() -> dict:
    return json.loads(VALID.read_text(encoding="utf-8"))


def test_valid_reference_fixture_ingests() -> None:
    result = load_portfolio_snapshot(VALID)
    assert result.validation.is_valid is True
    assert result.validation.error_count == 0


def test_valid_reference_counts_are_locked() -> None:
    result = load_portfolio_snapshot(VALID)
    assert result.snapshot.counts() == {
        "currencies": 3,
        "legal_entities": 1,
        "counterparties": 3,
        "agreements": 2,
        "netting_sets": 2,
        "collateral_sets": 2,
        "trades": 4,
    }


def test_round_trip_serialization_preserves_snapshot() -> None:
    first = load_portfolio_snapshot(VALID).snapshot
    second = portfolio_from_mapping(
        json.loads(portfolio_to_json(first))
    )
    assert portfolio_to_mapping(first) == portfolio_to_mapping(second)


def test_canonical_hash_is_independent_of_collection_order() -> None:
    payload = raw_valid()
    first = portfolio_from_mapping(payload)
    payload["trades"] = list(reversed(payload["trades"]))
    payload["counterparties"] = list(reversed(payload["counterparties"]))
    second = portfolio_from_mapping(payload)
    assert canonical_portfolio_hash(first) == canonical_portfolio_hash(second)


def test_compact_json_is_deterministic() -> None:
    snapshot = load_portfolio_snapshot(VALID).snapshot
    assert portfolio_to_json(snapshot, indent=None) == portfolio_to_json(
        snapshot,
        indent=None,
    )


def test_unknown_root_field_is_rejected() -> None:
    payload = raw_valid()
    payload["unsupported"] = True
    with pytest.raises(PortfolioSchemaError):
        portfolio_from_mapping(payload)


def test_unknown_trade_field_is_rejected() -> None:
    payload = raw_valid()
    payload["trades"][0]["unsupported"] = True
    with pytest.raises(PortfolioSchemaError):
        portfolio_from_mapping(payload)


def test_collection_must_be_an_array() -> None:
    payload = raw_valid()
    payload["trades"] = {}
    with pytest.raises(PortfolioSchemaError):
        portfolio_from_mapping(payload)


def test_invalid_snapshot_is_rejected_by_default() -> None:
    payload = raw_valid()
    payload["trades"][0]["netting_set_id"] = "NS_MISSING"
    with pytest.raises(PortfolioIngestionError) as exc_info:
        ingest_portfolio_mapping(payload)
    assert "MISSING_NETTING_SET" in exc_info.value.validation.issue_codes


def test_invalid_snapshot_can_generate_blocking_evidence() -> None:
    payload = raw_valid()
    payload["trades"][0]["netting_set_id"] = "NS_MISSING"
    result = ingest_portfolio_mapping(payload, reject_invalid=False)
    report = build_data_quality_report(result.snapshot, result.validation)
    assert report["status"] == "BLOCK"
    assert report["downstream_calculation_permitted"] is False

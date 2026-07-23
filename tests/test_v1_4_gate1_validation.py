from __future__ import annotations

import copy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from qmrl.portfolio import (
    build_data_quality_report,
    ingest_portfolio_mapping,
)

VALID = ROOT / "data" / "portfolio" / "fixtures" / "valid_reference_portfolio.json"


def raw_valid() -> dict:
    return json.loads(VALID.read_text(encoding="utf-8"))


def issue_codes(payload: dict) -> set[str]:
    result = ingest_portfolio_mapping(payload, reject_invalid=False)
    return set(result.validation.issue_codes)


def test_duplicate_trade_identifier_is_blocked() -> None:
    payload = raw_valid()
    payload["trades"].append(copy.deepcopy(payload["trades"][0]))
    assert "DUPLICATE_IDENTIFIER" in issue_codes(payload)


def test_missing_netting_set_is_blocked() -> None:
    payload = raw_valid()
    payload["trades"][0]["netting_set_id"] = "NS_MISSING"
    assert "MISSING_NETTING_SET" in issue_codes(payload)


def test_counterparty_hierarchy_cycle_is_blocked() -> None:
    payload = raw_valid()
    payload["counterparties"][0]["parent_counterparty_id"] = "CP_BANK_A"
    assert "COUNTERPARTY_HIERARCHY_CYCLE" in issue_codes(payload)


def test_trade_collateral_mapping_mismatch_is_blocked() -> None:
    payload = raw_valid()
    payload["trades"][0]["collateral_set_id"] = "CS_B"
    assert "TRADE_COLLATERAL_MAPPING_MISMATCH" in issue_codes(payload)


def test_trade_counterparty_mismatch_is_blocked() -> None:
    payload = raw_valid()
    payload["trades"][0]["counterparty_id"] = "CP_CORP_B"
    assert "TRADE_COUNTERPARTY_MISMATCH" in issue_codes(payload)


def test_trade_legal_entity_mismatch_is_blocked() -> None:
    payload = raw_valid()
    payload["legal_entities"].append(
        {
            "legal_entity_id": "LE_ALT",
            "name": "Alternative Entity",
            "reporting_currency": "EUR",
        }
    )
    payload["trades"][0]["legal_entity_id"] = "LE_ALT"
    assert "TRADE_LEGAL_ENTITY_MISMATCH" in issue_codes(payload)


def test_undeclared_trade_currency_is_blocked() -> None:
    payload = raw_valid()
    payload["trades"][0]["trade_currency"] = "JPY"
    assert "UNDECLARED_TRADE_CURRENCY" in issue_codes(payload)


def test_zero_notional_is_blocked() -> None:
    payload = raw_valid()
    payload["trades"][0]["notional"] = 0.0
    assert "ZERO_NOTIONAL" in issue_codes(payload)


def test_invalid_trade_date_order_is_blocked() -> None:
    payload = raw_valid()
    payload["trades"][0]["effective_date"] = "2028-01-01"
    payload["trades"][0]["maturity_date"] = "2027-01-01"
    assert "INVALID_TRADE_DATE_ORDER" in issue_codes(payload)


def test_matured_trade_is_blocked() -> None:
    payload = raw_valid()
    payload["trades"][0]["maturity_date"] = "2026-07-22"
    codes = issue_codes(payload)
    assert "MATURED_TRADE" in codes


def test_data_quality_metrics_reconcile() -> None:
    payload = raw_valid()
    payload["trades"][0]["notional"] = 0.0
    result = ingest_portfolio_mapping(payload, reject_invalid=False)
    report = build_data_quality_report(result.snapshot, result.validation)
    assert report["metrics"]["trades"] == 4
    assert report["metrics"]["errors"] >= 1
    assert report["status"] == "BLOCK"

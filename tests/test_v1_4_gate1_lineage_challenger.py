from __future__ import annotations

import copy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from qmrl.portfolio import (
    build_lineage_manifest,
    canonical_mapping_hash,
    canonical_portfolio_hash,
    challenge_portfolio_parser,
    compare_lineage_manifests,
    independent_raw_counts,
    portfolio_from_mapping,
)

VALID = ROOT / "data" / "portfolio" / "fixtures" / "valid_reference_portfolio.json"


def raw_valid() -> dict:
    return json.loads(VALID.read_text(encoding="utf-8"))


def snapshot():
    return portfolio_from_mapping(raw_valid())


def build_manifest(
    *,
    configuration: dict | None = None,
    created_at: str = "2026-07-23T12:00:00Z",
):
    return build_lineage_manifest(
        snapshot(),
        configuration=configuration or {"paths": 1000, "currency": "EUR"},
        model_version="1.4.0-dev",
        random_seed=17,
        created_at_utc=created_at,
        source_hash="source",
    )


def test_canonical_mapping_hash_is_key_order_independent() -> None:
    assert canonical_mapping_hash({"a": 1, "b": 2}) == canonical_mapping_hash(
        {"b": 2, "a": 1}
    )


def test_run_identity_ignores_creation_timestamp() -> None:
    first = build_manifest(created_at="2026-07-23T12:00:00Z")
    second = build_manifest(created_at="2026-07-23T13:00:00Z")
    assert first.run.run_id == second.run.run_id


def test_configuration_change_changes_run_identity() -> None:
    first = build_manifest(configuration={"paths": 1000})
    second = build_manifest(configuration={"paths": 2000})
    assert first.run.configuration_hash != second.run.configuration_hash
    assert first.run.run_id != second.run.run_id


def test_portfolio_change_changes_canonical_input_hash() -> None:
    payload = raw_valid()
    first = portfolio_from_mapping(payload)
    payload["trades"][0]["notional"] += 1.0
    second = portfolio_from_mapping(payload)
    assert canonical_portfolio_hash(first) != canonical_portfolio_hash(second)


def test_lineage_comparison_identifies_configuration_difference() -> None:
    first = build_manifest(configuration={"paths": 1000})
    second = build_manifest(configuration={"paths": 2000})
    comparison = compare_lineage_manifests(first, second)
    assert comparison["identical_calculation_identity"] is False
    assert "configuration_hash" in comparison["differences"]


def test_independent_parser_challenger_passes_valid_snapshot() -> None:
    payload = raw_valid()
    report = challenge_portfolio_parser(
        portfolio_from_mapping(payload),
        payload,
    )
    assert report.status == "PASS"
    assert report.discrepancies == ()


def test_independent_parser_challenger_detects_tampered_mapping() -> None:
    payload = raw_valid()
    primary = portfolio_from_mapping(payload)
    tampered = copy.deepcopy(payload)
    tampered["trades"][0]["counterparty_id"] = "CP_CORP_B"
    report = challenge_portfolio_parser(primary, tampered)
    assert report.status == "BLOCK"
    assert any("counterparty_mismatch" in item for item in report.discrepancies)


def test_independent_raw_counts_cover_all_canonical_collections() -> None:
    counts = independent_raw_counts(raw_valid())
    assert counts == {
        "currencies": 3,
        "legal_entities": 1,
        "counterparties": 3,
        "agreements": 2,
        "netting_sets": 2,
        "collateral_sets": 2,
        "trades": 4,
    }


def test_invalid_validation_status_blocks_lineage_promotion() -> None:
    manifest = build_lineage_manifest(
        snapshot(),
        configuration={"paths": 1000},
        model_version="1.4.0-dev",
        random_seed=17,
        created_at_utc="2026-07-23T12:00:00Z",
        validation_status="BLOCK",
    )
    assert manifest.downstream_calculation_permitted is False

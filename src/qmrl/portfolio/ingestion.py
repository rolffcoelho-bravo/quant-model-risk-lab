"""Strict JSON ingestion and deterministic serialization for portfolio snapshots."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .domain import (
    AgreementTerms,
    CollateralSet,
    Counterparty,
    CurrencyDefinition,
    LegalEntity,
    NettingSet,
    PortfolioSnapshot,
    TradeRecord,
)
from .validation import (
    PortfolioValidationResult,
    validate_portfolio_snapshot,
)


class PortfolioSchemaError(ValueError):
    """Raised when raw input does not satisfy the canonical JSON schema."""


class PortfolioIngestionError(ValueError):
    """Raised when parsed portfolio data fails validation."""

    def __init__(
        self,
        message: str,
        validation: PortfolioValidationResult,
    ) -> None:
        super().__init__(message)
        self.validation = validation


@dataclass(frozen=True)
class PortfolioIngestionResult:
    snapshot: PortfolioSnapshot
    validation: PortfolioValidationResult
    source_hash: str
    canonical_hash: str


def _expect_mapping(value: object, path: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise PortfolioSchemaError(f"{path} must be an object.")
    return value


def _expect_sequence(value: object, path: str) -> Sequence[object]:
    if not isinstance(value, list):
        raise PortfolioSchemaError(f"{path} must be an array.")
    return value


def _keys(
    mapping: Mapping[str, Any],
    *,
    required: set[str],
    optional: set[str],
    path: str,
) -> None:
    missing = required - set(mapping)
    unknown = set(mapping) - required - optional
    if missing:
        raise PortfolioSchemaError(
            f"{path} is missing required fields: {sorted(missing)}"
        )
    if unknown:
        raise PortfolioSchemaError(
            f"{path} contains unknown fields: {sorted(unknown)}"
        )


def _string(value: object, path: str) -> str:
    if not isinstance(value, str):
        raise PortfolioSchemaError(f"{path} must be a string.")
    return value


def _optional_string(value: object, path: str) -> str | None:
    if value is None:
        return None
    return _string(value, path)


def _number(value: object, path: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise PortfolioSchemaError(f"{path} must be numeric.")
    return float(value)


def _integer(value: object, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise PortfolioSchemaError(f"{path} must be an integer.")
    return value


def _string_tuple(value: object, path: str) -> tuple[str, ...]:
    return tuple(
        _string(item, f"{path}[{index}]")
        for index, item in enumerate(_expect_sequence(value, path))
    )


def _attributes(value: object, path: str) -> Mapping[str, Any]:
    mapping = _expect_mapping(value, path)
    try:
        json.dumps(mapping, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise PortfolioSchemaError(
            f"{path} must contain JSON-compatible finite values."
        ) from exc
    return dict(mapping)


def portfolio_from_mapping(
    payload: Mapping[str, Any],
) -> PortfolioSnapshot:
    root = _expect_mapping(payload, "$")
    required = {
        "snapshot_id",
        "valuation_date",
        "reporting_currency",
        "currencies",
        "legal_entities",
        "counterparties",
        "agreements",
        "netting_sets",
        "collateral_sets",
        "trades",
    }
    _keys(
        root,
        required=required,
        optional={"schema_version"},
        path="$",
    )

    currencies = []
    for index, raw in enumerate(_expect_sequence(root["currencies"], "$.currencies")):
        item = _expect_mapping(raw, f"$.currencies[{index}]")
        _keys(
            item,
            required={"code"},
            optional={"decimals"},
            path=f"$.currencies[{index}]",
        )
        currencies.append(
            CurrencyDefinition(
                code=_string(item["code"], f"$.currencies[{index}].code"),
                decimals=_integer(
                    item.get("decimals", 2),
                    f"$.currencies[{index}].decimals",
                ),
            )
        )

    legal_entities = []
    for index, raw in enumerate(
        _expect_sequence(root["legal_entities"], "$.legal_entities")
    ):
        item = _expect_mapping(raw, f"$.legal_entities[{index}]")
        _keys(
            item,
            required={"legal_entity_id", "name", "reporting_currency"},
            optional=set(),
            path=f"$.legal_entities[{index}]",
        )
        legal_entities.append(
            LegalEntity(
                legal_entity_id=_string(
                    item["legal_entity_id"],
                    f"$.legal_entities[{index}].legal_entity_id",
                ),
                name=_string(item["name"], f"$.legal_entities[{index}].name"),
                reporting_currency=_string(
                    item["reporting_currency"],
                    f"$.legal_entities[{index}].reporting_currency",
                ),
            )
        )

    counterparties = []
    for index, raw in enumerate(
        _expect_sequence(root["counterparties"], "$.counterparties")
    ):
        item = _expect_mapping(raw, f"$.counterparties[{index}]")
        _keys(
            item,
            required={"counterparty_id", "name"},
            optional={"parent_counterparty_id", "credit_curve_id"},
            path=f"$.counterparties[{index}]",
        )
        counterparties.append(
            Counterparty(
                counterparty_id=_string(
                    item["counterparty_id"],
                    f"$.counterparties[{index}].counterparty_id",
                ),
                name=_string(item["name"], f"$.counterparties[{index}].name"),
                parent_counterparty_id=_optional_string(
                    item.get("parent_counterparty_id"),
                    f"$.counterparties[{index}].parent_counterparty_id",
                ),
                credit_curve_id=_optional_string(
                    item.get("credit_curve_id"),
                    f"$.counterparties[{index}].credit_curve_id",
                ),
            )
        )

    agreements = []
    for index, raw in enumerate(
        _expect_sequence(root["agreements"], "$.agreements")
    ):
        item = _expect_mapping(raw, f"$.agreements[{index}]")
        _keys(
            item,
            required={"agreement_id"},
            optional={
                "threshold",
                "minimum_transfer_amount",
                "margin_frequency_days",
                "margin_period_of_risk_days",
                "eligible_collateral_currencies",
            },
            path=f"$.agreements[{index}]",
        )
        agreements.append(
            AgreementTerms(
                agreement_id=_string(
                    item["agreement_id"],
                    f"$.agreements[{index}].agreement_id",
                ),
                threshold=_number(
                    item.get("threshold", 0.0),
                    f"$.agreements[{index}].threshold",
                ),
                minimum_transfer_amount=_number(
                    item.get("minimum_transfer_amount", 0.0),
                    f"$.agreements[{index}].minimum_transfer_amount",
                ),
                margin_frequency_days=_integer(
                    item.get("margin_frequency_days", 1),
                    f"$.agreements[{index}].margin_frequency_days",
                ),
                margin_period_of_risk_days=_integer(
                    item.get("margin_period_of_risk_days", 10),
                    f"$.agreements[{index}].margin_period_of_risk_days",
                ),
                eligible_collateral_currencies=_string_tuple(
                    item.get("eligible_collateral_currencies", []),
                    f"$.agreements[{index}].eligible_collateral_currencies",
                ),
            )
        )

    netting_sets = []
    for index, raw in enumerate(
        _expect_sequence(root["netting_sets"], "$.netting_sets")
    ):
        item = _expect_mapping(raw, f"$.netting_sets[{index}]")
        _keys(
            item,
            required={
                "netting_set_id",
                "counterparty_id",
                "legal_entity_id",
                "agreement_id",
            },
            optional=set(),
            path=f"$.netting_sets[{index}]",
        )
        netting_sets.append(
            NettingSet(
                netting_set_id=_string(
                    item["netting_set_id"],
                    f"$.netting_sets[{index}].netting_set_id",
                ),
                counterparty_id=_string(
                    item["counterparty_id"],
                    f"$.netting_sets[{index}].counterparty_id",
                ),
                legal_entity_id=_string(
                    item["legal_entity_id"],
                    f"$.netting_sets[{index}].legal_entity_id",
                ),
                agreement_id=_string(
                    item["agreement_id"],
                    f"$.netting_sets[{index}].agreement_id",
                ),
            )
        )

    collateral_sets = []
    for index, raw in enumerate(
        _expect_sequence(root["collateral_sets"], "$.collateral_sets")
    ):
        item = _expect_mapping(raw, f"$.collateral_sets[{index}]")
        _keys(
            item,
            required={
                "collateral_set_id",
                "netting_set_id",
                "agreement_id",
            },
            optional={"eligible_currencies"},
            path=f"$.collateral_sets[{index}]",
        )
        collateral_sets.append(
            CollateralSet(
                collateral_set_id=_string(
                    item["collateral_set_id"],
                    f"$.collateral_sets[{index}].collateral_set_id",
                ),
                netting_set_id=_string(
                    item["netting_set_id"],
                    f"$.collateral_sets[{index}].netting_set_id",
                ),
                agreement_id=_string(
                    item["agreement_id"],
                    f"$.collateral_sets[{index}].agreement_id",
                ),
                eligible_currencies=_string_tuple(
                    item.get("eligible_currencies", []),
                    f"$.collateral_sets[{index}].eligible_currencies",
                ),
            )
        )

    trades = []
    for index, raw in enumerate(_expect_sequence(root["trades"], "$.trades")):
        item = _expect_mapping(raw, f"$.trades[{index}]")
        _keys(
            item,
            required={
                "trade_id",
                "product_type",
                "legal_entity_id",
                "counterparty_id",
                "netting_set_id",
                "trade_currency",
                "settlement_currency",
                "notional",
                "effective_date",
                "maturity_date",
            },
            optional={"collateral_set_id", "attributes"},
            path=f"$.trades[{index}]",
        )
        trades.append(
            TradeRecord(
                trade_id=_string(item["trade_id"], f"$.trades[{index}].trade_id"),
                product_type=_string(
                    item["product_type"],
                    f"$.trades[{index}].product_type",
                ),
                legal_entity_id=_string(
                    item["legal_entity_id"],
                    f"$.trades[{index}].legal_entity_id",
                ),
                counterparty_id=_string(
                    item["counterparty_id"],
                    f"$.trades[{index}].counterparty_id",
                ),
                netting_set_id=_string(
                    item["netting_set_id"],
                    f"$.trades[{index}].netting_set_id",
                ),
                collateral_set_id=_optional_string(
                    item.get("collateral_set_id"),
                    f"$.trades[{index}].collateral_set_id",
                ),
                trade_currency=_string(
                    item["trade_currency"],
                    f"$.trades[{index}].trade_currency",
                ),
                settlement_currency=_string(
                    item["settlement_currency"],
                    f"$.trades[{index}].settlement_currency",
                ),
                notional=_number(
                    item["notional"],
                    f"$.trades[{index}].notional",
                ),
                effective_date=_string(
                    item["effective_date"],
                    f"$.trades[{index}].effective_date",
                ),
                maturity_date=_string(
                    item["maturity_date"],
                    f"$.trades[{index}].maturity_date",
                ),
                attributes=_attributes(
                    item.get("attributes", {}),
                    f"$.trades[{index}].attributes",
                ),
            )
        )

    return PortfolioSnapshot(
        snapshot_id=_string(root["snapshot_id"], "$.snapshot_id"),
        valuation_date=_string(root["valuation_date"], "$.valuation_date"),
        reporting_currency=_string(
            root["reporting_currency"],
            "$.reporting_currency",
        ),
        currencies=tuple(currencies),
        legal_entities=tuple(legal_entities),
        counterparties=tuple(counterparties),
        agreements=tuple(agreements),
        netting_sets=tuple(netting_sets),
        collateral_sets=tuple(collateral_sets),
        trades=tuple(trades),
        schema_version=_string(root.get("schema_version", "1.0"), "$.schema_version"),
    )


def _normal(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _normal(value[key])
            for key in sorted(value, key=str)
        }
    if isinstance(value, tuple):
        return [_normal(item) for item in value]
    if isinstance(value, list):
        return [_normal(item) for item in value]
    return value


def portfolio_to_mapping(snapshot: PortfolioSnapshot) -> dict[str, Any]:
    return {
        "schema_version": snapshot.schema_version,
        "snapshot_id": snapshot.snapshot_id,
        "valuation_date": snapshot.valuation_date,
        "reporting_currency": snapshot.reporting_currency,
        "currencies": [
            {"code": item.code, "decimals": item.decimals}
            for item in sorted(snapshot.currencies, key=lambda item: item.code)
        ],
        "legal_entities": [
            {
                "legal_entity_id": item.legal_entity_id,
                "name": item.name,
                "reporting_currency": item.reporting_currency,
            }
            for item in sorted(
                snapshot.legal_entities,
                key=lambda item: item.legal_entity_id,
            )
        ],
        "counterparties": [
            {
                "counterparty_id": item.counterparty_id,
                "name": item.name,
                **(
                    {"parent_counterparty_id": item.parent_counterparty_id}
                    if item.parent_counterparty_id is not None
                    else {}
                ),
                **(
                    {"credit_curve_id": item.credit_curve_id}
                    if item.credit_curve_id is not None
                    else {}
                ),
            }
            for item in sorted(
                snapshot.counterparties,
                key=lambda item: item.counterparty_id,
            )
        ],
        "agreements": [
            {
                "agreement_id": item.agreement_id,
                "threshold": item.threshold,
                "minimum_transfer_amount": item.minimum_transfer_amount,
                "margin_frequency_days": item.margin_frequency_days,
                "margin_period_of_risk_days": item.margin_period_of_risk_days,
                "eligible_collateral_currencies": sorted(
                    item.eligible_collateral_currencies
                ),
            }
            for item in sorted(
                snapshot.agreements,
                key=lambda item: item.agreement_id,
            )
        ],
        "netting_sets": [
            {
                "netting_set_id": item.netting_set_id,
                "counterparty_id": item.counterparty_id,
                "legal_entity_id": item.legal_entity_id,
                "agreement_id": item.agreement_id,
            }
            for item in sorted(
                snapshot.netting_sets,
                key=lambda item: item.netting_set_id,
            )
        ],
        "collateral_sets": [
            {
                "collateral_set_id": item.collateral_set_id,
                "netting_set_id": item.netting_set_id,
                "agreement_id": item.agreement_id,
                "eligible_currencies": sorted(item.eligible_currencies),
            }
            for item in sorted(
                snapshot.collateral_sets,
                key=lambda item: item.collateral_set_id,
            )
        ],
        "trades": [
            {
                "trade_id": item.trade_id,
                "product_type": item.product_type,
                "legal_entity_id": item.legal_entity_id,
                "counterparty_id": item.counterparty_id,
                "netting_set_id": item.netting_set_id,
                **(
                    {"collateral_set_id": item.collateral_set_id}
                    if item.collateral_set_id is not None
                    else {}
                ),
                "trade_currency": item.trade_currency,
                "settlement_currency": item.settlement_currency,
                "notional": item.notional,
                "effective_date": item.effective_date,
                "maturity_date": item.maturity_date,
                "attributes": _normal(item.attributes),
            }
            for item in sorted(snapshot.trades, key=lambda item: item.trade_id)
        ],
    }


def portfolio_to_json(
    snapshot: PortfolioSnapshot,
    *,
    indent: int | None = 2,
) -> str:
    return json.dumps(
        portfolio_to_mapping(snapshot),
        sort_keys=True,
        separators=(",", ":") if indent is None else None,
        indent=indent,
        ensure_ascii=False,
        allow_nan=False,
    ) + ("" if indent is None else "\n")


def portfolio_from_json(value: str) -> PortfolioSnapshot:
    try:
        payload = json.loads(value)
    except json.JSONDecodeError as exc:
        raise PortfolioSchemaError(f"Invalid JSON: {exc.msg}") from exc
    return portfolio_from_mapping(_expect_mapping(payload, "$"))


def ingest_portfolio_mapping(
    payload: Mapping[str, Any],
    *,
    reject_invalid: bool = True,
    source_hash: str = "",
) -> PortfolioIngestionResult:
    from .lineage import canonical_portfolio_hash

    snapshot = portfolio_from_mapping(payload)
    validation = validate_portfolio_snapshot(snapshot)
    result = PortfolioIngestionResult(
        snapshot=snapshot,
        validation=validation,
        source_hash=source_hash,
        canonical_hash=canonical_portfolio_hash(snapshot),
    )
    if reject_invalid and not validation.is_valid:
        raise PortfolioIngestionError(
            "Portfolio snapshot failed governed validation.",
            validation,
        )
    return result


def ingest_portfolio_json(
    value: str,
    *,
    reject_invalid: bool = True,
) -> PortfolioIngestionResult:
    from .lineage import sha256_bytes

    payload = json.loads(value)
    return ingest_portfolio_mapping(
        _expect_mapping(payload, "$"),
        reject_invalid=reject_invalid,
        source_hash=sha256_bytes(value.encode("utf-8")),
    )


def load_portfolio_snapshot(
    path: str | Path,
    *,
    reject_invalid: bool = True,
) -> PortfolioIngestionResult:
    file_path = Path(path)
    data = file_path.read_bytes()
    try:
        value = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise PortfolioSchemaError(
            "Portfolio input must be UTF-8 encoded."
        ) from exc
    from .lineage import sha256_bytes

    payload = json.loads(value)
    return ingest_portfolio_mapping(
        _expect_mapping(payload, "$"),
        reject_invalid=reject_invalid,
        source_hash=sha256_bytes(data),
    )

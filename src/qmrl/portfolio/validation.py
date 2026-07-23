"""Deterministic portfolio validation and data-quality evidence."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import math
import re
from typing import Iterable

from .domain import PortfolioSnapshot


_CURRENCY = re.compile(r"^[A-Z]{3}$")
_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    severity: str
    path: str
    message: str


@dataclass(frozen=True)
class PortfolioValidationResult:
    is_valid: bool
    issues: tuple[ValidationIssue, ...]
    metrics: dict[str, int]

    @property
    def issue_codes(self) -> tuple[str, ...]:
        return tuple(issue.code for issue in self.issues)

    @property
    def error_count(self) -> int:
        return sum(issue.severity == "ERROR" for issue in self.issues)

    @property
    def warning_count(self) -> int:
        return sum(issue.severity == "WARNING" for issue in self.issues)


def _duplicates(values: Iterable[str]) -> set[str]:
    seen: set[str] = set()
    duplicate: set[str] = set()
    for value in values:
        if value in seen:
            duplicate.add(value)
        seen.add(value)
    return duplicate


def _valid_date(value: str) -> date | None:
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def _issue(
    issues: list[ValidationIssue],
    code: str,
    path: str,
    message: str,
    severity: str = "ERROR",
) -> None:
    issues.append(
        ValidationIssue(
            code=code,
            severity=severity,
            path=path,
            message=message,
        )
    )


def _validate_id(
    issues: list[ValidationIssue],
    value: str,
    path: str,
) -> None:
    if not isinstance(value, str) or not _ID.fullmatch(value):
        _issue(
            issues,
            "INVALID_IDENTIFIER",
            path,
            "Identifier must match the governed identifier syntax.",
        )


def validate_portfolio_snapshot(
    snapshot: PortfolioSnapshot,
) -> PortfolioValidationResult:
    issues: list[ValidationIssue] = []

    _validate_id(issues, snapshot.snapshot_id, "snapshot_id")
    valuation_date = _valid_date(snapshot.valuation_date)
    if valuation_date is None:
        _issue(
            issues,
            "INVALID_VALUATION_DATE",
            "valuation_date",
            "Valuation date must be ISO-8601 YYYY-MM-DD.",
        )

    collections = {
        "currencies": (
            snapshot.currencies,
            lambda item: item.code,
        ),
        "legal_entities": (
            snapshot.legal_entities,
            lambda item: item.legal_entity_id,
        ),
        "counterparties": (
            snapshot.counterparties,
            lambda item: item.counterparty_id,
        ),
        "agreements": (
            snapshot.agreements,
            lambda item: item.agreement_id,
        ),
        "netting_sets": (
            snapshot.netting_sets,
            lambda item: item.netting_set_id,
        ),
        "collateral_sets": (
            snapshot.collateral_sets,
            lambda item: item.collateral_set_id,
        ),
        "trades": (
            snapshot.trades,
            lambda item: item.trade_id,
        ),
    }

    for collection_name, (items, key) in collections.items():
        for duplicate in sorted(_duplicates(key(item) for item in items)):
            _issue(
                issues,
                "DUPLICATE_IDENTIFIER",
                collection_name,
                f"Duplicate identifier: {duplicate}",
            )

    currency_codes = {item.code for item in snapshot.currencies}
    legal_entity_ids = {
        item.legal_entity_id for item in snapshot.legal_entities
    }
    counterparty_ids = {
        item.counterparty_id for item in snapshot.counterparties
    }
    agreement_ids = {
        item.agreement_id for item in snapshot.agreements
    }
    netting_by_id = {
        item.netting_set_id: item for item in snapshot.netting_sets
    }
    collateral_by_id = {
        item.collateral_set_id: item
        for item in snapshot.collateral_sets
    }

    for index, currency in enumerate(snapshot.currencies):
        _validate_id(
            issues,
            currency.code,
            f"currencies[{index}].code",
        )
        if not _CURRENCY.fullmatch(currency.code):
            _issue(
                issues,
                "INVALID_CURRENCY",
                f"currencies[{index}].code",
                "Currency code must contain exactly three uppercase letters.",
            )
        if currency.decimals < 0 or currency.decimals > 6:
            _issue(
                issues,
                "INVALID_CURRENCY_DECIMALS",
                f"currencies[{index}].decimals",
                "Currency decimals must be between zero and six.",
            )

    if snapshot.reporting_currency not in currency_codes:
        _issue(
            issues,
            "UNDECLARED_REPORTING_CURRENCY",
            "reporting_currency",
            "Reporting currency must be declared in currencies.",
        )

    for index, entity in enumerate(snapshot.legal_entities):
        _validate_id(
            issues,
            entity.legal_entity_id,
            f"legal_entities[{index}].legal_entity_id",
        )
        if entity.reporting_currency not in currency_codes:
            _issue(
                issues,
                "UNDECLARED_ENTITY_CURRENCY",
                f"legal_entities[{index}].reporting_currency",
                "Legal-entity reporting currency is not declared.",
            )

    counterparties = {
        item.counterparty_id: item
        for item in snapshot.counterparties
    }

    for index, counterparty in enumerate(snapshot.counterparties):
        _validate_id(
            issues,
            counterparty.counterparty_id,
            f"counterparties[{index}].counterparty_id",
        )
        parent = counterparty.parent_counterparty_id
        if parent is not None and parent not in counterparty_ids:
            _issue(
                issues,
                "MISSING_PARENT_COUNTERPARTY",
                f"counterparties[{index}].parent_counterparty_id",
                f"Parent counterparty {parent!r} does not exist.",
            )

    for start_id in sorted(counterparty_ids):
        visited: set[str] = set()
        current = start_id
        while current in counterparties:
            if current in visited:
                _issue(
                    issues,
                    "COUNTERPARTY_HIERARCHY_CYCLE",
                    f"counterparties[{start_id}]",
                    "Counterparty hierarchy contains a cycle.",
                )
                break
            visited.add(current)
            parent = counterparties[current].parent_counterparty_id
            if parent is None:
                break
            current = parent

    for index, agreement in enumerate(snapshot.agreements):
        _validate_id(
            issues,
            agreement.agreement_id,
            f"agreements[{index}].agreement_id",
        )
        if agreement.threshold < 0:
            _issue(
                issues,
                "NEGATIVE_THRESHOLD",
                f"agreements[{index}].threshold",
                "Threshold cannot be negative.",
            )
        if agreement.minimum_transfer_amount < 0:
            _issue(
                issues,
                "NEGATIVE_MTA",
                f"agreements[{index}].minimum_transfer_amount",
                "Minimum transfer amount cannot be negative.",
            )
        if agreement.margin_frequency_days <= 0:
            _issue(
                issues,
                "INVALID_MARGIN_FREQUENCY",
                f"agreements[{index}].margin_frequency_days",
                "Margin frequency must be positive.",
            )
        if agreement.margin_period_of_risk_days <= 0:
            _issue(
                issues,
                "INVALID_MPOR",
                f"agreements[{index}].margin_period_of_risk_days",
                "Margin period of risk must be positive.",
            )
        for currency in agreement.eligible_collateral_currencies:
            if currency not in currency_codes:
                _issue(
                    issues,
                    "UNDECLARED_COLLATERAL_CURRENCY",
                    f"agreements[{index}].eligible_collateral_currencies",
                    f"Eligible collateral currency {currency!r} is not declared.",
                )

    for index, netting_set in enumerate(snapshot.netting_sets):
        _validate_id(
            issues,
            netting_set.netting_set_id,
            f"netting_sets[{index}].netting_set_id",
        )
        if netting_set.counterparty_id not in counterparty_ids:
            _issue(
                issues,
                "MISSING_COUNTERPARTY",
                f"netting_sets[{index}].counterparty_id",
                "Netting-set counterparty does not exist.",
            )
        if netting_set.legal_entity_id not in legal_entity_ids:
            _issue(
                issues,
                "MISSING_LEGAL_ENTITY",
                f"netting_sets[{index}].legal_entity_id",
                "Netting-set legal entity does not exist.",
            )
        if netting_set.agreement_id not in agreement_ids:
            _issue(
                issues,
                "MISSING_AGREEMENT",
                f"netting_sets[{index}].agreement_id",
                "Netting-set agreement does not exist.",
            )

    for index, collateral_set in enumerate(snapshot.collateral_sets):
        _validate_id(
            issues,
            collateral_set.collateral_set_id,
            f"collateral_sets[{index}].collateral_set_id",
        )
        netting = netting_by_id.get(collateral_set.netting_set_id)
        if netting is None:
            _issue(
                issues,
                "MISSING_NETTING_SET",
                f"collateral_sets[{index}].netting_set_id",
                "Collateral-set netting set does not exist.",
            )
        if collateral_set.agreement_id not in agreement_ids:
            _issue(
                issues,
                "MISSING_AGREEMENT",
                f"collateral_sets[{index}].agreement_id",
                "Collateral-set agreement does not exist.",
            )
        if (
            netting is not None
            and netting.agreement_id != collateral_set.agreement_id
        ):
            _issue(
                issues,
                "COLLATERAL_AGREEMENT_MISMATCH",
                f"collateral_sets[{index}].agreement_id",
                "Collateral set and netting set reference different agreements.",
            )
        for currency in collateral_set.eligible_currencies:
            if currency not in currency_codes:
                _issue(
                    issues,
                    "UNDECLARED_COLLATERAL_CURRENCY",
                    f"collateral_sets[{index}].eligible_currencies",
                    f"Eligible collateral currency {currency!r} is not declared.",
                )

    for index, trade in enumerate(snapshot.trades):
        prefix = f"trades[{index}]"
        _validate_id(issues, trade.trade_id, f"{prefix}.trade_id")
        netting = netting_by_id.get(trade.netting_set_id)
        if trade.legal_entity_id not in legal_entity_ids:
            _issue(
                issues,
                "MISSING_LEGAL_ENTITY",
                f"{prefix}.legal_entity_id",
                "Trade legal entity does not exist.",
            )
        if trade.counterparty_id not in counterparty_ids:
            _issue(
                issues,
                "MISSING_COUNTERPARTY",
                f"{prefix}.counterparty_id",
                "Trade counterparty does not exist.",
            )
        if netting is None:
            _issue(
                issues,
                "MISSING_NETTING_SET",
                f"{prefix}.netting_set_id",
                "Trade netting set does not exist.",
            )
        else:
            if netting.counterparty_id != trade.counterparty_id:
                _issue(
                    issues,
                    "TRADE_COUNTERPARTY_MISMATCH",
                    f"{prefix}.counterparty_id",
                    "Trade and netting-set counterparties differ.",
                )
            if netting.legal_entity_id != trade.legal_entity_id:
                _issue(
                    issues,
                    "TRADE_LEGAL_ENTITY_MISMATCH",
                    f"{prefix}.legal_entity_id",
                    "Trade and netting-set legal entities differ.",
                )

        if trade.collateral_set_id is not None:
            collateral = collateral_by_id.get(trade.collateral_set_id)
            if collateral is None:
                _issue(
                    issues,
                    "MISSING_COLLATERAL_SET",
                    f"{prefix}.collateral_set_id",
                    "Trade collateral set does not exist.",
                )
            elif collateral.netting_set_id != trade.netting_set_id:
                _issue(
                    issues,
                    "TRADE_COLLATERAL_MAPPING_MISMATCH",
                    f"{prefix}.collateral_set_id",
                    "Trade collateral set belongs to a different netting set.",
                )

        for field_name, currency in (
            ("trade_currency", trade.trade_currency),
            ("settlement_currency", trade.settlement_currency),
        ):
            if currency not in currency_codes:
                _issue(
                    issues,
                    "UNDECLARED_TRADE_CURRENCY",
                    f"{prefix}.{field_name}",
                    f"Trade currency {currency!r} is not declared.",
                )

        if not isinstance(trade.notional, (int, float)) or not math.isfinite(
            float(trade.notional)
        ):
            _issue(
                issues,
                "NON_FINITE_NOTIONAL",
                f"{prefix}.notional",
                "Trade notional must be finite.",
            )
        elif float(trade.notional) == 0.0:
            _issue(
                issues,
                "ZERO_NOTIONAL",
                f"{prefix}.notional",
                "Trade notional cannot be zero.",
            )

        effective = _valid_date(trade.effective_date)
        maturity = _valid_date(trade.maturity_date)
        if effective is None:
            _issue(
                issues,
                "INVALID_EFFECTIVE_DATE",
                f"{prefix}.effective_date",
                "Trade effective date must be ISO-8601.",
            )
        if maturity is None:
            _issue(
                issues,
                "INVALID_MATURITY_DATE",
                f"{prefix}.maturity_date",
                "Trade maturity date must be ISO-8601.",
            )
        if effective is not None and maturity is not None and maturity <= effective:
            _issue(
                issues,
                "INVALID_TRADE_DATE_ORDER",
                f"{prefix}.maturity_date",
                "Maturity date must be after effective date.",
            )
        if valuation_date is not None and maturity is not None and maturity <= valuation_date:
            _issue(
                issues,
                "MATURED_TRADE",
                f"{prefix}.maturity_date",
                "Matured trade cannot enter the active portfolio snapshot.",
            )

    issues.sort(
        key=lambda item: (
            item.path,
            item.code,
            item.message,
        )
    )
    metrics = snapshot.counts()
    metrics.update(
        {
            "errors": sum(item.severity == "ERROR" for item in issues),
            "warnings": sum(item.severity == "WARNING" for item in issues),
        }
    )
    return PortfolioValidationResult(
        is_valid=not any(item.severity == "ERROR" for item in issues),
        issues=tuple(issues),
        metrics=metrics,
    )


def build_data_quality_report(
    snapshot: PortfolioSnapshot,
    result: PortfolioValidationResult,
) -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "snapshot_id": snapshot.snapshot_id,
        "valuation_date": snapshot.valuation_date,
        "status": "PASS" if result.is_valid else "BLOCK",
        "is_valid": result.is_valid,
        "metrics": dict(sorted(result.metrics.items())),
        "issues": [
            {
                "code": issue.code,
                "severity": issue.severity,
                "path": issue.path,
                "message": issue.message,
            }
            for issue in result.issues
        ],
        "downstream_calculation_permitted": result.is_valid,
    }

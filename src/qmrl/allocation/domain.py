"""Domain objects for v1.4 Gate 5 incremental and allocation analytics."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import math
from typing import Mapping


ALLOCATION_BOUNDARY = "FULL_REVALUATION_PRIMARY_APPROXIMATION_DISCLOSED"


class AllocationStatus(str, Enum):
    PASS = "PASS"
    PASS_WITH_MONITORING = "PASS_WITH_MONITORING"
    REMEDIATE = "REMEDIATE"
    BLOCK = "BLOCK"
    INVALID = "INVALID"


_COMPONENTS = (
    "cva",
    "dva",
    "fca",
    "fba",
    "mva",
    "kva",
    "wwr_uplift",
    "stress_adjustment",
)


@dataclass(frozen=True)
class AdjustmentVector:
    """Valuation-adjustment components.

    CVA, FCA, MVA, KVA, and WWR uplift are cost magnitudes.
    DVA and FBA are benefit magnitudes. Stress adjustment is signed.
    """

    cva: float = 0.0
    dva: float = 0.0
    fca: float = 0.0
    fba: float = 0.0
    mva: float = 0.0
    kva: float = 0.0
    wwr_uplift: float = 0.0
    stress_adjustment: float = 0.0

    def __post_init__(self) -> None:
        for name in _COMPONENTS:
            value = float(getattr(self, name))
            if not math.isfinite(value):
                raise ValueError(f"{name} must be finite.")
            if name != "stress_adjustment" and value < -1e-12:
                raise ValueError(f"{name} must be non-negative.")
            object.__setattr__(self, name, max(value, 0.0) if name != "stress_adjustment" else value)

    @property
    def fva(self) -> float:
        return self.fca - self.fba

    @property
    def total_adjustment(self) -> float:
        return (
            -self.cva
            + self.dva
            - self.fca
            + self.fba
            - self.mva
            - self.kva
            - self.wwr_uplift
            + self.stress_adjustment
        )

    def as_dict(self) -> dict[str, float]:
        result = {name: float(getattr(self, name)) for name in _COMPONENTS}
        result["fva"] = self.fva
        result["total_adjustment"] = self.total_adjustment
        return result

    def add(self, other: "AdjustmentVector") -> "AdjustmentVector":
        return AdjustmentVector(**{
            name: float(getattr(self, name)) + float(getattr(other, name))
            for name in _COMPONENTS
        })

    def subtract(self, other: "AdjustmentVector") -> "SignedAdjustmentVector":
        return SignedAdjustmentVector(**{
            name: float(getattr(self, name)) - float(getattr(other, name))
            for name in _COMPONENTS
        })

    def scaled(self, factor: float) -> "AdjustmentVector":
        factor = float(factor)
        if not math.isfinite(factor) or factor < 0.0:
            raise ValueError("AdjustmentVector scale factor must be finite and non-negative.")
        return AdjustmentVector(**{
            name: float(getattr(self, name)) * factor
            for name in _COMPONENTS
        })


@dataclass(frozen=True)
class SignedAdjustmentVector:
    """Signed change or allocation vector."""

    cva: float = 0.0
    dva: float = 0.0
    fca: float = 0.0
    fba: float = 0.0
    mva: float = 0.0
    kva: float = 0.0
    wwr_uplift: float = 0.0
    stress_adjustment: float = 0.0

    def __post_init__(self) -> None:
        for name in _COMPONENTS:
            value = float(getattr(self, name))
            if not math.isfinite(value):
                raise ValueError(f"{name} must be finite.")
            object.__setattr__(self, name, value)

    @property
    def fva(self) -> float:
        return self.fca - self.fba

    @property
    def total_adjustment(self) -> float:
        return (
            -self.cva
            + self.dva
            - self.fca
            + self.fba
            - self.mva
            - self.kva
            - self.wwr_uplift
            + self.stress_adjustment
        )

    def as_dict(self) -> dict[str, float]:
        result = {name: float(getattr(self, name)) for name in _COMPONENTS}
        result["fva"] = self.fva
        result["total_adjustment"] = self.total_adjustment
        return result

    def add(self, other: "SignedAdjustmentVector") -> "SignedAdjustmentVector":
        return SignedAdjustmentVector(**{
            name: float(getattr(self, name)) + float(getattr(other, name))
            for name in _COMPONENTS
        })

    def subtract(self, other: "SignedAdjustmentVector") -> "SignedAdjustmentVector":
        return SignedAdjustmentVector(**{
            name: float(getattr(self, name)) - float(getattr(other, name))
            for name in _COMPONENTS
        })

    def scaled(self, factor: float) -> "SignedAdjustmentVector":
        factor = float(factor)
        if not math.isfinite(factor):
            raise ValueError("SignedAdjustmentVector scale factor must be finite.")
        return SignedAdjustmentVector(**{
            name: float(getattr(self, name)) * factor
            for name in _COMPONENTS
        })


@dataclass(frozen=True)
class TradeAllocationInput:
    trade_id: str
    counterparty_id: str
    netting_set_id: str
    currency: str
    product_family: str
    scale: float
    standalone: AdjustmentVector
    threshold: float = 0.0
    minimum_transfer_amount: float = 0.0
    concentration_group: str = ""
    stress_multiplier: float = 1.0

    def __post_init__(self) -> None:
        for name in (
            "trade_id",
            "counterparty_id",
            "netting_set_id",
            "currency",
            "product_family",
        ):
            value = str(getattr(self, name)).strip()
            if not value:
                raise ValueError(f"{name} cannot be blank.")
            object.__setattr__(self, name, value.upper() if name == "currency" else value)
        if len(self.currency) != 3 or not self.currency.isalpha():
            raise ValueError("currency must be an ISO-style three-letter code.")
        for name in ("scale", "threshold", "minimum_transfer_amount", "stress_multiplier"):
            value = float(getattr(self, name))
            if not math.isfinite(value):
                raise ValueError(f"{name} must be finite.")
            if name in {"scale", "stress_multiplier"} and value <= 0.0:
                raise ValueError(f"{name} must be positive.")
            if name in {"threshold", "minimum_transfer_amount"} and value < 0.0:
                raise ValueError(f"{name} cannot be negative.")
            object.__setattr__(self, name, value)

    def rescaled(self, new_scale: float) -> "TradeAllocationInput":
        return TradeAllocationInput(
            trade_id=self.trade_id,
            counterparty_id=self.counterparty_id,
            netting_set_id=self.netting_set_id,
            currency=self.currency,
            product_family=self.product_family,
            scale=float(new_scale),
            standalone=self.standalone,
            threshold=self.threshold,
            minimum_transfer_amount=self.minimum_transfer_amount,
            concentration_group=self.concentration_group,
            stress_multiplier=self.stress_multiplier,
        )


@dataclass(frozen=True)
class PortfolioAllocationState:
    portfolio_id: str
    trades: tuple[TradeAllocationInput, ...]
    reporting_currency: str = "USD"
    collateral_regime_switch: bool = False
    concentration_addon_rate: float = 0.0

    def __post_init__(self) -> None:
        if not self.portfolio_id.strip():
            raise ValueError("portfolio_id cannot be blank.")
        if not self.trades:
            raise ValueError("Portfolio must contain at least one trade.")
        ids = [trade.trade_id for trade in self.trades]
        if len(ids) != len(set(ids)):
            raise ValueError("Trade identifiers must be unique.")
        currency = self.reporting_currency.strip().upper()
        if len(currency) != 3 or not currency.isalpha():
            raise ValueError("reporting_currency must be an ISO-style three-letter code.")
        rate = float(self.concentration_addon_rate)
        if not math.isfinite(rate) or rate < 0.0:
            raise ValueError("concentration_addon_rate must be finite and non-negative.")
        object.__setattr__(self, "reporting_currency", currency)
        object.__setattr__(self, "concentration_addon_rate", rate)

    def trade(self, trade_id: str) -> TradeAllocationInput:
        for trade in self.trades:
            if trade.trade_id == trade_id:
                return trade
        raise KeyError(trade_id)

    def without(self, trade_id: str) -> "PortfolioAllocationState":
        retained = tuple(trade for trade in self.trades if trade.trade_id != trade_id)
        if len(retained) == len(self.trades):
            raise KeyError(trade_id)
        if not retained:
            raise ValueError("Removal cannot create an empty portfolio.")
        return PortfolioAllocationState(
            portfolio_id=self.portfolio_id,
            trades=retained,
            reporting_currency=self.reporting_currency,
            collateral_regime_switch=self.collateral_regime_switch,
            concentration_addon_rate=self.concentration_addon_rate,
        )

    def with_trade(self, trade: TradeAllocationInput) -> "PortfolioAllocationState":
        if any(item.trade_id == trade.trade_id for item in self.trades):
            raise ValueError("Inserted trade identifier already exists.")
        return PortfolioAllocationState(
            portfolio_id=self.portfolio_id,
            trades=(*self.trades, trade),
            reporting_currency=self.reporting_currency,
            collateral_regime_switch=self.collateral_regime_switch,
            concentration_addon_rate=self.concentration_addon_rate,
        )

    def replace(self, trade_id: str, trade: TradeAllocationInput) -> "PortfolioAllocationState":
        if trade.trade_id != trade_id and any(item.trade_id == trade.trade_id for item in self.trades):
            raise ValueError("Replacement trade identifier already exists.")
        found = False
        updated = []
        for item in self.trades:
            if item.trade_id == trade_id:
                updated.append(trade)
                found = True
            else:
                updated.append(item)
        if not found:
            raise KeyError(trade_id)
        return PortfolioAllocationState(
            portfolio_id=self.portfolio_id,
            trades=tuple(updated),
            reporting_currency=self.reporting_currency,
            collateral_regime_switch=self.collateral_regime_switch,
            concentration_addon_rate=self.concentration_addon_rate,
        )


@dataclass(frozen=True)
class IncrementalResult:
    operation: str
    trade_id: str
    base: AdjustmentVector
    changed: AdjustmentVector
    increment: SignedAdjustmentVector
    full_revaluation: bool = True
    boundary: str = ALLOCATION_BOUNDARY

    def __post_init__(self) -> None:
        if self.operation not in {"insert", "remove", "replace"}:
            raise ValueError("Unsupported incremental operation.")
        if not self.trade_id.strip():
            raise ValueError("trade_id cannot be blank.")
        expected = self.changed.subtract(self.base)
        for name in _COMPONENTS:
            if abs(float(getattr(expected, name)) - float(getattr(self.increment, name))) > 1e-10:
                raise ValueError("Incremental components do not reconcile.")
        if not self.full_revaluation:
            raise ValueError("IncrementalResult must originate from full revaluation.")
        if self.boundary != ALLOCATION_BOUNDARY:
            raise ValueError("Incremental result must retain the governance boundary.")


@dataclass(frozen=True)
class MarginalResult:
    trade_id: str
    bump_fraction: float
    derivative: SignedAdjustmentVector
    convergence_error: float
    full_revaluation_reference: SignedAdjustmentVector | None
    approximation_error: float | None
    status: AllocationStatus
    boundary: str = ALLOCATION_BOUNDARY

    def __post_init__(self) -> None:
        if not self.trade_id.strip():
            raise ValueError("trade_id cannot be blank.")
        if not math.isfinite(self.bump_fraction) or self.bump_fraction <= 0.0:
            raise ValueError("bump_fraction must be finite and positive.")
        if not math.isfinite(self.convergence_error) or self.convergence_error < 0.0:
            raise ValueError("convergence_error must be finite and non-negative.")
        if self.approximation_error is not None and (
            not math.isfinite(self.approximation_error) or self.approximation_error < 0.0
        ):
            raise ValueError("approximation_error must be finite and non-negative.")
        if self.boundary != ALLOCATION_BOUNDARY:
            raise ValueError("Marginal result must retain the governance boundary.")


@dataclass(frozen=True)
class NonlinearityReport:
    threshold_present: bool
    mta_present: bool
    concentration_addon_present: bool
    collateral_regime_switch: bool
    homogeneity_error: float
    euler_valid: bool
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class AllocationResult:
    portfolio: AdjustmentVector
    by_trade: Mapping[str, SignedAdjustmentVector]
    residual: SignedAdjustmentVector
    method: str
    status: AllocationStatus
    nonlinearity: NonlinearityReport
    boundary: str = ALLOCATION_BOUNDARY

    def __post_init__(self) -> None:
        if self.method not in {"euler", "leave_one_out", "standalone"}:
            raise ValueError("Unsupported allocation method.")
        if len(self.by_trade) != len(set(self.by_trade)):
            raise ValueError("Trade allocation keys must be unique.")
        combined = SignedAdjustmentVector()
        for vector in self.by_trade.values():
            combined = combined.add(vector)
        target = SignedAdjustmentVector(**{
            name: float(getattr(self.portfolio, name))
            for name in _COMPONENTS
        })
        expected_residual = target.subtract(combined)
        for name in _COMPONENTS:
            if abs(float(getattr(expected_residual, name)) - float(getattr(self.residual, name))) > 1e-9:
                raise ValueError("Allocation residual does not reconcile.")
        if self.boundary != ALLOCATION_BOUNDARY:
            raise ValueError("Allocation result must retain the governance boundary.")


@dataclass(frozen=True)
class RankingRow:
    key: str
    total_adjustment: float
    absolute_share: float
    rank: int


@dataclass(frozen=True)
class AllocationChallenge:
    status: AllocationStatus
    primary_total: float
    challenger_total: float
    absolute_difference: float
    tolerance: float
    details: Mapping[str, float] = field(default_factory=dict)

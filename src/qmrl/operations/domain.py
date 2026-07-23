"""Operational domain objects for v1.4 Gate 6."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import math
from types import MappingProxyType
from typing import Any, Mapping


OPERATIONAL_BOUNDARY = "QUANTITATIVE_EQUIVALENCE_REQUIRED"


class ChangeKind(str, Enum):
    NONE = "none"
    TRADE = "trade"
    MARKET = "market"
    POLICY = "policy"
    GRAPH = "graph"


class ExecutionStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"
    REUSED = "REUSED"
    CACHE_HIT = "CACHE_HIT"


class FailureClass(str, Enum):
    INPUT = "INPUT"
    DEPENDENCY = "DEPENDENCY"
    RESOURCE = "RESOURCE"
    EXECUTION = "EXECUTION"
    CHECKPOINT = "CHECKPOINT"


def _id(value: str, name: str) -> str:
    result = str(value).strip()
    if not result:
        raise ValueError(f"{name} cannot be empty.")
    return result


def _hash(value: str, name: str) -> str:
    result = _id(value, name).lower()
    if len(result) != 64 or any(char not in "0123456789abcdef" for char in result):
        raise ValueError(f"{name} must be a 64-character SHA-256 hex digest.")
    return result


def _sorted_mapping(value: Mapping[str, str], name: str) -> Mapping[str, str]:
    converted: dict[str, str] = {}
    for key, digest in value.items():
        item_id = _id(key, f"{name} key")
        if item_id in converted:
            raise ValueError(f"Duplicate {name} key: {item_id}.")
        converted[item_id] = _hash(digest, f"{name}[{item_id}]")
    return MappingProxyType(dict(sorted(converted.items())))


@dataclass(frozen=True)
class DependencyNode:
    node_id: str
    dependencies: tuple[str, ...] = ()
    cacheable: bool = True
    quantitative: bool = True
    scope: str = "portfolio"

    def __post_init__(self) -> None:
        node_id = _id(self.node_id, "node_id")
        dependencies = tuple(_id(value, "dependency") for value in self.dependencies)
        if len(set(dependencies)) != len(dependencies):
            raise ValueError("Dependencies must be unique.")
        if node_id in dependencies:
            raise ValueError("A dependency node cannot depend on itself.")
        object.__setattr__(self, "node_id", node_id)
        object.__setattr__(self, "dependencies", dependencies)
        object.__setattr__(self, "scope", _id(self.scope, "scope"))


@dataclass(frozen=True)
class OperationalSnapshot:
    snapshot_id: str
    portfolio_hash: str
    trade_hashes: Mapping[str, str]
    market_hashes: Mapping[str, str]
    policy_hashes: Mapping[str, str]
    graph_hash: str
    engine_version: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "snapshot_id", _id(self.snapshot_id, "snapshot_id"))
        object.__setattr__(self, "portfolio_hash", _hash(self.portfolio_hash, "portfolio_hash"))
        object.__setattr__(self, "trade_hashes", _sorted_mapping(self.trade_hashes, "trade_hashes"))
        object.__setattr__(self, "market_hashes", _sorted_mapping(self.market_hashes, "market_hashes"))
        object.__setattr__(self, "policy_hashes", _sorted_mapping(self.policy_hashes, "policy_hashes"))
        object.__setattr__(self, "graph_hash", _hash(self.graph_hash, "graph_hash"))
        object.__setattr__(self, "engine_version", _id(self.engine_version, "engine_version"))


@dataclass(frozen=True)
class ChangeSet:
    added_trades: tuple[str, ...] = ()
    removed_trades: tuple[str, ...] = ()
    modified_trades: tuple[str, ...] = ()
    market_factors: tuple[str, ...] = ()
    policies: tuple[str, ...] = ()
    graph_changed: bool = False

    def __post_init__(self) -> None:
        for name in (
            "added_trades",
            "removed_trades",
            "modified_trades",
            "market_factors",
            "policies",
        ):
            values = tuple(sorted({_id(value, name) for value in getattr(self, name)}))
            object.__setattr__(self, name, values)
        trade_groups = [
            set(self.added_trades),
            set(self.removed_trades),
            set(self.modified_trades),
        ]
        if any(trade_groups[i] & trade_groups[j] for i in range(3) for j in range(i + 1, 3)):
            raise ValueError("A trade cannot belong to multiple change categories.")

    @property
    def is_empty(self) -> bool:
        return not (
            self.added_trades
            or self.removed_trades
            or self.modified_trades
            or self.market_factors
            or self.policies
            or self.graph_changed
        )

    @property
    def affected_scopes(self) -> tuple[str, ...]:
        values = [
            *(f"trade:{value}" for value in self.added_trades),
            *(f"trade:{value}" for value in self.removed_trades),
            *(f"trade:{value}" for value in self.modified_trades),
            *(f"market:{value}" for value in self.market_factors),
            *(f"policy:{value}" for value in self.policies),
        ]
        if self.graph_changed:
            values.append("graph:topology")
        return tuple(sorted(values))


@dataclass(frozen=True)
class RecalculationPlan:
    node_ids: tuple[str, ...]
    reasons: Mapping[str, tuple[str, ...]]
    affected_scopes: tuple[str, ...]
    full_recalculation: bool
    plan_hash: str
    boundary: str = OPERATIONAL_BOUNDARY

    def __post_init__(self) -> None:
        nodes = tuple(_id(value, "node_id") for value in self.node_ids)
        if len(set(nodes)) != len(nodes):
            raise ValueError("Recalculation nodes must be unique.")
        converted = {
            _id(key, "reason node"): tuple(sorted({_id(v, "reason") for v in values}))
            for key, values in self.reasons.items()
        }
        if set(converted) != set(nodes):
            raise ValueError("Every planned node must have a reason record.")
        if self.boundary != OPERATIONAL_BOUNDARY:
            raise ValueError("Operational plans must retain the quantitative-equivalence boundary.")
        object.__setattr__(self, "node_ids", nodes)
        object.__setattr__(self, "reasons", MappingProxyType(dict(sorted(converted.items()))))
        object.__setattr__(self, "affected_scopes", tuple(sorted(set(self.affected_scopes))))
        object.__setattr__(self, "plan_hash", _hash(self.plan_hash, "plan_hash"))


@dataclass(frozen=True)
class ExecutionRecord:
    node_id: str
    status: ExecutionStatus
    input_hash: str
    output_hash: str
    cache_key: str
    duration_seconds: float
    attempt: int = 1
    failure_class: FailureClass | None = None
    message: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "node_id", _id(self.node_id, "node_id"))
        for name in ("input_hash", "output_hash", "cache_key"):
            value = getattr(self, name)
            if value:
                object.__setattr__(self, name, _hash(value, name))
        if not math.isfinite(self.duration_seconds) or self.duration_seconds < 0.0:
            raise ValueError("duration_seconds must be finite and non-negative.")
        if self.attempt < 1:
            raise ValueError("attempt must be positive.")
        if self.status == ExecutionStatus.FAILED and self.failure_class is None:
            raise ValueError("Failed records require a failure class.")


@dataclass(frozen=True)
class RunManifest:
    run_id: str
    plan_hash: str
    engine_version: str
    seed: int
    output_hashes: Mapping[str, str]
    records: tuple[ExecutionRecord, ...]
    completed: bool
    production_approval: bool = False
    regulatory_approval: bool = False
    boundary: str = OPERATIONAL_BOUNDARY

    def __post_init__(self) -> None:
        object.__setattr__(self, "run_id", _id(self.run_id, "run_id"))
        object.__setattr__(self, "plan_hash", _hash(self.plan_hash, "plan_hash"))
        object.__setattr__(self, "engine_version", _id(self.engine_version, "engine_version"))
        object.__setattr__(self, "output_hashes", _sorted_mapping(self.output_hashes, "output_hashes"))
        if self.production_approval or self.regulatory_approval:
            raise ValueError("Gate 6 does not grant production or regulatory approval.")
        if self.boundary != OPERATIONAL_BOUNDARY:
            raise ValueError("Run manifests must retain the quantitative-equivalence boundary.")


@dataclass(frozen=True)
class ReconciliationReport:
    status: str
    compared_values: int
    max_absolute_difference: float
    max_relative_difference: float
    tolerance: float
    mismatches: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.status not in {"PASS", "REMEDIATE"}:
            raise ValueError("Unsupported reconciliation status.")
        if self.compared_values < 0:
            raise ValueError("compared_values cannot be negative.")
        for name in ("max_absolute_difference", "max_relative_difference", "tolerance"):
            value = float(getattr(self, name))
            if not math.isfinite(value) or value < 0.0:
                raise ValueError(f"{name} must be finite and non-negative.")


@dataclass(frozen=True)
class ScalingPoint:
    trade_count: int
    path_count: int
    chunk_size: int
    workers: int
    elapsed_seconds: float
    peak_bytes: int
    checksum: str
    within_budget: bool

    def __post_init__(self) -> None:
        if min(self.trade_count, self.path_count, self.chunk_size, self.workers) <= 0:
            raise ValueError("Scaling dimensions must be positive.")
        if not math.isfinite(self.elapsed_seconds) or self.elapsed_seconds < 0.0:
            raise ValueError("elapsed_seconds must be finite and non-negative.")
        if self.peak_bytes < 0:
            raise ValueError("peak_bytes cannot be negative.")
        object.__setattr__(self, "checksum", _hash(self.checksum, "checksum"))

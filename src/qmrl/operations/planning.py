"""Snapshot comparison and dependency-aware recalculation planning."""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from .dependency import DependencyGraph
from .domain import ChangeSet, OperationalSnapshot, RecalculationPlan
from .fingerprint import content_hash


def _changed_keys(previous: dict[str, str], current: dict[str, str]) -> tuple[str, ...]:
    return tuple(
        sorted(
            key
            for key in set(previous) | set(current)
            if previous.get(key) != current.get(key)
        )
    )


def compare_snapshots(
    previous: OperationalSnapshot,
    current: OperationalSnapshot,
) -> ChangeSet:
    previous_trades = dict(previous.trade_hashes)
    current_trades = dict(current.trade_hashes)
    added = tuple(sorted(set(current_trades) - set(previous_trades)))
    removed = tuple(sorted(set(previous_trades) - set(current_trades)))
    modified = tuple(
        sorted(
            key
            for key in set(previous_trades) & set(current_trades)
            if previous_trades[key] != current_trades[key]
        )
    )
    return ChangeSet(
        added_trades=added,
        removed_trades=removed,
        modified_trades=modified,
        market_factors=_changed_keys(dict(previous.market_hashes), dict(current.market_hashes)),
        policies=_changed_keys(dict(previous.policy_hashes), dict(current.policy_hashes)),
        graph_changed=previous.graph_hash != current.graph_hash,
    )


def _roots_for_changes(changes: ChangeSet) -> dict[str, set[str]]:
    roots: dict[str, set[str]] = defaultdict(set)
    trade_changes = (
        changes.added_trades + changes.removed_trades + changes.modified_trades
    )
    if trade_changes:
        roots["portfolio_ingestion"].update(f"trade:{value}" for value in trade_changes)
    if changes.market_factors:
        roots["market_state"].update(f"market:{value}" for value in changes.market_factors)
    if changes.policies:
        roots["policy_state"].update(f"policy:{value}" for value in changes.policies)
    return roots


def build_recalculation_plan(
    graph: DependencyGraph,
    changes: ChangeSet,
) -> RecalculationPlan:
    if changes.is_empty:
        payload = {
            "graph_hash": graph.graph_hash,
            "nodes": (),
            "reasons": {},
            "affected_scopes": (),
            "full_recalculation": False,
        }
        return RecalculationPlan(
            node_ids=(),
            reasons={},
            affected_scopes=(),
            full_recalculation=False,
            plan_hash=content_hash(payload),
        )

    if changes.graph_changed:
        nodes = graph.order
        reasons = {node_id: ("graph:topology",) for node_id in nodes}
        full = True
    else:
        root_reasons = _roots_for_changes(changes)
        impacted: set[str] = set()
        reasons_map: dict[str, set[str]] = defaultdict(set)
        for root, reasons_for_root in root_reasons.items():
            descendants = graph.descendants((root,))
            impacted.update(descendants)
            for node_id in descendants:
                reasons_map[node_id].update(reasons_for_root)
        nodes = tuple(node_id for node_id in graph.order if node_id in impacted)
        reasons = {
            node_id: tuple(sorted(reasons_map[node_id]))
            for node_id in nodes
        }
        full = set(nodes) == set(graph.node_ids)

    payload = {
        "graph_hash": graph.graph_hash,
        "nodes": nodes,
        "reasons": reasons,
        "affected_scopes": changes.affected_scopes,
        "full_recalculation": full,
    }
    return RecalculationPlan(
        node_ids=nodes,
        reasons=reasons,
        affected_scopes=changes.affected_scopes,
        full_recalculation=full,
        plan_hash=content_hash(payload),
    )


def validate_plan(graph: DependencyGraph, plan: RecalculationPlan) -> None:
    unknown = set(plan.node_ids) - set(graph.node_ids)
    if unknown:
        raise ValueError(f"Plan references unknown nodes: {sorted(unknown)}.")
    ordered = tuple(node_id for node_id in graph.order if node_id in set(plan.node_ids))
    if ordered != plan.node_ids:
        raise ValueError("Recalculation plan is not in deterministic topological order.")
    selected = set(plan.node_ids)
    for node_id in plan.node_ids:
        for dependency in graph.node(node_id).dependencies:
            if dependency not in selected:
                # Reuse is permitted, but only from a completed baseline or valid cache.
                continue

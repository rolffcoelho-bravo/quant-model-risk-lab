from __future__ import annotations

import pytest

from qmrl.operations import (
    ChangeSet,
    DependencyGraph,
    DependencyNode,
    build_recalculation_plan,
    compare_snapshots,
    reference_graph,
)
from v1_4_gate6_helpers import digest, snapshot


def test_reference_graph_is_topologically_ordered():
    graph = reference_graph()
    positions = {node_id: index for index, node_id in enumerate(graph.order)}
    for node_id in graph.order:
        for dependency in graph.node(node_id).dependencies:
            assert positions[dependency] < positions[node_id]


def test_dependency_cycle_is_rejected():
    with pytest.raises(ValueError, match="cycle"):
        DependencyGraph(
            (
                DependencyNode("a", ("b",)),
                DependencyNode("b", ("a",)),
            )
        )


def test_snapshot_comparison_classifies_changes():
    previous = snapshot()
    current = snapshot(
        snapshot_id="current",
        trades={"T1": digest({"T1": 2.0}), "T2": digest({"T2": 1.0})},
        markets={"USD": digest({"USD": 2.0})},
        policies={"margin": digest({"margin": 1.0}), "capital": digest({"capital": 1.0})},
    )
    changes = compare_snapshots(previous, current)
    assert changes.added_trades == ("T2",)
    assert changes.modified_trades == ("T1",)
    assert changes.market_factors == ("USD",)
    assert changes.policies == ("capital",)


def test_trade_change_propagates_to_all_quantitative_descendants():
    graph = reference_graph()
    plan = build_recalculation_plan(
        graph,
        ChangeSet(modified_trades=("T1",)),
    )
    assert plan.node_ids[0] == "portfolio_ingestion"
    assert "exposure" in plan.node_ids
    assert "mva" in plan.node_ids
    assert "kva" in plan.node_ids
    assert "allocation" in plan.node_ids


def test_graph_change_forces_full_recalculation():
    graph = reference_graph()
    plan = build_recalculation_plan(graph, ChangeSet(graph_changed=True))
    assert plan.full_recalculation
    assert plan.node_ids == graph.order
    assert all(plan.reasons[node_id] == ("graph:topology",) for node_id in graph.order)


def test_no_change_produces_empty_plan():
    graph = reference_graph()
    plan = build_recalculation_plan(graph, ChangeSet())
    assert plan.node_ids == ()
    assert not plan.full_recalculation
    assert len(plan.plan_hash) == 64

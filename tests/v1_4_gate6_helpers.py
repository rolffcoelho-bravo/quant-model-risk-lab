from __future__ import annotations

from pathlib import Path
from typing import Any

from qmrl.operations import (
    ChangeSet,
    DependencyGraph,
    DependencyNode,
    OperationalSnapshot,
    RecalculationPlan,
    content_hash,
)


def digest(value: Any) -> str:
    return content_hash(value)


def simple_graph() -> DependencyGraph:
    return DependencyGraph(
        (
            DependencyNode("input_a"),
            DependencyNode("input_b"),
            DependencyNode("double", ("input_a",)),
            DependencyNode("total", ("double", "input_b")),
        )
    )


def simple_functions():
    return {
        "input_a": lambda dependencies, payload, seed: {"value": float(payload["value"])},
        "input_b": lambda dependencies, payload, seed: {"value": float(payload["value"])},
        "double": lambda dependencies, payload, seed: {
            "value": 2.0 * float(dependencies["input_a"]["value"])
        },
        "total": lambda dependencies, payload, seed: {
            "value": float(dependencies["double"]["value"])
            + float(dependencies["input_b"]["value"])
        },
    }


def full_plan(graph: DependencyGraph) -> RecalculationPlan:
    reasons = {node_id: ("test:full",) for node_id in graph.order}
    payload = {
        "nodes": graph.order,
        "reasons": reasons,
        "scopes": ("test:full",),
        "full": True,
    }
    return RecalculationPlan(
        node_ids=graph.order,
        reasons=reasons,
        affected_scopes=("test:full",),
        full_recalculation=True,
        plan_hash=digest(payload),
    )


def partial_plan(graph: DependencyGraph) -> RecalculationPlan:
    nodes = tuple(node_id for node_id in graph.order if node_id in {"input_a", "double", "total"})
    reasons = {node_id: ("trade:T1",) for node_id in nodes}
    payload = {
        "nodes": nodes,
        "reasons": reasons,
        "scopes": ("trade:T1",),
        "full": False,
    }
    return RecalculationPlan(
        node_ids=nodes,
        reasons=reasons,
        affected_scopes=("trade:T1",),
        full_recalculation=False,
        plan_hash=digest(payload),
    )


def snapshot(
    *,
    snapshot_id: str = "snapshot",
    trades: dict[str, str] | None = None,
    markets: dict[str, str] | None = None,
    policies: dict[str, str] | None = None,
    graph_hash: str | None = None,
) -> OperationalSnapshot:
    trade_values = trades or {"T1": digest({"T1": 1.0})}
    market_values = markets or {"USD": digest({"USD": 1.0})}
    policy_values = policies or {"margin": digest({"margin": 1.0})}
    return OperationalSnapshot(
        snapshot_id=snapshot_id,
        portfolio_hash=digest(trade_values),
        trade_hashes=trade_values,
        market_hashes=market_values,
        policy_hashes=policy_values,
        graph_hash=graph_hash or digest({"graph": "v1"}),
        engine_version="1.4-gate6",
    )


def write_gate_sequence(root: Path) -> None:
    path = root / "configs/v1_4_gate_sequence.yml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        """schema_version: "1.0"
release_line: "v1.4"
status: "ARCHITECTURE_FROZEN"
required_order: [0, 1, 2, 3, 4, 5, 6, 7, 8]
gates:
  - gate: 6
    depends_on: [5]
    target_status: "OPERATIONAL_SCALE_VALIDATED"
""",
        encoding="utf-8",
    )

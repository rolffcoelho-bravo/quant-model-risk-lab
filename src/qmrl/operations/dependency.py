"""Dependency graph validation and impact propagation."""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable, Sequence

from .domain import DependencyNode
from .fingerprint import content_hash


class DependencyGraph:
    def __init__(self, nodes: Sequence[DependencyNode]) -> None:
        if not nodes:
            raise ValueError("A dependency graph requires at least one node.")
        self._nodes = {node.node_id: node for node in nodes}
        if len(self._nodes) != len(nodes):
            raise ValueError("Dependency node identifiers must be unique.")
        for node in nodes:
            missing = set(node.dependencies) - set(self._nodes)
            if missing:
                raise ValueError(
                    f"Node {node.node_id!r} references missing dependencies: {sorted(missing)}."
                )
        self._order = self._topological_order()
        children: dict[str, set[str]] = defaultdict(set)
        for node in nodes:
            for dependency in node.dependencies:
                children[dependency].add(node.node_id)
        self._children = {key: tuple(sorted(value)) for key, value in children.items()}

    def _topological_order(self) -> tuple[str, ...]:
        indegree = {node_id: len(node.dependencies) for node_id, node in self._nodes.items()}
        children: dict[str, list[str]] = defaultdict(list)
        for node in self._nodes.values():
            for dependency in node.dependencies:
                children[dependency].append(node.node_id)
        ready = sorted(node_id for node_id, degree in indegree.items() if degree == 0)
        order: list[str] = []
        while ready:
            node_id = ready.pop(0)
            order.append(node_id)
            for child in sorted(children[node_id]):
                indegree[child] -= 1
                if indegree[child] == 0:
                    ready.append(child)
                    ready.sort()
        if len(order) != len(self._nodes):
            raise ValueError("Dependency graph contains a cycle.")
        return tuple(order)

    @property
    def order(self) -> tuple[str, ...]:
        return self._order

    @property
    def node_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._nodes))

    @property
    def graph_hash(self) -> str:
        return content_hash(
            [
                {
                    "node_id": node_id,
                    "dependencies": self._nodes[node_id].dependencies,
                    "cacheable": self._nodes[node_id].cacheable,
                    "quantitative": self._nodes[node_id].quantitative,
                    "scope": self._nodes[node_id].scope,
                }
                for node_id in self._order
            ]
        )

    def node(self, node_id: str) -> DependencyNode:
        try:
            return self._nodes[node_id]
        except KeyError as exc:
            raise KeyError(f"Unknown dependency node: {node_id}.") from exc

    def descendants(self, node_ids: Iterable[str], *, include_roots: bool = True) -> tuple[str, ...]:
        roots = tuple(node_ids)
        unknown = set(roots) - set(self._nodes)
        if unknown:
            raise KeyError(f"Unknown impact roots: {sorted(unknown)}.")
        visited = set(roots if include_roots else ())
        queue = list(roots)
        while queue:
            current = queue.pop(0)
            for child in self._children.get(current, ()):
                if child not in visited:
                    visited.add(child)
                    queue.append(child)
        return tuple(node_id for node_id in self._order if node_id in visited)

    def ancestors(self, node_id: str, *, include_node: bool = False) -> tuple[str, ...]:
        self.node(node_id)
        visited = {node_id} if include_node else set()
        queue = list(self.node(node_id).dependencies)
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            queue.extend(self.node(current).dependencies)
        return tuple(value for value in self._order if value in visited)


def reference_graph() -> DependencyGraph:
    """Return the governed v1.4 operational dependency graph."""

    return DependencyGraph(
        (
            DependencyNode("portfolio_ingestion", (), scope="portfolio"),
            DependencyNode("market_state", (), scope="market"),
            DependencyNode("policy_state", (), scope="policy"),
            DependencyNode(
                "fx_conversion",
                ("portfolio_ingestion", "market_state"),
                scope="currency",
            ),
            DependencyNode(
                "exposure",
                ("fx_conversion", "policy_state"),
                scope="netting_set",
            ),
            DependencyNode(
                "credit_funding_xva",
                ("exposure", "market_state", "policy_state"),
                scope="netting_set",
            ),
            DependencyNode(
                "initial_margin",
                ("exposure", "policy_state"),
                scope="netting_set",
            ),
            DependencyNode(
                "mva",
                ("initial_margin", "market_state", "policy_state"),
                scope="netting_set",
            ),
            DependencyNode(
                "capital_profile",
                ("exposure", "policy_state"),
                scope="netting_set",
            ),
            DependencyNode(
                "kva",
                ("capital_profile", "market_state", "policy_state"),
                scope="netting_set",
            ),
            DependencyNode(
                "total_xva",
                ("credit_funding_xva", "mva", "kva"),
                scope="portfolio",
            ),
            DependencyNode(
                "allocation",
                ("total_xva", "portfolio_ingestion", "policy_state"),
                scope="trade",
            ),
        )
    )

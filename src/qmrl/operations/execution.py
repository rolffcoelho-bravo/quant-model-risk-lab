"""Cache-aware, checkpointed, dependency-ordered execution."""

from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Any, Callable, Mapping

from .cache import FileCache
from .checkpoint import CheckpointStore
from .dependency import DependencyGraph
from .domain import (
    ExecutionRecord,
    ExecutionStatus,
    FailureClass,
    RecalculationPlan,
    RunManifest,
)
from .fingerprint import (
    content_hash,
    deterministic_cache_key,
    deterministic_run_id,
)
from .planning import validate_plan


NodeFunction = Callable[[Mapping[str, Any], Any, int], Any]


@dataclass(frozen=True)
class ExecutionResult:
    outputs: Mapping[str, Any]
    manifest: RunManifest


def _failure_class(exc: Exception) -> FailureClass:
    if isinstance(exc, MemoryError):
        return FailureClass.RESOURCE
    if isinstance(exc, (ValueError, TypeError, KeyError)):
        return FailureClass.INPUT
    return FailureClass.EXECUTION


class ExecutionEngine:
    def __init__(
        self,
        graph: DependencyGraph,
        functions: Mapping[str, NodeFunction],
        *,
        cache: FileCache | None = None,
        engine_version: str = "1.4-gate6",
    ) -> None:
        missing = set(graph.node_ids) - set(functions)
        if missing:
            raise ValueError(f"Missing node functions: {sorted(missing)}.")
        self.graph = graph
        self.functions = dict(functions)
        self.cache = cache
        self.engine_version = engine_version.strip()
        if not self.engine_version:
            raise ValueError("engine_version cannot be empty.")

    def execute(
        self,
        plan: RecalculationPlan,
        *,
        node_inputs: Mapping[str, Any],
        baseline_outputs: Mapping[str, Any] | None = None,
        policy_hashes: Mapping[str, str] | None = None,
        seed: int = 0,
        run_id: str | None = None,
        checkpoint_store: CheckpointStore | None = None,
        use_cache: bool = True,
    ) -> ExecutionResult:
        validate_plan(self.graph, plan)
        selected = set(plan.node_ids)
        outputs: dict[str, Any] = dict(baseline_outputs or {})
        policy_hashes = dict(policy_hashes or {})
        run_id = run_id or deterministic_run_id(plan.plan_hash, self.engine_version, seed)
        if checkpoint_store is not None:
            try:
                checkpoint_store.load(run_id)
            except FileNotFoundError:
                checkpoint_store.initialize(run_id, plan.plan_hash, plan.node_ids)

        records: list[ExecutionRecord] = []
        for node_id in self.graph.order:
            node = self.graph.node(node_id)
            if node_id not in selected:
                if node_id not in outputs:
                    raise ValueError(
                        f"Partial recalculation requires baseline output for {node_id}."
                    )
                output_hash = content_hash(outputs[node_id])
                records.append(
                    ExecutionRecord(
                        node_id=node_id,
                        status=ExecutionStatus.REUSED,
                        input_hash=content_hash({"baseline": node_id}),
                        output_hash=output_hash,
                        cache_key=content_hash({"baseline": node_id, "output": output_hash}),
                        duration_seconds=0.0,
                    )
                )
                continue

            dependencies = {
                dependency: outputs[dependency]
                for dependency in node.dependencies
            }
            external_input = node_inputs.get(node_id, {})
            input_hash = content_hash(
                {"dependencies": dependencies, "external_input": external_input}
            )
            policy_hash = policy_hashes.get(node_id, content_hash({"policy": node_id}))
            dependency_hashes = {
                dependency: content_hash(value)
                for dependency, value in dependencies.items()
            }
            key = deterministic_cache_key(
                node_id=node_id,
                dependency_hashes=dependency_hashes,
                external_input=external_input,
                policy_hash=policy_hash,
                engine_version=self.engine_version,
                seed=seed,
                scope=node.scope,
            )
            metadata = {
                "node_id": node_id,
                "input_hash": input_hash,
                "policy_hash": policy_hash,
                "engine_version": self.engine_version,
                "seed": int(seed),
            }

            start = time.perf_counter()
            if self.cache is not None and use_cache and node.cacheable:
                lookup = self.cache.get(key, expected_metadata=metadata)
            else:
                lookup = None

            if lookup is not None and lookup.status == "HIT":
                output = lookup.value
                output_hash = lookup.output_hash
                status = ExecutionStatus.CACHE_HIT
            else:
                try:
                    output = self.functions[node_id](dependencies, external_input, int(seed))
                    output_hash = content_hash(output)
                    if self.cache is not None and use_cache and node.cacheable:
                        cached_hash = self.cache.put(key, output, metadata)
                        if cached_hash != output_hash:
                            raise RuntimeError("Cache output hash changed during persistence.")
                    status = ExecutionStatus.COMPLETE
                except Exception as exc:
                    duration = max(0.0, time.perf_counter() - start)
                    record = ExecutionRecord(
                        node_id=node_id,
                        status=ExecutionStatus.FAILED,
                        input_hash=input_hash,
                        output_hash="",
                        cache_key=key,
                        duration_seconds=duration,
                        failure_class=_failure_class(exc),
                        message=str(exc),
                    )
                    records.append(record)
                    if checkpoint_store is not None:
                        checkpoint_store.mark_node(
                            run_id,
                            node_id,
                            "FAILED",
                            failure=f"{record.failure_class.value}:{record.message}",
                        )
                    raise

            outputs[node_id] = output
            duration = max(0.0, time.perf_counter() - start)
            records.append(
                ExecutionRecord(
                    node_id=node_id,
                    status=status,
                    input_hash=input_hash,
                    output_hash=output_hash,
                    cache_key=key,
                    duration_seconds=duration,
                )
            )
            if checkpoint_store is not None:
                checkpoint_store.mark_node(
                    run_id,
                    node_id,
                    "COMPLETE",
                    output_hash=output_hash,
                )

        output_hashes = {
            node_id: content_hash(outputs[node_id])
            for node_id in self.graph.order
        }
        manifest = RunManifest(
            run_id=run_id,
            plan_hash=plan.plan_hash,
            engine_version=self.engine_version,
            seed=int(seed),
            output_hashes=output_hashes,
            records=tuple(records),
            completed=True,
        )
        return ExecutionResult(outputs=dict(outputs), manifest=manifest)

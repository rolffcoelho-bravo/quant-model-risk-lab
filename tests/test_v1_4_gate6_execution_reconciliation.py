from __future__ import annotations

import pytest

from qmrl.operations import (
    ExecutionEngine,
    ExecutionStatus,
    FileCache,
    RecalculationPlan,
    reconcile_outputs,
)
from v1_4_gate6_helpers import (
    digest,
    full_plan,
    partial_plan,
    simple_functions,
    simple_graph,
)


def test_full_execution_follows_dependency_order():
    graph = simple_graph()
    engine = ExecutionEngine(graph, simple_functions())
    result = engine.execute(
        full_plan(graph),
        node_inputs={"input_a": {"value": 3.0}, "input_b": {"value": 4.0}},
    )
    assert result.outputs["total"]["value"] == 10.0
    assert tuple(record.node_id for record in result.manifest.records) == graph.order


def test_second_execution_uses_validated_cache(tmp_path):
    graph = simple_graph()
    engine = ExecutionEngine(graph, simple_functions(), cache=FileCache(tmp_path))
    kwargs = {
        "node_inputs": {"input_a": {"value": 2.0}, "input_b": {"value": 5.0}},
        "seed": 11,
    }
    engine.execute(full_plan(graph), **kwargs)
    second = engine.execute(full_plan(graph), **kwargs)
    assert all(
        record.status == ExecutionStatus.CACHE_HIT
        for record in second.manifest.records
    )


def test_partial_recalculation_matches_changed_full_revaluation():
    graph = simple_graph()
    engine = ExecutionEngine(graph, simple_functions())
    base = engine.execute(
        full_plan(graph),
        node_inputs={"input_a": {"value": 2.0}, "input_b": {"value": 5.0}},
    )
    partial = engine.execute(
        partial_plan(graph),
        node_inputs={"input_a": {"value": 4.0}},
        baseline_outputs=base.outputs,
    )
    changed_full = engine.execute(
        full_plan(graph),
        node_inputs={"input_a": {"value": 4.0}, "input_b": {"value": 5.0}},
    )
    report = reconcile_outputs(partial.outputs, changed_full.outputs)
    assert report.status == "PASS"
    assert partial.outputs["total"]["value"] == 13.0


def test_partial_recalculation_blocks_missing_baseline():
    graph = simple_graph()
    engine = ExecutionEngine(graph, simple_functions())
    with pytest.raises(ValueError, match="baseline output"):
        engine.execute(
            partial_plan(graph),
            node_inputs={"input_a": {"value": 4.0}},
            baseline_outputs={},
        )


def test_node_failure_is_checkpointed_and_re_raised(tmp_path):
    graph = simple_graph()
    functions = simple_functions()
    functions["double"] = lambda dependencies, payload, seed: (_ for _ in ()).throw(ValueError("bad input"))
    engine = ExecutionEngine(graph, functions)
    from qmrl.operations import CheckpointStore
    store = CheckpointStore(tmp_path)
    plan = full_plan(graph)
    with pytest.raises(ValueError, match="bad input"):
        engine.execute(
            plan,
            node_inputs={"input_a": {"value": 2.0}, "input_b": {"value": 5.0}},
            checkpoint_store=store,
            run_id="failure-run",
        )
    state = store.load("failure-run")
    assert state.node_status["double"] == "FAILED"
    assert "INPUT:bad input" in state.failures["double"]


def test_deterministic_run_identity_ignores_wall_clock_time():
    graph = simple_graph()
    engine = ExecutionEngine(graph, simple_functions())
    plan = full_plan(graph)
    first = engine.execute(
        plan,
        node_inputs={"input_a": {"value": 1.0}, "input_b": {"value": 2.0}},
        seed=9,
    )
    second = engine.execute(
        plan,
        node_inputs={"input_a": {"value": 1.0}, "input_b": {"value": 2.0}},
        seed=9,
    )
    assert first.manifest.run_id == second.manifest.run_id
    assert first.manifest.output_hashes == second.manifest.output_hashes

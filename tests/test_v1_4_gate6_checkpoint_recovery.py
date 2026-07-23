from __future__ import annotations

import json

import pytest

from qmrl.operations import CheckpointStore
from v1_4_gate6_helpers import digest


def test_checkpoint_initialization_records_pending_work(tmp_path):
    store = CheckpointStore(tmp_path)
    state = store.initialize(
        "run-1",
        digest({"plan": 1}),
        ("a", "b"),
        ("chunk-1", "chunk-2"),
    )
    assert state.pending_nodes == ("a", "b")
    assert state.pending_chunks == ("chunk-1", "chunk-2")


def test_completed_node_is_removed_from_pending_work(tmp_path):
    store = CheckpointStore(tmp_path)
    store.initialize("run-2", digest({"plan": 2}), ("a", "b"))
    state = store.mark_node("run-2", "a", "COMPLETE", output_hash=digest({"a": 1}))
    assert state.pending_nodes == ("b",)
    assert state.node_output_hashes["a"] == digest({"a": 1})


def test_completed_chunk_is_removed_from_pending_work(tmp_path):
    store = CheckpointStore(tmp_path)
    store.initialize("run-3", digest({"plan": 3}), (), ("chunk-1", "chunk-2"))
    state = store.mark_chunk("run-3", "chunk-1", "COMPLETE")
    assert state.pending_chunks == ("chunk-2",)


def test_interrupted_run_recovers_only_pending_nodes(tmp_path):
    store = CheckpointStore(tmp_path)
    store.initialize("run-4", digest({"plan": 4}), ("a", "b", "c"))
    store.mark_node("run-4", "a", "COMPLETE", output_hash=digest({"a": 1}))
    store.mark_node("run-4", "b", "FAILED", failure="RESOURCE:memory")
    state = store.load("run-4")
    assert state.pending_nodes == ("b", "c")
    assert state.failures["b"] == "RESOURCE:memory"


def test_unknown_checkpoint_work_is_blocked(tmp_path):
    store = CheckpointStore(tmp_path)
    store.initialize("run-5", digest({"plan": 5}), ("a",))
    with pytest.raises(KeyError, match="Unknown checkpoint node"):
        store.mark_node("run-5", "missing", "COMPLETE", output_hash=digest({"x": 1}))


def test_corrupt_checkpoint_is_rejected(tmp_path):
    store = CheckpointStore(tmp_path)
    store.initialize("run-6", digest({"plan": 6}), ("a",))
    path = tmp_path / "run-6.json"
    envelope = json.loads(path.read_text(encoding="utf-8"))
    envelope["payload"]["node_status"]["a"] = "COMPLETE"
    path.write_text(json.dumps(envelope), encoding="utf-8")
    with pytest.raises(ValueError, match="hash mismatch"):
        store.load("run-6")

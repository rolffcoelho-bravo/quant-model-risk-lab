from __future__ import annotations

import math

import pytest

from qmrl.operations import (
    aggregate_chunk_outputs,
    deterministic_chunks,
    execute_chunks,
    output_map,
)


def worker(item_id: str, value: float, seed: int) -> float:
    return value * 2.0 + (seed % 13) * 1.0e-6


def test_chunk_partition_is_deterministic():
    items = {"c": 3.0, "a": 1.0, "b": 2.0}
    first = deterministic_chunks(items, 2)
    second = deterministic_chunks(dict(reversed(list(items.items()))), 2)
    assert first == second
    assert first[0].items == (("a", 1.0), ("b", 2.0))


def test_chunk_partition_has_no_duplicates_or_omissions():
    items = {f"T{index}": float(index) for index in range(17)}
    chunks = deterministic_chunks(items, 4)
    identifiers = [item_id for chunk in chunks for item_id, _ in chunk.items]
    assert len(identifiers) == len(set(identifiers)) == len(items)
    assert set(identifiers) == set(items)


def test_sequential_and_parallel_outputs_are_identical():
    items = {f"T{index:03d}": float(index + 1) for index in range(40)}
    chunks = deterministic_chunks(items, 7)
    sequential = execute_chunks(chunks, worker, seed=23, max_workers=1)
    parallel = execute_chunks(chunks, worker, seed=23, max_workers=4)
    assert sequential == parallel


def test_aggregation_uses_all_chunk_outputs():
    chunks = deterministic_chunks({"a": 1.0, "b": 2.0, "c": 3.0}, 2)
    outputs = execute_chunks(chunks, lambda i, v, s: v, seed=0)
    assert aggregate_chunk_outputs(outputs) == math.fsum((1.0, 2.0, 3.0))
    assert output_map(outputs) == {"a": 1.0, "b": 2.0, "c": 3.0}


def test_item_seed_is_reproducible_and_seed_sensitive():
    chunks = deterministic_chunks({"a": 1.0, "b": 2.0}, 1)
    first = execute_chunks(chunks, worker, seed=1)
    repeated = execute_chunks(chunks, worker, seed=1)
    changed = execute_chunks(chunks, worker, seed=2)
    assert first == repeated
    assert first != changed


def test_invalid_chunk_or_worker_count_is_blocked():
    with pytest.raises(ValueError, match="chunk_size"):
        deterministic_chunks({"a": 1.0}, 0)
    chunks = deterministic_chunks({"a": 1.0}, 1)
    with pytest.raises(ValueError, match="max_workers"):
        execute_chunks(chunks, worker, max_workers=0)

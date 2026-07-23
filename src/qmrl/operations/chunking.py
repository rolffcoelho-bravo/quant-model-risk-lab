"""Deterministic chunking and reproducible parallel execution."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import hashlib
import math
from typing import Callable, Mapping

from .fingerprint import content_hash


@dataclass(frozen=True)
class WorkChunk:
    chunk_id: str
    items: tuple[tuple[str, float], ...]


@dataclass(frozen=True)
class ChunkOutput:
    chunk_id: str
    values: tuple[tuple[str, float], ...]
    checksum: str


def deterministic_chunks(
    items: Mapping[str, float],
    chunk_size: int,
) -> tuple[WorkChunk, ...]:
    if int(chunk_size) <= 0:
        raise ValueError("chunk_size must be positive.")
    ordered = tuple(sorted((str(key), float(value)) for key, value in items.items()))
    if any(not key for key, _ in ordered):
        raise ValueError("Work item identifiers cannot be empty.")
    if any(not math.isfinite(value) for _, value in ordered):
        raise ValueError("Work values must be finite.")
    chunks = []
    for index in range(0, len(ordered), int(chunk_size)):
        chunk_index = index // int(chunk_size)
        chunks.append(WorkChunk(f"chunk-{chunk_index:06d}", ordered[index:index + int(chunk_size)]))
    return tuple(chunks)


def _item_seed(seed: int, item_id: str) -> int:
    digest = hashlib.sha256(f"{int(seed)}:{item_id}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big", signed=False)


def execute_chunks(
    chunks: tuple[WorkChunk, ...],
    worker: Callable[[str, float, int], float],
    *,
    seed: int = 0,
    max_workers: int = 1,
) -> tuple[ChunkOutput, ...]:
    if int(max_workers) <= 0:
        raise ValueError("max_workers must be positive.")
    if len({chunk.chunk_id for chunk in chunks}) != len(chunks):
        raise ValueError("Chunk identifiers must be unique.")

    def execute(chunk: WorkChunk) -> ChunkOutput:
        values = tuple(
            (
                item_id,
                float(worker(item_id, value, _item_seed(seed, item_id))),
            )
            for item_id, value in chunk.items
        )
        if any(not math.isfinite(value) for _, value in values):
            raise ValueError("Chunk worker returned a non-finite value.")
        return ChunkOutput(chunk.chunk_id, values, content_hash(values))

    if int(max_workers) == 1:
        results = [execute(chunk) for chunk in chunks]
    else:
        with ThreadPoolExecutor(max_workers=int(max_workers)) as executor:
            results = list(executor.map(execute, chunks))
    return tuple(sorted(results, key=lambda result: result.chunk_id))


def aggregate_chunk_outputs(outputs: tuple[ChunkOutput, ...]) -> float:
    values: list[tuple[str, float]] = []
    for output in outputs:
        if content_hash(output.values) != output.checksum:
            raise ValueError(f"Chunk checksum mismatch: {output.chunk_id}.")
        values.extend(output.values)
    identifiers = [item_id for item_id, _ in values]
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("A work item appeared in multiple chunks.")
    return math.fsum(value for _, value in sorted(values))


def output_map(outputs: tuple[ChunkOutput, ...]) -> dict[str, float]:
    result: dict[str, float] = {}
    for output in outputs:
        for item_id, value in output.values:
            if item_id in result:
                raise ValueError(f"Duplicate output item: {item_id}.")
            result[item_id] = value
    return dict(sorted(result.items()))

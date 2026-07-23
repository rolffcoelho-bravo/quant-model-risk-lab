"""Measured runtime and peak-memory evidence for deterministic synthetic workloads."""

from __future__ import annotations

import math
import time
import tracemalloc
from typing import Iterable

from .chunking import (
    aggregate_chunk_outputs,
    deterministic_chunks,
    execute_chunks,
)
from .domain import ScalingPoint
from .fingerprint import content_hash


def benchmark_worker(item_id: str, value: float, seed: int, path_count: int) -> float:
    accumulator = 0.0
    seed_scale = 1.0 + (seed % 101) * 1.0e-7
    for path_index in range(path_count):
        accumulator += (
            value * seed_scale / (path_index + 1.0)
            + math.sin((path_index + 1.0) * 0.001 + value * 1.0e-6)
        )
    return accumulator


def run_scaling_benchmark(
    *,
    trade_counts: Iterable[int] = (100, 500),
    path_counts: Iterable[int] = (10, 50),
    chunk_size: int = 100,
    workers: int = 1,
    max_seconds: float = 30.0,
    max_peak_bytes: int = 256_000_000,
    seed: int = 17,
) -> tuple[ScalingPoint, ...]:
    if max_seconds <= 0.0 or max_peak_bytes <= 0:
        raise ValueError("Performance budgets must be positive.")
    points: list[ScalingPoint] = []
    for trade_count in tuple(int(value) for value in trade_counts):
        for path_count in tuple(int(value) for value in path_counts):
            if trade_count <= 0 or path_count <= 0:
                raise ValueError("Benchmark dimensions must be positive.")
            items = {
                f"trade-{index:07d}": float(index + 1)
                for index in range(trade_count)
            }
            chunks = deterministic_chunks(items, chunk_size)
            tracemalloc.start()
            start = time.perf_counter()
            outputs = execute_chunks(
                chunks,
                lambda item_id, value, item_seed: benchmark_worker(
                    item_id, value, item_seed, path_count
                ),
                seed=seed,
                max_workers=workers,
            )
            aggregate = aggregate_chunk_outputs(outputs)
            elapsed = max(0.0, time.perf_counter() - start)
            _, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            checksum = content_hash(
                {
                    "trade_count": trade_count,
                    "path_count": path_count,
                    "aggregate": aggregate,
                    "chunk_checksums": [output.checksum for output in outputs],
                }
            )
            points.append(
                ScalingPoint(
                    trade_count=trade_count,
                    path_count=path_count,
                    chunk_size=chunk_size,
                    workers=workers,
                    elapsed_seconds=elapsed,
                    peak_bytes=int(peak),
                    checksum=checksum,
                    within_budget=elapsed <= max_seconds and peak <= max_peak_bytes,
                )
            )
    return tuple(points)


def scaling_evidence(points: tuple[ScalingPoint, ...]) -> dict[str, object]:
    return {
        "status": "PASS" if points and all(point.within_budget for point in points) else "REMEDIATE",
        "point_count": len(points),
        "checksums": [point.checksum for point in points],
        "maximum_elapsed_seconds": max((point.elapsed_seconds for point in points), default=0.0),
        "maximum_peak_bytes": max((point.peak_bytes for point in points), default=0),
    }

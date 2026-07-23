"""Operational recalculation, performance, and scale controls for v1.4 Gate 6."""

from .benchmark import benchmark_worker, run_scaling_benchmark, scaling_evidence
from .cache import CacheLookup, FileCache
from .challenger import reconcile_output_hashes, reconcile_outputs
from .checkpoint import CheckpointState, CheckpointStore
from .chunking import (
    ChunkOutput,
    WorkChunk,
    aggregate_chunk_outputs,
    deterministic_chunks,
    execute_chunks,
    output_map,
)
from .dependency import DependencyGraph, reference_graph
from .domain import (
    ChangeKind,
    ChangeSet,
    DependencyNode,
    ExecutionRecord,
    ExecutionStatus,
    FailureClass,
    OperationalSnapshot,
    RecalculationPlan,
    ReconciliationReport,
    RunManifest,
    ScalingPoint,
    OPERATIONAL_BOUNDARY,
)
from .execution import ExecutionEngine, ExecutionResult
from .fingerprint import (
    canonical_data,
    canonical_json,
    content_hash,
    deterministic_cache_key,
    deterministic_run_id,
    normalized_text_hash,
)
from .planning import build_recalculation_plan, compare_snapshots, validate_plan

__all__ = [
    "CacheLookup",
    "ChangeKind",
    "ChangeSet",
    "CheckpointState",
    "CheckpointStore",
    "ChunkOutput",
    "DependencyGraph",
    "DependencyNode",
    "ExecutionEngine",
    "ExecutionRecord",
    "ExecutionResult",
    "ExecutionStatus",
    "FailureClass",
    "FileCache",
    "OPERATIONAL_BOUNDARY",
    "OperationalSnapshot",
    "RecalculationPlan",
    "ReconciliationReport",
    "RunManifest",
    "ScalingPoint",
    "WorkChunk",
    "aggregate_chunk_outputs",
    "benchmark_worker",
    "build_recalculation_plan",
    "canonical_data",
    "canonical_json",
    "compare_snapshots",
    "content_hash",
    "deterministic_cache_key",
    "deterministic_chunks",
    "deterministic_run_id",
    "execute_chunks",
    "normalized_text_hash",
    "output_map",
    "reconcile_output_hashes",
    "reconcile_outputs",
    "reference_graph",
    "run_scaling_benchmark",
    "scaling_evidence",
    "validate_plan",
]

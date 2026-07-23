from __future__ import annotations

from qmrl.operations import (
    reconcile_output_hashes,
    reconcile_outputs,
    run_scaling_benchmark,
    scaling_evidence,
)


def test_scaling_benchmark_records_trade_and_path_dimensions():
    points = run_scaling_benchmark(
        trade_counts=(5, 10),
        path_counts=(2, 4),
        chunk_size=3,
        workers=1,
    )
    assert len(points) == 4
    assert {(point.trade_count, point.path_count) for point in points} == {
        (5, 2), (5, 4), (10, 2), (10, 4)
    }


def test_scaling_benchmark_records_runtime_memory_and_budget():
    points = run_scaling_benchmark(
        trade_counts=(5,),
        path_counts=(2,),
        chunk_size=2,
        max_seconds=30.0,
        max_peak_bytes=256_000_000,
    )
    point = points[0]
    assert point.elapsed_seconds >= 0.0
    assert point.peak_bytes >= 0
    assert point.within_budget


def test_scaling_checksum_is_deterministic_across_worker_counts():
    sequential = run_scaling_benchmark(
        trade_counts=(20,),
        path_counts=(5,),
        chunk_size=4,
        workers=1,
        seed=19,
    )
    parallel = run_scaling_benchmark(
        trade_counts=(20,),
        path_counts=(5,),
        chunk_size=4,
        workers=3,
        seed=19,
    )
    assert sequential[0].checksum == parallel[0].checksum


def test_scaling_evidence_promotes_only_when_all_points_pass():
    points = run_scaling_benchmark(
        trade_counts=(5,),
        path_counts=(2,),
        chunk_size=2,
    )
    evidence = scaling_evidence(points)
    assert evidence["status"] == "PASS"
    assert evidence["point_count"] == 1


def test_independent_reconciliation_passes_within_tolerance():
    report = reconcile_outputs(
        {"x": [1.0, 2.0], "status": "ok"},
        {"x": [1.0 + 1.0e-12, 2.0], "status": "ok"},
        tolerance=1.0e-10,
    )
    assert report.status == "PASS"
    assert report.compared_values == 2


def test_independent_reconciliation_detects_hash_mismatch():
    report = reconcile_output_hashes(
        {"exposure": "a" * 64},
        {"exposure": "b" * 64},
    )
    assert report.status == "REMEDIATE"
    assert report.mismatches

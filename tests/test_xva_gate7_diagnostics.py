from __future__ import annotations

from qmrl.xva import benchmark_drift_score, detect_threshold_discontinuity, rank_sensitivity_drivers


def test_sensitivity_ranking_uses_absolute_magnitude() -> None:
    ranking = rank_sensitivity_drivers({"recovery": -4.0, "spread": 10.0, "funding": 2.0})
    assert ranking[0][0] == "spread"
    assert ranking[-1][0] == "funding"


def test_threshold_discontinuity_flags_large_jump() -> None:
    flags = detect_threshold_discontinuity([0.0, 1.0, 2.0, 3.0, 4.0], [10.0, 10.1, 10.2, 20.0, 20.1], jump_ratio_threshold=5.0)
    assert 2 in flags


def test_benchmark_drift_passes_locked_values() -> None:
    result = benchmark_drift_score([1.0, 2.0], [1.0, 2.0], absolute_tolerance=1e-10)
    assert result["status"] == "PASS"


def test_benchmark_drift_blocks_a_breach() -> None:
    result = benchmark_drift_score([1.0, 2.1], [1.0, 2.0], absolute_tolerance=0.01)
    assert result["status"] == "BLOCK"
    assert result["breach_count"] == 1

from __future__ import annotations

import pytest

from qmrl.xva import (
    StabilityThresholds,
    antithetic_comparison,
    path_count_convergence,
    seed_stability,
    time_grid_refinement,
)


THRESHOLDS = StabilityThresholds(
    soft_relative_change=0.03,
    hard_relative_change=0.10,
    soft_coefficient_of_variation=0.02,
    hard_coefficient_of_variation=0.08,
    minimum_observations=3,
)


def test_path_count_convergence_passes_for_stable_tail() -> None:
    result = path_count_convergence([1000, 5000, 20000, 80000], [100.0, 100.8, 100.4, 100.3], THRESHOLDS)
    assert result.status in {"PASS", "PASS_WITH_MONITORING"}


def test_seed_stability_blocks_large_dispersion() -> None:
    result = seed_stability([80.0, 120.0, 60.0, 140.0], THRESHOLDS)
    assert result.status == "BLOCK"


def test_time_grid_requires_decreasing_steps() -> None:
    with pytest.raises(ValueError):
        time_grid_refinement([0.1, 0.2, 0.05], [10.0, 10.0, 10.0], THRESHOLDS)


def test_time_grid_refinement_returns_governed_status() -> None:
    result = time_grid_refinement([0.25, 0.125, 0.0625, 0.03125], [50.0, 50.5, 50.3, 50.25], THRESHOLDS)
    assert result.status in {"PASS", "PASS_WITH_MONITORING"}


def test_antithetic_comparison_rewards_variance_reduction() -> None:
    result = antithetic_comparison([90.0, 110.0, 95.0, 105.0], [98.0, 102.0, 99.0, 101.0])
    assert result["variance_ratio"] < 1.0
    assert result["status"] == "PASS"

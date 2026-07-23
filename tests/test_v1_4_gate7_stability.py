from __future__ import annotations

import pytest

from qmrl.lifecycle_governance import (
    GovernanceStatus,
    classify_deviation,
    input_perturbation_stability,
    path_count_stability,
    seed_stability,
    sensitivity_ranking_stability,
    time_grid_stability,
)


def test_deviation_classification_boundaries():
    assert classify_deviation(0.01, 0.01, 0.05) == GovernanceStatus.PASS
    assert classify_deviation(0.02, 0.01, 0.05) == GovernanceStatus.PASS_WITH_MONITORING
    assert classify_deviation(0.06, 0.01, 0.05) == GovernanceStatus.BLOCK


def test_seed_stability_passes_for_close_estimates():
    observation = seed_stability({1: 100.0, 2: 100.1, 3: 99.9})
    assert observation.status == GovernanceStatus.PASS


def test_path_count_stability_uses_largest_path_count_as_reference():
    observation = path_count_stability({1000: 95.0, 10000: 99.0, 100000: 100.0})
    assert observation.baseline_value == 100.0
    assert observation.status == GovernanceStatus.PASS_WITH_MONITORING


def test_time_grid_stability_requires_reference_grid():
    with pytest.raises(ValueError, match="reference grid"):
        time_grid_stability({"monthly": 1.0, "weekly": 1.1}, "daily")


def test_direction_failure_blocks_perturbation():
    observation = input_perturbation_stability(label="funding", baseline=10.0, perturbed=9.0, expected_direction="increase")
    assert observation.status == GovernanceStatus.BLOCK


def test_sensitivity_ranking_stability_detects_rank_reversal():
    observation = sensitivity_ranking_stability(
        {"a": 3.0, "b": 2.0, "c": 1.0},
        {"a": 1.0, "b": 2.0, "c": 3.0},
    )
    assert observation.status == GovernanceStatus.BLOCK
    assert observation.challenged_value < 0.0

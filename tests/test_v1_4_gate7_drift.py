from __future__ import annotations

import pytest

from qmrl.lifecycle_governance import (
    GovernanceStatus,
    aggregate_drift,
    consecutive_monitoring_breach,
    population_stability_index,
    scalar_drift,
)


def test_scalar_drift_passes_small_change():
    observation = scalar_drift("cva", 100.0, 102.0)
    assert observation.status == GovernanceStatus.PASS


def test_scalar_drift_blocks_material_change():
    observation = scalar_drift("cva", 100.0, 140.0)
    assert observation.status == GovernanceStatus.BLOCK


def test_population_stability_index_is_zero_for_equal_distributions():
    observation = population_stability_index((0.2, 0.3, 0.5), (0.2, 0.3, 0.5))
    assert observation.current_value == pytest.approx(0.0)
    assert observation.status == GovernanceStatus.PASS


def test_population_stability_index_rejects_negative_mass():
    with pytest.raises(ValueError, match="non-negative"):
        population_stability_index((0.5, 0.5), (1.1, -0.1))


def test_aggregate_drift_returns_worst_status():
    observations = (
        scalar_drift("a", 100.0, 101.0),
        scalar_drift("b", 100.0, 140.0),
    )
    summary = aggregate_drift(observations)
    assert summary["status"] == "BLOCK"
    assert summary["block_count"] == 1


def test_consecutive_monitoring_breach_detection():
    observations = (
        scalar_drift("a", 100.0, 110.0),
        scalar_drift("a", 100.0, 112.0),
    )
    assert consecutive_monitoring_breach(observations, required_consecutive=2)

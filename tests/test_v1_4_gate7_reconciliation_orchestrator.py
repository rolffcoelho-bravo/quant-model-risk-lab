from __future__ import annotations

import pytest

from qmrl.lifecycle_governance import (
    ChallengeComponent,
    ChallengeOrchestrator,
    GovernanceStatus,
    component_reconciliation,
    default_registry,
    disagreement_matrix,
    reconcile_scalar,
    reconcile_series,
)


def test_scalar_reconciliation_passes_within_tolerance():
    spec = default_registry().get(ChallengeComponent.MULTICURRENCY)
    report = reconcile_scalar(run_id="r1", metric_name="ee", primary_value=1.0, challenger_value=1.0 + 1e-10, spec=spec)
    assert report.status == GovernanceStatus.PASS


def test_scalar_reconciliation_requires_remediation_above_tolerance():
    spec = default_registry().get(ChallengeComponent.MARGIN_MVA)
    report = reconcile_scalar(run_id="r2", metric_name="mva", primary_value=1.0, challenger_value=1.0 + 5e-6, spec=spec)
    assert report.status == GovernanceStatus.REMEDIATE


def test_scalar_reconciliation_blocks_material_disagreement():
    spec = default_registry().get(ChallengeComponent.CAPITAL_KVA)
    report = reconcile_scalar(run_id="r3", metric_name="kva", primary_value=1.0, challenger_value=2.0, spec=spec)
    assert report.status == GovernanceStatus.BLOCK
    assert report.material_blocks


def test_series_reconciliation_requires_aligned_vectors():
    spec = default_registry().get(ChallengeComponent.OPERATIONS)
    with pytest.raises(ValueError, match="aligned"):
        reconcile_series(run_id="r4", metric_name="profile", primary_values=(1, 2), challenger_values=(1,), spec=spec)


def test_component_reconciliation_and_disagreement_matrix():
    spec = default_registry().get(ChallengeComponent.INCREMENTAL_ALLOCATION)
    report = component_reconciliation("r5", {"cva": 1.0, "kva": 2.0}, {"cva": 1.0, "kva": 2.0}, spec)
    matrix = disagreement_matrix((report,))
    assert matrix[ChallengeComponent.INCREMENTAL_ALLOCATION.value]["status"] == "PASS"
    assert matrix[ChallengeComponent.INCREMENTAL_ALLOCATION.value]["finding_count"] == 2


def test_orchestrator_runs_registered_bundle_deterministically():
    registry = default_registry()
    values = {component: (1.0, 1.0, "total") for component in registry.components}
    reports = ChallengeOrchestrator(registry).run_scalar_bundle("bundle", values)
    assert tuple(report.component for report in reports) == registry.components
    assert all(report.status == GovernanceStatus.PASS for report in reports)

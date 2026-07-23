from __future__ import annotations

from qmrl.lifecycle_governance import (
    ChallengeComponent,
    ChallengeOrchestrator,
    DispositionRecord,
    default_registry,
    reconcile_scalar,
)


def complete_pass_reports(run_id: str = "gate7-pass"):
    registry = default_registry()
    reports = ChallengeOrchestrator(registry).run_scalar_bundle(
        run_id,
        {
            component: (100.0, 100.0, "total")
            for component in registry.components
        },
    )
    return registry, reports


def remediation_report():
    registry = default_registry()
    report = reconcile_scalar(
        run_id="gate7-remediation",
        metric_name="mva",
        primary_value=1.0,
        challenger_value=1.0 + 5.0e-6,
        spec=registry.get(ChallengeComponent.MARGIN_MVA),
    )
    return registry, report


def closed_disposition(report):
    return DispositionRecord(
        finding_id=report.findings[0].finding_id,
        owner="model-risk",
        action="independent numerical reconciliation",
        state="CLOSED",
        evidence_id="gate7-remediation-evidence",
        reviewed_by="human-reviewer",
    )

"""Primary-versus-challenger reconciliation and disagreement classification."""

from __future__ import annotations

import math
from typing import Mapping, Sequence

from .domain import (
    ChallengeComponent,
    ChallengeFinding,
    ChallengeReport,
    GovernanceStatus,
    evidence_sha256,
)
from .registry import ChallengerSpec


def _difference(primary: float, challenger: float) -> tuple[float, float]:
    first = float(primary)
    second = float(challenger)
    if not math.isfinite(first) or not math.isfinite(second):
        raise ValueError("Challenge values must be finite.")
    absolute = abs(first - second)
    relative = absolute / max(abs(first), abs(second), 1.0e-15)
    return absolute, relative


def _status(absolute: float, tolerance: float, materiality: float) -> GovernanceStatus:
    if absolute <= tolerance:
        return GovernanceStatus.PASS
    if absolute <= materiality:
        return GovernanceStatus.REMEDIATE
    return GovernanceStatus.BLOCK


def reconcile_scalar(
    *,
    run_id: str,
    metric_name: str,
    primary_value: float,
    challenger_value: float,
    spec: ChallengerSpec,
    evidence_ids: tuple[str, ...] = (),
) -> ChallengeReport:
    absolute, relative = _difference(primary_value, challenger_value)
    status = _status(absolute, spec.tolerance, spec.materiality_threshold)
    finding = ChallengeFinding(
        finding_id=f"{run_id}:{spec.component.value}:{metric_name}",
        component=spec.component,
        status=status,
        metric_name=metric_name,
        primary_value=primary_value,
        challenger_value=challenger_value,
        tolerance=spec.tolerance,
        absolute_difference=absolute,
        relative_difference=relative,
        material=status == GovernanceStatus.BLOCK,
        message=f"{metric_name} primary-versus-challenger reconciliation",
        evidence_ids=evidence_ids,
    )
    evidence = {
        "run_id": run_id,
        "spec": spec,
        "finding": finding,
    }
    return ChallengeReport(
        report_id=f"report:{run_id}:{spec.component.value}",
        run_id=run_id,
        challenger_id=spec.challenger_id,
        component=spec.component,
        findings=(finding,),
        evidence_hash=evidence_sha256(evidence),
    )


def reconcile_series(
    *,
    run_id: str,
    metric_name: str,
    primary_values: Sequence[float],
    challenger_values: Sequence[float],
    spec: ChallengerSpec,
) -> ChallengeReport:
    primary = tuple(float(value) for value in primary_values)
    challenger = tuple(float(value) for value in challenger_values)
    if len(primary) != len(challenger) or not primary:
        raise ValueError("Primary and challenger series must be non-empty and aligned.")
    findings = []
    for index, (first, second) in enumerate(zip(primary, challenger)):
        absolute, relative = _difference(first, second)
        status = _status(absolute, spec.tolerance, spec.materiality_threshold)
        findings.append(
            ChallengeFinding(
                finding_id=f"{run_id}:{spec.component.value}:{metric_name}:{index}",
                component=spec.component,
                status=status,
                metric_name=f"{metric_name}[{index}]",
                primary_value=first,
                challenger_value=second,
                tolerance=spec.tolerance,
                absolute_difference=absolute,
                relative_difference=relative,
                material=status == GovernanceStatus.BLOCK,
            )
        )
    return ChallengeReport(
        report_id=f"report:{run_id}:{spec.component.value}:{metric_name}",
        run_id=run_id,
        challenger_id=spec.challenger_id,
        component=spec.component,
        findings=tuple(findings),
        evidence_hash=evidence_sha256(
            {"primary": primary, "challenger": challenger, "spec": spec}
        ),
    )


def component_reconciliation(
    run_id: str,
    primary: Mapping[str, float],
    challenger: Mapping[str, float],
    spec: ChallengerSpec,
) -> ChallengeReport:
    if set(primary) != set(challenger) or not primary:
        raise ValueError("Component reconciliation requires matching non-empty keys.")
    findings = []
    for name in sorted(primary):
        absolute, relative = _difference(primary[name], challenger[name])
        status = _status(absolute, spec.tolerance, spec.materiality_threshold)
        findings.append(
            ChallengeFinding(
                finding_id=f"{run_id}:{spec.component.value}:{name}",
                component=spec.component,
                status=status,
                metric_name=name,
                primary_value=primary[name],
                challenger_value=challenger[name],
                tolerance=spec.tolerance,
                absolute_difference=absolute,
                relative_difference=relative,
                material=status == GovernanceStatus.BLOCK,
            )
        )
    return ChallengeReport(
        report_id=f"report:{run_id}:{spec.component.value}:components",
        run_id=run_id,
        challenger_id=spec.challenger_id,
        component=spec.component,
        findings=tuple(findings),
        evidence_hash=evidence_sha256(
            {"primary": dict(primary), "challenger": dict(challenger), "spec": spec}
        ),
    )


def disagreement_matrix(reports: Sequence[ChallengeReport]) -> dict[str, dict[str, float | str]]:
    matrix: dict[str, dict[str, float | str]] = {}
    for report in sorted(reports, key=lambda item: item.component.value):
        max_absolute = max(finding.absolute_difference for finding in report.findings)
        max_relative = max(finding.relative_difference for finding in report.findings)
        matrix[report.component.value] = {
            "status": report.status.value,
            "max_absolute_difference": max_absolute,
            "max_relative_difference": max_relative,
            "finding_count": len(report.findings),
        }
    return matrix

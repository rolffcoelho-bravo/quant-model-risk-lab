"""Deterministic Gate 7 challenge, stability, lifecycle, and GenAI benchmarks."""

from __future__ import annotations

from dataclasses import dataclass

from .domain import (
    ChallengeComponent,
    DispositionRecord,
    GovernanceStatus,
    evidence_sha256,
)
from .drift import scalar_drift
from .genai import record_from_mapping, validate_genai_record
from .governance import assess_release_candidate
from .orchestrator import ChallengeOrchestrator
from .reconciliation import reconcile_scalar
from .registry import default_registry
from .stability import path_count_stability, seed_stability, sensitivity_ranking_stability


@dataclass(frozen=True)
class BenchmarkResult:
    benchmark_id: str
    status: str
    detail: str


def _digest(value: str) -> str:
    return evidence_sha256({"value": value})


def run_gate7_benchmarks() -> tuple[BenchmarkResult, ...]:
    registry = default_registry()
    results = []
    results.append(
        BenchmarkResult(
            "registry_coverage",
            "PASS" if not registry.missing() else "FAIL",
            registry.registry_hash,
        )
    )

    spec = registry.get(ChallengeComponent.MULTICURRENCY)
    passed = reconcile_scalar(
        run_id="benchmark-pass",
        metric_name="exposure",
        primary_value=10.0,
        challenger_value=10.0 + 1.0e-10,
        spec=spec,
    )
    results.append(BenchmarkResult("scalar_reconciliation", passed.status.value, passed.evidence_hash))

    blocked = reconcile_scalar(
        run_id="benchmark-block",
        metric_name="exposure",
        primary_value=10.0,
        challenger_value=11.0,
        spec=spec,
    )
    results.append(
        BenchmarkResult(
            "material_disagreement_detection",
            "PASS" if blocked.status == GovernanceStatus.BLOCK else "FAIL",
            blocked.evidence_hash,
        )
    )

    seed = seed_stability({1: 100.0, 2: 100.1, 3: 99.9})
    results.append(BenchmarkResult("seed_stability", seed.status.value, str(seed.deviation)))

    path = path_count_stability({1000: 100.0, 10000: 100.5, 100000: 101.0})
    results.append(
        BenchmarkResult(
            "path_count_stability",
            "PASS" if path.status != GovernanceStatus.BLOCK else "FAIL",
            str(path.deviation),
        )
    )

    ranking = sensitivity_ranking_stability(
        {"fx": 5.0, "credit": 3.0, "funding": 1.0},
        {"fx": 5.2, "credit": 2.9, "funding": 1.1},
    )
    results.append(BenchmarkResult("sensitivity_ranking", ranking.status.value, str(ranking.challenged_value)))

    drift = scalar_drift("cva", 100.0, 140.0)
    results.append(
        BenchmarkResult(
            "drift_block_detection",
            "PASS" if drift.status == GovernanceStatus.BLOCK else "FAIL",
            str(drift.relative_shift),
        )
    )

    rem_spec = registry.get(ChallengeComponent.MARGIN_MVA)
    remediation = reconcile_scalar(
        run_id="benchmark-remediation",
        metric_name="mva",
        primary_value=1.0,
        challenger_value=1.0 + 5.0e-6,
        spec=rem_spec,
    )
    disposition = DispositionRecord(
        finding_id=remediation.findings[0].finding_id,
        owner="model-risk",
        action="independent numerical review",
        state="CLOSED",
        evidence_id="evidence-remediation-1",
        reviewed_by="human-reviewer",
    )
    pass_reports = ChallengeOrchestrator(registry).run_scalar_bundle(
        "benchmark-release",
        {
            component: (1.0, 1.0, "total")
            for component in registry.components
        },
    )
    assessment = assess_release_candidate(
        assessment_id="benchmark-release-candidate",
        reports=(*pass_reports, remediation),
        registry=registry,
        dispositions=(disposition,),
    )
    results.append(
        BenchmarkResult(
            "remediation_and_promotion",
            "PASS" if assessment.eligible_for_release_candidate else "FAIL",
            assessment.evidence_hash,
        )
    )

    invalid_record = record_from_mapping(
        {
            "record_id": "genai-invalid",
            "prompt_id": "prompt-1",
            "model_id": "fixture-model",
            "model_version": "1",
            "input_hash": _digest("input"),
            "output_hash": _digest("output"),
            "reviewer": "human-reviewer",
            "disposition": "REJECTED",
            "autonomous_model_approval": True,
            "boundary": "GENAI_ADVISORY_ONLY_NO_AUTONOMOUS_APPROVAL",
        }
    )
    genai_report = validate_genai_record(invalid_record)
    results.append(
        BenchmarkResult(
            "genai_autonomous_approval_block",
            "PASS" if genai_report.status == GovernanceStatus.BLOCK else "FAIL",
            genai_report.evidence_hash,
        )
    )
    return tuple(results)


def benchmark_evidence() -> dict[str, object]:
    results = run_gate7_benchmarks()
    return {
        "gate": 7,
        "results": results,
        "all_expected_behaviour_confirmed": all(result.status == "PASS" for result in results),
        "evidence_hash": evidence_sha256(results),
    }

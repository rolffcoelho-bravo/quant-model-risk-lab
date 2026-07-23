"""Locked Gate 8 release-consolidation benchmarks."""

from __future__ import annotations

from dataclasses import dataclass

from .assurance import assess_release, standard_pre_release_checks
from .domain import AssuranceCheck, CheckStatus
from .matrix import GATE_TARGETS, build_gate_matrix, matrix_summary
from .publication import publication_payload, required_disclosures, validate_tag_name


@dataclass(frozen=True)
class BenchmarkResult:
    benchmark_id: str
    status: str
    detail: str


def run_gate8_benchmarks() -> tuple[BenchmarkResult, ...]:
    matrix = build_gate_matrix(GATE_TARGETS)
    summary = matrix_summary(matrix)
    checks = standard_pre_release_checks()
    pending = assess_release(checks, human_release_approval=False)
    approved = assess_release(checks, human_release_approval=True, release_tag_created=True)
    blocked = assess_release((AssuranceCheck("material", CheckStatus.BLOCK, "failure", True),), human_release_approval=True)
    payload = publication_payload(commit_sha="f433475", test_count=708)
    results = (
        BenchmarkResult("gate_matrix_complete", "PASS" if summary["gate_count"] == 9 else "FAIL", summary["matrix_hash"]),
        BenchmarkResult("gate_targets_met", "PASS" if summary["all_targets_met"] else "FAIL", str(summary["release_status"])),
        BenchmarkResult("human_release_gate", "PASS" if pending.status == "RELEASE_APPROVAL_REQUIRED" else "FAIL", pending.status),
        BenchmarkResult("release_with_monitoring", "PASS" if approved.status == "RELEASED_WITH_MONITORING" else "FAIL", approved.status),
        BenchmarkResult("material_block", "PASS" if blocked.status == "BLOCK" else "FAIL", blocked.status),
        BenchmarkResult("annotated_tag_name", "PASS" if validate_tag_name("v1.4.0") == "v1.4.0" else "FAIL", "v1.4.0"),
        BenchmarkResult("publication_boundaries", "PASS" if not required_disclosures(payload) else "FAIL", str(payload["boundary"])),
        BenchmarkResult("production_approval_false", "PASS" if payload["production_approval"] is False else "FAIL", "False"),
        BenchmarkResult("regulatory_approval_false", "PASS" if payload["regulatory_approval"] is False else "FAIL", "False"),
        BenchmarkResult("test_surface", "PASS" if payload["collected_test_count"] == 708 else "FAIL", "708"),
    )
    return results


def benchmark_evidence() -> dict[str, object]:
    results = run_gate8_benchmarks()
    return {
        "gate": 8,
        "benchmark_count": len(results),
        "all_expected_behaviour_confirmed": all(item.status == "PASS" for item in results),
        "results": results,
    }

"""v1.4 Gate 8 release consolidation and assurance."""

from .assurance import assess_release, post_release_checks, standard_pre_release_checks
from .benchmark import BenchmarkResult, benchmark_evidence, run_gate8_benchmarks
from .dashboard import build_validation_dashboard, render_dashboard_markdown, render_lifecycle_summary
from .domain import (
    RELEASE_BOUNDARY,
    RELEASE_STATUS,
    RELEASE_TAG,
    AssuranceCheck,
    CheckStatus,
    GateEvidence,
    ReleaseArtifact,
    ReleaseAssessment,
)
from .manifest import artifact_category, build_artifacts, normalized_bytes, normalized_sha256, verify_artifacts
from .matrix import GATE_TARGETS, build_gate_matrix, matrix_hash, matrix_summary
from .publication import publication_payload, previous_release_preserved, release_title, required_disclosures, validate_tag_name

__all__ = [
    "RELEASE_BOUNDARY", "RELEASE_STATUS", "RELEASE_TAG",
    "AssuranceCheck", "BenchmarkResult", "CheckStatus", "GATE_TARGETS",
    "GateEvidence", "ReleaseArtifact", "ReleaseAssessment",
    "artifact_category", "assess_release", "benchmark_evidence",
    "build_artifacts", "build_gate_matrix", "build_validation_dashboard",
    "matrix_hash", "matrix_summary", "normalized_bytes", "normalized_sha256",
    "post_release_checks", "previous_release_preserved", "publication_payload",
    "release_title", "render_dashboard_markdown", "render_lifecycle_summary",
    "required_disclosures", "run_gate8_benchmarks", "standard_pre_release_checks",
    "validate_tag_name", "verify_artifacts",
]

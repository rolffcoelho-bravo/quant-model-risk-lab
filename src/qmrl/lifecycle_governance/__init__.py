"""v1.4 Gate 7 independent challenge and lifecycle governance."""

from .benchmark import BenchmarkResult, benchmark_evidence, run_gate7_benchmarks
from .dashboard import build_lifecycle_dashboard, render_review_card
from .domain import (
    CHALLENGE_BOUNDARY,
    GENAI_BOUNDARY,
    RELEASE_CANDIDATE_STATUS,
    ChallengeComponent,
    ChallengeFinding,
    ChallengeReport,
    DispositionRecord,
    DriftObservation,
    GenAIEvidenceRecord,
    GovernanceStatus,
    LifecycleAssessment,
    StabilityObservation,
    canonical_json,
    evidence_sha256,
    worst_status,
)
from .drift import aggregate_drift, consecutive_monitoring_breach, population_stability_index, scalar_drift
from .genai import advisory_summary, challenge_evidence_bundle, load_record, record_from_mapping, validate_genai_record
from .governance import PromotionPolicy, assess_release_candidate, disposition_map, validate_dispositions
from .orchestrator import ChallengeOrchestrator
from .reconciliation import component_reconciliation, disagreement_matrix, reconcile_scalar, reconcile_series
from .registry import ChallengerRegistry, ChallengerSpec, REQUIRED_COMPONENTS, default_registry
from .stability import (
    classify_deviation,
    input_perturbation_stability,
    path_count_stability,
    seed_stability,
    sensitivity_ranking_stability,
    time_grid_stability,
)

__all__ = [
    "CHALLENGE_BOUNDARY",
    "GENAI_BOUNDARY",
    "RELEASE_CANDIDATE_STATUS",
    "BenchmarkResult",
    "ChallengeComponent",
    "ChallengeFinding",
    "ChallengeOrchestrator",
    "ChallengeReport",
    "ChallengerRegistry",
    "ChallengerSpec",
    "DispositionRecord",
    "DriftObservation",
    "GenAIEvidenceRecord",
    "GovernanceStatus",
    "LifecycleAssessment",
    "PromotionPolicy",
    "REQUIRED_COMPONENTS",
    "StabilityObservation",
    "advisory_summary",
    "aggregate_drift",
    "assess_release_candidate",
    "benchmark_evidence",
    "build_lifecycle_dashboard",
    "canonical_json",
    "challenge_evidence_bundle",
    "classify_deviation",
    "component_reconciliation",
    "consecutive_monitoring_breach",
    "default_registry",
    "disagreement_matrix",
    "disposition_map",
    "evidence_sha256",
    "input_perturbation_stability",
    "load_record",
    "path_count_stability",
    "population_stability_index",
    "reconcile_scalar",
    "reconcile_series",
    "record_from_mapping",
    "render_review_card",
    "run_gate7_benchmarks",
    "scalar_drift",
    "seed_stability",
    "sensitivity_ranking_stability",
    "time_grid_stability",
    "validate_dispositions",
    "validate_genai_record",
    "worst_status",
]

"""Tests for deterministic GenAI grounding controls."""

from __future__ import annotations

from qmrl.genai_grounding import (
    unsupported_numeric_claims,
    validate_citations,
    validate_grounding,
)
from qmrl.genai_schemas import GenAIValidationChallenge


def evidence_package() -> dict:
    return {
        "evidence_package_id": "QMRL-GENAI-FXOPTION-002",
        "sources": [
            {
                "path": "reports/fx_option_validation_report.md",
                "content": (
                    "Observed metric 0.25 and stress level 100."
                ),
            },
            {
                "path": "tests/test_fx_options.py",
                "content": "Unrelated test value 0.99.",
            },
        ],
    }


def challenge_payload() -> dict:
    return {
        "evidence_package_id": "QMRL-GENAI-FXOPTION-002",
        "decision": "CONDITIONAL",
        "executive_summary": (
            "Metric 0.25 is documented."
        ),
        "supported_use": "Restricted validation use.",
        "prohibited_use": "Formal approval.",
        "findings": [
            {
                "finding_id": "GENAI-001",
                "title": "Restriction required",
                "severity": "medium",
                "category": "model_use",
                "observed_evidence": (
                    "Stress level 100 is supplied."
                ),
                "interpretation": (
                    "The evidence supports restricted use."
                ),
                "required_action": "Retain human review.",
                "citation": {
                    "source_path": (
                        "reports/fx_option_validation_report.md"
                    ),
                    "field_or_excerpt": (
                        "Observed metric 0.25"
                    ),
                },
            }
        ],
        "missing_evidence": [],
        "human_review_required": True,
    }


def test_grounded_response_passes() -> None:
    challenge = GenAIValidationChallenge.model_validate(
        challenge_payload()
    )

    assert validate_grounding(
        challenge,
        evidence_package(),
    ) == []


def test_unknown_source_fails() -> None:
    payload = challenge_payload()

    payload["findings"][0]["citation"][
        "source_path"
    ] = "unknown.csv"

    challenge = GenAIValidationChallenge.model_validate(
        payload
    )

    issues = validate_citations(
        challenge,
        evidence_package(),
    )

    assert issues


def test_unsupported_global_number_is_detected() -> None:
    payload = challenge_payload()
    payload["executive_summary"] = (
        "Metric 7.77 is documented."
    )

    challenge = GenAIValidationChallenge.model_validate(
        payload
    )

    assert unsupported_numeric_claims(
        challenge,
        evidence_package(),
    ) == ["7.77"]


def test_number_must_exist_in_cited_source() -> None:
    payload = challenge_payload()

    payload["findings"][0]["observed_evidence"] = (
        "The cited source reports 0.99."
    )

    challenge = GenAIValidationChallenge.model_validate(
        payload
    )

    assert unsupported_numeric_claims(
        challenge,
        evidence_package(),
    ) == ["0.99"]
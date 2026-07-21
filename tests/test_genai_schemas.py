"""Tests for governed GenAI structured outputs."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from qmrl.genai_schemas import GenAIValidationChallenge


def valid_payload() -> dict:
    return {
        "evidence_package_id": "QMRL-GENAI-FXOPTION-001",
        "decision": "CONDITIONAL",
        "executive_summary": "The supplied evidence supports restricted use.",
        "supported_use": "Public validation demonstration.",
        "prohibited_use": "Formal production approval.",
        "findings": [
            {
                "finding_id": "GENAI-001",
                "title": "Documented limitation remains open",
                "severity": "medium",
                "category": "governance",
                "observed_evidence": "The report records an explicit limitation.",
                "interpretation": "The use boundary must remain restricted.",
                "required_action": "Retain the documented restriction.",
                "citation": {
                    "source_path": "reports/fx_option_validation_report.md",
                    "field_or_excerpt": "limitations",
                },
            }
        ],
        "missing_evidence": [],
        "human_review_required": True,
    }


def test_valid_challenge_parses() -> None:
    challenge = GenAIValidationChallenge.model_validate(valid_payload())
    assert challenge.decision == "CONDITIONAL"
    assert challenge.human_review_required is True


def test_unknown_decision_is_rejected() -> None:
    payload = valid_payload()
    payload["decision"] = "APPROVED"

    with pytest.raises(ValidationError):
        GenAIValidationChallenge.model_validate(payload)


def test_extra_fields_are_rejected() -> None:
    payload = valid_payload()
    payload["uncontrolled_field"] = "not allowed"

    with pytest.raises(ValidationError):
        GenAIValidationChallenge.model_validate(payload)
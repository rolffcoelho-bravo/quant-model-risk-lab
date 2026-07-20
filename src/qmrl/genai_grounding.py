"""Deterministic grounding controls for GenAI validation outputs."""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from typing import Any

from qmrl.genai_schemas import GenAIValidationChallenge


_NUMBER_PATTERN = re.compile(r"(?<![A-Za-z0-9_])[-+]?\d+(?:\.\d+)?%?")


def allowed_source_paths(evidence_package: dict[str, Any]) -> set[str]:
    """Return all source paths supplied in the evidence package."""
    return {
        str(source["path"])
        for source in evidence_package.get("sources", [])
        if isinstance(source, dict) and source.get("path")
    }


def validate_citations(
    challenge: GenAIValidationChallenge,
    evidence_package: dict[str, Any],
) -> list[str]:
    """Identify findings that cite a path absent from the evidence package."""
    allowed = allowed_source_paths(evidence_package)
    issues: list[str] = []

    for finding in challenge.findings:
        if finding.citation.source_path not in allowed:
            issues.append(
                f"{finding.finding_id} cites unknown source path: "
                f"{finding.citation.source_path}"
            )

    return issues


def _claim_texts(challenge: GenAIValidationChallenge) -> Iterable[str]:
    yield challenge.executive_summary
    yield challenge.supported_use
    yield challenge.prohibited_use

    for finding in challenge.findings:
        yield finding.observed_evidence
        yield finding.interpretation
        yield finding.required_action

    yield from challenge.missing_evidence


def _normalise_number(token: str) -> str:
    return token.strip().lstrip("+")


def unsupported_numeric_claims(
    challenge: GenAIValidationChallenge,
    evidence_package: dict[str, Any],
) -> list[str]:
    """Return numeric claims that cannot be located in the supplied evidence."""
    source_text = json.dumps(evidence_package, ensure_ascii=False, sort_keys=True)
    supported = {
        _normalise_number(token)
        for token in _NUMBER_PATTERN.findall(source_text)
    }

    unsupported: set[str] = set()
    for text in _claim_texts(challenge):
        for token in _NUMBER_PATTERN.findall(text):
            normalised = _normalise_number(token)
            if normalised not in supported:
                unsupported.add(normalised)

    return sorted(unsupported)


def validate_grounding(
    challenge: GenAIValidationChallenge,
    evidence_package: dict[str, Any],
) -> list[str]:
    """Run all deterministic grounding controls."""
    issues = validate_citations(challenge, evidence_package)
    unsupported = unsupported_numeric_claims(challenge, evidence_package)

    if unsupported:
        issues.append(
            "Unsupported numeric claims: " + ", ".join(unsupported)
        )

    if challenge.evidence_package_id != evidence_package.get("evidence_package_id"):
        issues.append(
            "Response evidence_package_id does not match the input package."
        )

    if challenge.human_review_required is not True:
        issues.append("The response removed the mandatory human-review gate.")

    return issues
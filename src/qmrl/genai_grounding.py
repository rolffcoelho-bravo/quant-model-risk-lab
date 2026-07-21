"""Deterministic grounding controls for GenAI validation outputs."""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from typing import Any

from qmrl.genai_schemas import GenAIValidationChallenge


_NUMBER_PATTERN = re.compile(
    r"(?<![A-Za-z0-9_])[-+]?\d+(?:\.\d+)?(?:e[-+]?\d+)?%?",
    flags=re.IGNORECASE,
)


def allowed_source_paths(
    evidence_package: dict[str, Any],
) -> set[str]:
    """Return every source path supplied in the evidence package."""
    return {
        str(source["path"])
        for source in evidence_package.get("sources", [])
        if isinstance(source, dict) and source.get("path")
    }


def source_payloads(
    evidence_package: dict[str, Any],
) -> dict[str, str]:
    """Return serialized evidence indexed by source path."""
    payloads: dict[str, str] = {}

    for source in evidence_package.get("sources", []):
        if not isinstance(source, dict):
            continue

        path = source.get("path")

        if not path:
            continue

        payloads[str(path)] = json.dumps(
            source,
            ensure_ascii=False,
            sort_keys=True,
        )

    return payloads


def validate_citations(
    challenge: GenAIValidationChallenge,
    evidence_package: dict[str, Any],
) -> list[str]:
    """Identify findings citing paths absent from the evidence package."""
    allowed = allowed_source_paths(evidence_package)
    issues: list[str] = []

    for finding in challenge.findings:
        if finding.citation.source_path not in allowed:
            issues.append(
                f"{finding.finding_id} cites unknown source path: "
                f"{finding.citation.source_path}"
            )

    return issues


def _normalise_number(token: str) -> str:
    return token.strip().lower().lstrip("+")


def _numbers(text: str) -> set[str]:
    return {
        _normalise_number(token)
        for token in _NUMBER_PATTERN.findall(text)
    }


def _global_claim_texts(
    challenge: GenAIValidationChallenge,
) -> Iterable[str]:
    yield challenge.executive_summary
    yield challenge.supported_use
    yield challenge.prohibited_use
    yield from challenge.missing_evidence


def unsupported_numeric_claims(
    challenge: GenAIValidationChallenge,
    evidence_package: dict[str, Any],
) -> list[str]:
    """Return numeric claims unsupported by the relevant evidence."""
    all_source_text = json.dumps(
        evidence_package,
        ensure_ascii=False,
        sort_keys=True,
    )

    all_supported = _numbers(all_source_text)
    unsupported: set[str] = set()

    for text in _global_claim_texts(challenge):
        unsupported.update(
            _numbers(text) - all_supported
        )

    by_path = source_payloads(evidence_package)

    for finding in challenge.findings:
        cited_text = by_path.get(
            finding.citation.source_path,
            "",
        )

        cited_supported = _numbers(cited_text)

        finding_texts = [
            finding.observed_evidence,
            finding.interpretation,
            finding.required_action,
            finding.citation.field_or_excerpt,
        ]

        for text in finding_texts:
            unsupported.update(
                _numbers(text) - cited_supported
            )

    return sorted(unsupported)


def validate_grounding(
    challenge: GenAIValidationChallenge,
    evidence_package: dict[str, Any],
) -> list[str]:
    """Run all deterministic grounding controls."""
    issues = validate_citations(
        challenge,
        evidence_package,
    )

    unsupported = unsupported_numeric_claims(
        challenge,
        evidence_package,
    )

    if unsupported:
        issues.append(
            "Unsupported numeric claims: "
            + ", ".join(unsupported)
        )

    expected_package_id = evidence_package.get(
        "evidence_package_id"
    )

    if challenge.evidence_package_id != expected_package_id:
        issues.append(
            "Response evidence_package_id does not match "
            "the input package."
        )

    if challenge.human_review_required is not True:
        issues.append(
            "The response removed the mandatory human-review gate."
        )

    return issues
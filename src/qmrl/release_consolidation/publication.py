"""Release publication metadata and boundary controls."""

from __future__ import annotations

from typing import Mapping

from .domain import RELEASE_BOUNDARY, RELEASE_STATUS, RELEASE_TAG


def validate_tag_name(tag: str) -> str:
    if tag != RELEASE_TAG:
        raise ValueError(f"Gate 8 may publish only {RELEASE_TAG}.")
    return tag


def previous_release_preserved(tags: tuple[str, ...]) -> bool:
    return "v1.3.0" in tags and RELEASE_TAG not in tuple(tag for tag in tags if tag != RELEASE_TAG)


def release_title() -> str:
    return "Quant Model Risk Lab v1.4.0"


def publication_payload(*, commit_sha: str, test_count: int, release_url: str = "") -> dict[str, object]:
    if len(commit_sha) < 7 or test_count <= 0:
        raise ValueError("Publication requires a commit SHA and positive test count.")
    return {
        "tag": validate_tag_name(RELEASE_TAG),
        "title": release_title(),
        "commit_sha": commit_sha,
        "collected_test_count": int(test_count),
        "status": RELEASE_STATUS,
        "release_url": release_url,
        "draft": False,
        "prerelease": False,
        "production_approval": False,
        "regulatory_approval": False,
        "boundary": RELEASE_BOUNDARY,
    }


def required_disclosures(payload: Mapping[str, object]) -> tuple[str, ...]:
    missing = []
    for field in ("status", "production_approval", "regulatory_approval", "boundary"):
        if field not in payload:
            missing.append(field)
    if payload.get("production_approval") is not False:
        missing.append("production_approval_false")
    if payload.get("regulatory_approval") is not False:
        missing.append("regulatory_approval_false")
    return tuple(sorted(set(missing)))

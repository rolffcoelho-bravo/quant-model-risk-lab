"""Pre-release and post-release assurance evaluation."""

from __future__ import annotations

from typing import Iterable

from .domain import AssuranceCheck, CheckStatus, ReleaseAssessment, RELEASE_STATUS


def assess_release(
    checks: Iterable[AssuranceCheck],
    *,
    human_release_approval: bool,
    release_tag_created: bool = False,
) -> ReleaseAssessment:
    values = tuple(checks)
    if not values:
        raise ValueError("At least one release assurance check is required.")
    if any(item.status in {CheckStatus.BLOCK, CheckStatus.INVALID} for item in values):
        status = "BLOCK"
    elif any(item.status == CheckStatus.REMEDIATE for item in values):
        status = "REMEDIATE"
    elif not human_release_approval:
        status = "RELEASE_APPROVAL_REQUIRED"
    elif any(item.status == CheckStatus.PASS_WITH_MONITORING for item in values):
        status = RELEASE_STATUS
    else:
        status = "RELEASED"
    monitoring = tuple(item.check_id for item in values if item.status == CheckStatus.PASS_WITH_MONITORING)
    return ReleaseAssessment(
        status=status,
        eligible=status in {"RELEASED", RELEASE_STATUS},
        checks=values,
        monitoring_ids=monitoring,
        release_tag_created=release_tag_created,
    )


def standard_pre_release_checks(test_count: int = 708) -> tuple[AssuranceCheck, ...]:
    return (
        AssuranceCheck("gate_matrix", CheckStatus.PASS, "Gates 0-8 reconciled"),
        AssuranceCheck("test_surface", CheckStatus.PASS, f"{test_count} collected tests"),
        AssuranceCheck("pull_request_ci", CheckStatus.PASS, "Python 3.12 validation"),
        AssuranceCheck("post_merge_ci", CheckStatus.PASS, "Python 3.12 validation"),
        AssuranceCheck("lifecycle_monitoring", CheckStatus.PASS_WITH_MONITORING, "Gate 7 lifecycle controls"),
        AssuranceCheck("genai_boundary", CheckStatus.PASS, "advisory-only validated"),
    )


def post_release_checks(
    *, tag_matches: bool, release_published: bool, assurance_tests_pass: bool,
    v13_preserved: bool, clean_tree: bool,
) -> tuple[AssuranceCheck, ...]:
    values = {
        "tag_target": tag_matches,
        "github_release": release_published,
        "assurance_tests": assurance_tests_pass,
        "v1_3_0_preserved": v13_preserved,
        "clean_tree": clean_tree,
    }
    return tuple(
        AssuranceCheck(name, CheckStatus.PASS if passed else CheckStatus.BLOCK, str(passed), material=not passed)
        for name, passed in values.items()
    )

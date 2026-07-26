"""Historical release-contract tests for Quant Model Risk Lab v1.3.0."""

from __future__ import annotations

import json
import re
from pathlib import Path


README = Path("README.md")
CHANGELOG = Path("CHANGELOG.md")
CITATION = Path("CITATION.cff")
MANIFEST = Path("configs/release_manifest_v1_3.json")
RELEASE_NOTES = Path("docs/releases/v1.3.0.md")
DASHBOARD = Path("reports/xva_v1_3_validation_dashboard.json")
LIFECYCLE = Path("reports/xva_v1_3_lifecycle_monitoring.json")
GENAI_REVIEW = Path("data/genai/outputs/xva_v1_3_human_review.json")


def manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8-sig"))


def test_v1_3_release_artifacts_exist() -> None:
    for path in (
        README,
        CHANGELOG,
        CITATION,
        MANIFEST,
        RELEASE_NOTES,
        DASHBOARD,
        LIFECYCLE,
        GENAI_REVIEW,
    ):
        assert path.exists(), path


def test_readme_preserves_v1_3_test_count_under_v1_4() -> None:
    expected = manifest()["validation"]["collected_test_count"]
    content = README.read_text(encoding="utf-8-sig")
    match = re.search(
        r"v1\.3\.0 validated test surface remains `(\d+) collected tests`",
        content,
    )
    assert match is not None
    assert int(match.group(1)) == expected == 350
    assert "**Current release:** v1.4.0" in content
    assert "Python 3.12 validation" in content


def test_release_metadata_is_consistent() -> None:
    release = manifest()["release"]
    assert release["version"] == "1.3.0"
    assert release["tag"] == "v1.3.0"
    assert "## [1.3.0]" in CHANGELOG.read_text(encoding="utf-8-sig")
    assert 'version: "1.3.0"' in CITATION.read_text(encoding="utf-8-sig")
    assert "collected tests" in RELEASE_NOTES.read_text(encoding="utf-8-sig")

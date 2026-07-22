"""Historical release-contract tests for Quant Model Risk Lab v1.2.0."""

from __future__ import annotations

import json
import re
from pathlib import Path


README = Path("README.md")
CHANGELOG = Path("CHANGELOG.md")
MANIFEST = Path("configs/release_manifest_v1_2.json")
GENAI_ARCHITECTURE = Path("docs/governed_genai_architecture.md")
RELEASE_NOTES = Path("docs/releases/v1.2.0.md")
VALIDATION_MATRIX = Path("docs/validation_matrix.md")


def manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8-sig"))


def test_v1_2_historical_release_artifacts_remain_available() -> None:
    for path in (
        README,
        CHANGELOG,
        MANIFEST,
        GENAI_ARCHITECTURE,
        RELEASE_NOTES,
        VALIDATION_MATRIX,
    ):
        assert path.exists(), path


def test_readme_presents_v1_3_and_preserves_v1_2_history() -> None:
    content = README.read_text(encoding="utf-8-sig")
    assert "**Current release:** v1.3.0" in content
    assert "v1.2.0" in content
    assert "Governed GenAI" in content
    assert "Python 3.12 validation" in content
    assert "OPEN_NO_PUBLIC_QUOTE_DATA" in content


def test_v1_2_test_count_remains_frozen_in_release_notes() -> None:
    expected = manifest()["validation"]["collected_test_count"]
    release_notes = RELEASE_NOTES.read_text(encoding="utf-8-sig")
    match = re.search(r"collected tests:\s*`(\d+)`", release_notes)
    assert match is not None
    assert int(match.group(1)) == expected == 136


def test_v1_2_genai_decision_boundary_remains_explicit() -> None:
    genai = manifest()["governed_genai"]
    assert genai["autonomous_model_approval"] is False
    assert genai["human_review_required"] is True
    content = GENAI_ARCHITECTURE.read_text(encoding="utf-8-sig").lower()
    assert "final decision remains human" in content
    assert "approve a model for production" in content


def test_v1_2_open_market_benchmark_is_preserved() -> None:
    open_gate = manifest()["open_gates"][0]
    assert open_gate["status"] == "OPEN_NO_PUBLIC_QUOTE_DATA"
    assert open_gate["production_approval"] is False


def test_v1_2_release_metadata_remains_historical() -> None:
    release = manifest()["release"]
    assert release["version"] == "1.2.0"
    assert release["tag"] == "v1.2.0"
    assert "## [1.2.0]" in CHANGELOG.read_text(encoding="utf-8-sig")

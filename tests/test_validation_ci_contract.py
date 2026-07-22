"""Tests for the governed GitHub Actions validation workflow."""

from __future__ import annotations

from pathlib import Path


WORKFLOW_PATH = Path(
    ".github/workflows/validation-ci.yml"
)

POLICY_PATH = Path(
    "docs/continuous_integration_policy.md"
)


def workflow_text() -> str:
    return WORKFLOW_PATH.read_text(
        encoding="utf-8-sig"
    )


def test_validation_workflow_exists() -> None:
    assert WORKFLOW_PATH.exists()
    assert POLICY_PATH.exists()


def test_validation_workflow_runs_for_main_changes() -> None:
    workflow = workflow_text()

    assert "pull_request:" in workflow
    assert "push:" in workflow
    assert "workflow_dispatch:" in workflow
    assert "Python 3.12 validation" in workflow


def test_validation_workflow_is_read_only_and_headless() -> None:
    workflow = workflow_text()

    assert "permissions:\n  contents: read" in workflow
    assert "MPLBACKEND: Agg" in workflow
    assert "PYTHONHASHSEED:" in workflow
    assert "pull_request_target:" not in workflow
    assert "OPENAI_API_KEY" not in workflow


def test_validation_workflow_executes_full_pytest_suite() -> None:
    workflow = workflow_text()

    required_controls = {
        "actions/checkout@v7",
        "actions/setup-python@v6",
        'python-version: "3.12"',
        "cache: pip",
        "python -m compileall -q src scripts tests",
        "python -m pytest -q --junitxml=test-results/pytest.xml",
        "actions/upload-artifact@v7",
    }

    for control in required_controls:
        assert control in workflow
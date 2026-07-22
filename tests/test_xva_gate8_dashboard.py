from __future__ import annotations

import json
from pathlib import Path

import pytest

from qmrl.xva.dashboard import (
    DashboardPanel,
    build_validation_dashboard,
    canonical_dashboard_hash,
    render_dashboard_markdown,
)


def panel(status: str = "PASS") -> DashboardPanel:
    return DashboardPanel(
        panel_id="exposure",
        title="Exposure",
        status=status,
        headline="Exposure controls reconciled.",
        metrics=(("test_count", 350),),
        artifact_refs=("configs/release_manifest_v1_3.json",),
    )


def test_dashboard_panel_rejects_invalid_status() -> None:
    with pytest.raises(ValueError):
        panel("UNKNOWN")


def test_dashboard_uses_worst_status() -> None:
    dashboard = build_validation_dashboard(
        [
            panel("PASS"),
            DashboardPanel(
                panel_id="monitoring",
                title="Monitoring",
                status="PASS_WITH_MONITORING",
                headline="Open gates remain visible.",
                artifact_refs=("docs/validation_matrix.md",),
            ),
        ]
    )
    assert dashboard.overall_status == "PASS_WITH_MONITORING"


def test_dashboard_markdown_preserves_nonproduction_boundary() -> None:
    markdown = render_dashboard_markdown(build_validation_dashboard([panel()]))
    assert "Production approval:** `False`" in markdown
    assert "does not constitute production" in markdown
    assert "Exposure" in markdown


def test_dashboard_hash_is_deterministic_and_content_sensitive() -> None:
    first = build_validation_dashboard([panel()])
    second = build_validation_dashboard([panel()])
    changed = build_validation_dashboard([panel("PASS_WITH_MONITORING")])
    assert canonical_dashboard_hash(first) == canonical_dashboard_hash(second)
    assert canonical_dashboard_hash(first) != canonical_dashboard_hash(changed)


def test_static_dashboard_reconciles_release_manifest() -> None:
    dashboard = json.loads(
        Path("reports/xva_v1_3_validation_dashboard.json").read_text(
            encoding="utf-8-sig"
        )
    )
    manifest = json.loads(
        Path("configs/release_manifest_v1_3.json").read_text(
            encoding="utf-8-sig"
        )
    )
    assert dashboard["collected_test_count"] == manifest["validation"]["collected_test_count"]
    assert dashboard["overall_status"] == "PASS_WITH_MONITORING"
    assert dashboard["production_approval"] is False

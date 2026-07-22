"""Decision-grade XVA validation dashboard structures."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Iterable


VALID_STATUSES = (
    "PASS",
    "PASS_WITH_MONITORING",
    "REMEDIATE",
    "BLOCK",
)
_STATUS_RANK = {
    "PASS": 0,
    "PASS_WITH_MONITORING": 1,
    "REMEDIATE": 2,
    "BLOCK": 3,
}


@dataclass(frozen=True)
class DashboardPanel:
    """One controlled dashboard panel with traceable evidence."""

    panel_id: str
    title: str
    status: str
    headline: str
    metrics: tuple[tuple[str, Any], ...] = ()
    artifact_refs: tuple[str, ...] = ()
    owner: str = "Model Risk"
    monitoring_required: bool = False

    def __post_init__(self) -> None:
        if not self.panel_id.strip():
            raise ValueError("panel_id must not be empty.")
        if not self.title.strip():
            raise ValueError("title must not be empty.")
        if self.status not in VALID_STATUSES:
            raise ValueError(f"Unsupported dashboard status: {self.status}")
        if not self.headline.strip():
            raise ValueError("headline must not be empty.")
        metric_names = [name for name, _ in self.metrics]
        if len(metric_names) != len(set(metric_names)):
            raise ValueError("Dashboard metric names must be unique within a panel.")
        if not self.artifact_refs:
            raise ValueError("Each dashboard panel requires at least one artifact reference.")

    def to_dict(self) -> dict[str, Any]:
        return {
            "panel_id": self.panel_id,
            "title": self.title,
            "status": self.status,
            "headline": self.headline,
            "metrics": {name: value for name, value in self.metrics},
            "artifact_refs": list(self.artifact_refs),
            "owner": self.owner,
            "monitoring_required": self.monitoring_required,
        }


@dataclass(frozen=True)
class ValidationDashboard:
    """Release-level dashboard preserving the non-production boundary."""

    release_version: str
    generated_at: str
    required_check: str
    panels: tuple[DashboardPanel, ...]
    production_approval: bool = False

    def __post_init__(self) -> None:
        if not self.release_version.strip():
            raise ValueError("release_version must not be empty.")
        if not self.generated_at.strip():
            raise ValueError("generated_at must not be empty.")
        if not self.required_check.strip():
            raise ValueError("required_check must not be empty.")
        if not self.panels:
            raise ValueError("At least one dashboard panel is required.")
        identifiers = [panel.panel_id for panel in self.panels]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("Dashboard panel identifiers must be unique.")
        if self.production_approval:
            raise ValueError("The public dashboard cannot grant production approval.")

    @property
    def overall_status(self) -> str:
        return max(
            (panel.status for panel in self.panels),
            key=lambda status: _STATUS_RANK[status],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "release_version": self.release_version,
            "generated_at": self.generated_at,
            "required_check": self.required_check,
            "overall_status": self.overall_status,
            "production_approval": self.production_approval,
            "panels": [panel.to_dict() for panel in self.panels],
        }


def build_validation_dashboard(
    panels: Iterable[DashboardPanel],
    *,
    release_version: str = "1.3.0",
    generated_at: str = "2026-07-22",
    required_check: str = "Python 3.12 validation",
) -> ValidationDashboard:
    """Build a deterministic public validation dashboard."""

    return ValidationDashboard(
        release_version=release_version,
        generated_at=generated_at,
        required_check=required_check,
        panels=tuple(panels),
        production_approval=False,
    )


def render_dashboard_markdown(dashboard: ValidationDashboard) -> str:
    """Render a concise institutional dashboard without hidden decisions."""

    lines = [
        "# XVA v1.3 Validation Dashboard",
        "",
        f"**Release:** v{dashboard.release_version}",
        f"**Overall validation status:** `{dashboard.overall_status}`",
        f"**Required CI check:** `{dashboard.required_check}`",
        "**Production approval:** `False`",
        "",
        "Passing this dashboard demonstrates public validation evidence and reproducibility. It does not constitute production, regulatory, or institutional model approval.",
        "",
        "| Panel | Status | Decision headline | Owner |",
        "|---|---|---|---|",
    ]

    for panel in dashboard.panels:
        lines.append(
            f"| {panel.title} | `{panel.status}` | {panel.headline} | {panel.owner} |"
        )

    for panel in dashboard.panels:
        lines.extend(["", f"## {panel.title}", "", panel.headline, ""])
        if panel.metrics:
            lines.extend(["| Metric | Value |", "|---|---:|"])
            for name, value in panel.metrics:
                lines.append(f"| {name} | `{value}` |")
        lines.extend(["", "Evidence:"])
        for artifact in panel.artifact_refs:
            lines.append(f"- `{artifact}`")

    return "\n".join(lines).rstrip() + "\n"


def canonical_dashboard_hash(dashboard: ValidationDashboard) -> str:
    """Return a deterministic SHA-256 digest of dashboard content."""

    payload = json.dumps(
        dashboard.to_dict(),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()

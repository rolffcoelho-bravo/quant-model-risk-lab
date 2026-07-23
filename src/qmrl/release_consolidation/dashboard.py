"""Decision-facing release dashboard and lifecycle report rendering."""

from __future__ import annotations

import hashlib
import json

from .domain import AssuranceCheck
from .matrix import matrix_summary


def build_validation_dashboard(matrix, checks: tuple[AssuranceCheck, ...], test_count: int) -> dict[str, object]:
    if test_count <= 0:
        raise ValueError("Test count must be positive.")
    summary = matrix_summary(tuple(matrix))
    payload = {
        "schema_version": "1.0",
        "release": "v1.4.0",
        "release_status": "RELEASED_WITH_MONITORING",
        "test_count": int(test_count),
        "gate_matrix": summary,
        "checks": tuple({"id": item.check_id, "status": item.status.value} for item in checks),
        "production_approval": False,
        "regulatory_approval": False,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    payload["dashboard_hash"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return payload


def render_dashboard_markdown(dashboard: dict[str, object]) -> str:
    return "\n".join((
        "# v1.4 Validation Dashboard",
        f"Release: {dashboard['release']}",
        f"Status: {dashboard['release_status']}",
        f"Collected tests: {dashboard['test_count']}",
        f"Gate count: {dashboard['gate_matrix']['gate_count']}",
        f"Evidence hash: {dashboard['dashboard_hash']}",
    ))


def render_lifecycle_summary(dashboard: dict[str, object]) -> str:
    monitoring = sum(item["status"] == "PASS_WITH_MONITORING" for item in dashboard["checks"])
    return (
        f"v1.4.0 is {dashboard['release_status']} with {monitoring} monitored "
        "assurance dimension(s); production and regulatory approval remain false."
    )

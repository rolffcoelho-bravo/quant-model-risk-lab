from __future__ import annotations
import pytest
from qmrl.release_consolidation import GATE_TARGETS, build_gate_matrix, build_validation_dashboard, render_dashboard_markdown, render_lifecycle_summary, standard_pre_release_checks

def dashboard():
    return build_validation_dashboard(build_gate_matrix(GATE_TARGETS), standard_pre_release_checks(), 708)

def test_dashboard_contains_release_identity():
    assert dashboard()["release"] == "v1.4.0"

def test_dashboard_contains_test_surface():
    assert dashboard()["test_count"] == 708

def test_dashboard_hash_is_deterministic():
    assert dashboard()["dashboard_hash"] == dashboard()["dashboard_hash"]

def test_dashboard_rejects_nonpositive_test_count():
    with pytest.raises(ValueError, match="positive"):
        build_validation_dashboard(build_gate_matrix(GATE_TARGETS), standard_pre_release_checks(), 0)

def test_dashboard_markdown_discloses_hash():
    value = dashboard(); text = render_dashboard_markdown(value)
    assert value["dashboard_hash"] in text

def test_lifecycle_summary_discloses_boundaries():
    text = render_lifecycle_summary(dashboard())
    assert "production and regulatory approval remain false" in text

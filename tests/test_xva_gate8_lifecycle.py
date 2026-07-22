from __future__ import annotations

from qmrl.xva.lifecycle import (
    MonitoringRule,
    assess_lifecycle,
    evaluate_monitoring_metric,
)


def higher_rule() -> MonitoringRule:
    return MonitoringRule(
        metric="challenger_disagreement",
        warning_threshold=0.01,
        remediate_threshold=0.03,
        block_threshold=0.05,
    )


def test_higher_is_worse_pass() -> None:
    assert evaluate_monitoring_metric(0.0, higher_rule()).status == "PASS"


def test_higher_is_worse_monitoring() -> None:
    assert evaluate_monitoring_metric(0.02, higher_rule()).status == "PASS_WITH_MONITORING"


def test_higher_is_worse_remediate() -> None:
    assert evaluate_monitoring_metric(0.04, higher_rule()).status == "REMEDIATE"


def test_higher_is_worse_block() -> None:
    assert evaluate_monitoring_metric(0.05, higher_rule()).status == "BLOCK"


def test_lower_is_worse_direction() -> None:
    rule = MonitoringRule(
        metric="coverage_ratio",
        warning_threshold=0.99,
        remediate_threshold=0.95,
        block_threshold=0.90,
        direction="lower_is_worse",
    )
    assert evaluate_monitoring_metric(1.0, rule).status == "PASS"
    assert evaluate_monitoring_metric(0.97, rule).status == "PASS_WITH_MONITORING"
    assert evaluate_monitoring_metric(0.92, rule).status == "REMEDIATE"
    assert evaluate_monitoring_metric(0.90, rule).status == "BLOCK"


def test_lifecycle_uses_worst_component_status() -> None:
    assessment = assess_lifecycle(
        [
            evaluate_monitoring_metric(0.0, higher_rule()),
            evaluate_monitoring_metric(0.02, higher_rule()),
        ]
    )
    assert assessment.overall_status == "PASS_WITH_MONITORING"

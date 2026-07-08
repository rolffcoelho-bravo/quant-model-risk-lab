from src.qmrl.model_selection import (
    build_model_selection_table,
    recommendation_records,
    select_active_monitoring_stack,
)


def test_model_selection_table_contains_dynamic_regime_roadmap():
    table = build_model_selection_table()
    tools = " ".join(item.primary_tool for item in table)

    assert "Gaussian Hidden Markov Model" in tools


def test_recommendation_records_include_implemented_flag():
    records = recommendation_records()

    assert records
    assert "implemented_in_v07" in records[0]


def test_active_monitoring_stack_escalates_when_pressure_is_high():
    stack = select_active_monitoring_stack(
        pressure_score=75.0,
        pca_percentile=92.0,
        mahalanobis_percentile=96.0,
    )

    assert "Enhanced validation review" in stack
    assert "PCA reconstruction error" in stack
    assert "Static regime clustering" in stack

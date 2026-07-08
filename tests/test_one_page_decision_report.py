from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def test_one_page_decision_report_exists():
    path = ROOT / "reports" / "one_page_curve_inflation_decision_report.md"
    assert path.exists()


def test_one_page_decision_figure_exists():
    path = ROOT / "reports" / "figures" / "curve_inflation_decision_map.png"
    assert path.exists()
    assert path.stat().st_size > 0


def test_one_page_decision_metrics_exist_and_have_decision_state():
    path = ROOT / "data" / "official" / "processed" / "one_page_curve_inflation_decision_metrics.csv"
    metrics = pd.read_csv(path)

    assert not metrics.empty
    assert "decision_state" in metrics.columns
    assert metrics.iloc[0]["decision_state"] in {"Standard review", "Watch", "Enhanced review"}


def test_one_page_decision_metrics_have_core_risk_fields():
    path = ROOT / "data" / "official" / "processed" / "one_page_curve_inflation_decision_metrics.csv"
    metrics = pd.read_csv(path)

    required = {
        "slope_2s10",
        "breakeven_10y",
        "dv01",
        "loss_50bp_percent",
        "loss_100bp_percent",
    }

    assert required.issubset(set(metrics.columns))

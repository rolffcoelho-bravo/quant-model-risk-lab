from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def test_one_page_decision_report_exists():
    path = ROOT / "reports" / "one_page_curve_inflation_decision_report.md"
    assert path.exists()


def test_one_page_decision_figure_exists():
    path = ROOT / "reports" / "figures" / "curve_inflation_decision_map.png"
    assert path.exists()
    assert path.stat().st_size > 100_000


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
        "slope_5s30",
        "breakeven_10y",
        "dgs10_60d_shift",
        "breakeven_60d_shift",
        "dv01",
        "loss_50bp_percent",
        "loss_100bp_percent",
    }

    assert required.issubset(set(metrics.columns))


def test_decision_shock_surface_exists_and_has_multiple_tenors():
    path = ROOT / "data" / "official" / "processed" / "curve_inflation_decision_shock_surface.csv"
    surface = pd.read_csv(path)

    assert not surface.empty
    assert set(surface["tenor_years"]) == {2.0, 5.0, 10.0, 30.0}
    assert set(surface["parallel_shift_bp"]) == {-150.0, -100.0, -50.0, 0.0, 50.0, 100.0, 150.0}

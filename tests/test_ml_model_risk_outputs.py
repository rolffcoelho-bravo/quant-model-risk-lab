from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def test_ml_model_risk_report_exists():
    path = ROOT / "reports" / "ml_model_risk_monitoring_report.md"
    assert path.exists()


def test_ml_model_risk_figure_exists():
    path = ROOT / "reports" / "figures" / "ml_model_risk_monitoring_map.png"
    assert path.exists()
    assert path.stat().st_size > 100_000


def test_ml_model_risk_features_exist():
    path = ROOT / "data" / "official" / "processed" / "ml_model_risk_features.csv"
    features = pd.read_csv(path)

    assert not features.empty
    assert "real_rate_proxy" in features.columns


def test_ml_model_risk_signals_exist_and_have_state():
    path = ROOT / "data" / "official" / "processed" / "ml_model_risk_signals.csv"
    signals = pd.read_csv(path)

    assert not signals.empty
    assert "decision_state" in signals.columns
    assert "ml_pressure_score" in signals.columns


def test_ml_model_selection_table_exists():
    path = ROOT / "data" / "official" / "processed" / "ml_model_selection_table.csv"
    table = pd.read_csv(path)

    assert not table.empty
    assert "primary_tool" in table.columns
    assert "challenger_tool" in table.columns

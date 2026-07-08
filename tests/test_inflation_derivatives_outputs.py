from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def test_inflation_derivatives_report_exists():
    path = ROOT / "reports" / "inflation_derivatives_validation_report.md"
    assert path.exists()


def test_inflation_derivatives_figure_exists():
    path = ROOT / "reports" / "figures" / "inflation_derivatives_validation_map.png"
    assert path.exists()
    assert path.stat().st_size > 100_000


def test_inflation_derivatives_summary_exists_and_has_decision_state():
    path = ROOT / "data" / "official" / "processed" / "inflation_derivatives_summary.csv"
    summary = pd.read_csv(path)

    assert not summary.empty
    assert "decision_state" in summary.columns
    assert "inflation_pressure_score" in summary.columns


def test_inflation_derivatives_shock_table_exists_and_has_100bp():
    path = ROOT / "data" / "official" / "processed" / "inflation_derivatives_shock_table.csv"
    table = pd.read_csv(path)

    assert not table.empty
    assert 100.0 in set(table["inflation_shock_bp"])
    assert -100.0 in set(table["inflation_shock_bp"])

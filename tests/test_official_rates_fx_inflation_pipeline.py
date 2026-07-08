import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def test_official_manifest_exists():
    manifest_path = ROOT / "data" / "official" / "manifest.json"
    assert manifest_path.exists()


def test_official_manifest_has_sources():
    manifest_path = ROOT / "data" / "official" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert "sources" in manifest
    assert "fred_rates_inflation" in manifest["sources"]
    assert "ecb_fx_rates" in manifest["sources"]


def test_curve_validation_summary_exists_and_has_discount_factors():
    path = ROOT / "data" / "official" / "processed" / "curve_validation_summary.csv"
    data = pd.read_csv(path)

    assert not data.empty
    assert "discount_factor_simple" in data.columns
    assert (data["discount_factor_simple"] > 0).all()


def test_fx_risk_summary_contains_real_currencies():
    path = ROOT / "data" / "official" / "processed" / "fx_risk_summary.csv"
    data = pd.read_csv(path)

    assert not data.empty
    assert set(["USD", "GBP", "JPY", "CHF"]).issubset(set(data["currency"]))


def test_official_pipeline_report_exists():
    path = ROOT / "reports" / "official_rates_fx_inflation_pipeline_report.md"
    assert path.exists()

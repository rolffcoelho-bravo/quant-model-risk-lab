from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pandas as pd


def run_fx_options_script() -> None:
    subprocess.run([sys.executable, "scripts/run_fx_options_validation.py"], check=True)


def test_fx_options_script_generates_outputs():
    run_fx_options_script()

    assert Path("data/official/processed/fx_option_validation_summary.csv").exists()
    assert Path("data/official/processed/fx_option_spot_vol_surface.csv").exists()
    assert Path("data/official/processed/fx_option_put_call_parity_table.csv").exists()
    assert Path("data/official/processed/fx_option_lifecycle_register.csv").exists()
    assert Path("reports/fx_option_validation_report.md").exists()
    assert Path("reports/figures/fx_option_validation_map.png").exists()


def test_fx_options_summary_has_required_columns():
    run_fx_options_script()

    summary = pd.read_csv("data/official/processed/fx_option_validation_summary.csv")
    required = {
        "model_id",
        "pricing_model",
        "spot_rate_brl_per_usd",
        "strike_rate",
        "realised_volatility_input",
        "call_value_brl",
        "put_value_brl",
        "call_delta",
        "put_delta",
        "call_vega",
        "put_call_parity_gap",
        "model_use_decision",
        "next_validation_gate",
    }

    assert required.issubset(summary.columns)
    assert summary.iloc[0]["call_value_brl"] > 0
    assert summary.iloc[0]["put_value_brl"] > 0
    assert summary.iloc[0]["realised_volatility_input"] > 0


def test_fx_options_surface_preserves_spot_and_vol_grid():
    run_fx_options_script()

    surface = pd.read_csv("data/official/processed/fx_option_spot_vol_surface.csv")
    assert {-10.0, -5.0, 0.0, 5.0, 10.0}.issubset(set(surface["spot_shock_pct"].astype(float)))
    assert {-0.05, 0.0, 0.05}.issubset(set(surface["vol_shock_abs"].astype(float)))
    assert {"call_value_domestic", "put_value_domestic", "call_delta", "put_delta"}.issubset(surface.columns)


def test_fx_options_report_contains_sabr_and_path_dependent_next_gate():
    run_fx_options_script()

    report = Path("reports/fx_option_validation_report.md").read_text(encoding="utf-8")
    assert "Garman-Kohlhagen" in report
    assert "put-call parity" in report
    assert "SABR" in report
    assert "path-dependent" in report
    assert "Archer / MRM action" in report

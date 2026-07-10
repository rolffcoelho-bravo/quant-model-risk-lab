from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pandas as pd


def run_fx_script() -> None:
    subprocess.run([sys.executable, "scripts/run_fx_derivatives_validation.py"], check=True)


def test_fx_script_generates_outputs():
    run_fx_script()

    assert Path("data/official/processed/fx_forward_validation_summary.csv").exists()
    assert Path("data/official/processed/fx_forward_shock_table.csv").exists()
    assert Path("data/official/processed/fx_model_lifecycle_register.csv").exists()
    assert Path("reports/fx_forward_validation_report.md").exists()
    assert Path("reports/figures/fx_forward_validation_map.png").exists()


def test_fx_summary_has_required_columns():
    run_fx_script()

    summary = pd.read_csv("data/official/processed/fx_forward_validation_summary.csv")
    required = {
        "model_id",
        "product",
        "spot_rate_brl_per_usd",
        "domestic_rate_brl",
        "foreign_rate_usd",
        "model_forward_rate",
        "contract_forward_rate",
        "long_usd_forward_value_brl",
        "fx_delta",
        "model_use_decision",
        "next_validation_gate",
    }

    assert required.issubset(summary.columns)
    assert summary.iloc[0]["spot_rate_brl_per_usd"] > 0
    assert summary.iloc[0]["model_forward_rate"] > 0


def test_fx_shock_table_has_required_shocks():
    run_fx_script()

    shocks = pd.read_csv("data/official/processed/fx_forward_shock_table.csv")
    assert {-10.0, -5.0, 0.0, 5.0, 10.0}.issubset(set(shocks["spot_shock_pct"].astype(float)))
    assert {"long_foreign_forward_pnl", "fx_delta"}.issubset(shocks.columns)


def test_fx_report_contains_mrm_and_next_gate():
    run_fx_script()

    report = Path("reports/fx_forward_validation_report.md").read_text(encoding="utf-8")
    assert "Foreign Exchange (FX)" in report
    assert "Archer / MRM action" in report
    assert "FX options" in report
    assert "cross-currency-basis" in report

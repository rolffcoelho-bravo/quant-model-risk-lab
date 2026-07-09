from pathlib import Path
import subprocess
import sys

import pandas as pd


def run_ir_validation_script():
    subprocess.run([sys.executable, "scripts/run_ir_derivatives_pricing_validation.py"], check=True)


def test_ir_derivatives_script_generates_outputs():
    run_ir_validation_script()

    assert Path("data/official/processed/ir_derivatives_pricing_summary.csv").exists()
    assert Path("data/official/processed/ir_swap_shock_table.csv").exists()
    assert Path("reports/ir_derivatives_pricing_validation_report.md").exists()
    assert Path("reports/figures/ir_derivatives_pricing_validation_map.png").exists()
    assert Path("data/official/processed/ir_derivatives_model_lifecycle_register.csv").exists()


def test_ir_derivatives_summary_has_required_columns():
    run_ir_validation_script()

    summary = pd.read_csv("data/official/processed/ir_derivatives_pricing_summary.csv")
    required = {
        "par_swap_rate",
        "validation_fixed_rate",
        "fixed_leg_pv",
        "floating_leg_pv",
        "payer_swap_npv",
        "receiver_swap_npv",
        "payer_dv01",
        "receiver_dv01",
        "decision_state",
    }
    assert required.issubset(summary.columns)
    assert not summary.empty


def test_ir_derivatives_payer_receiver_symmetry_in_output():
    run_ir_validation_script()

    summary = pd.read_csv("data/official/processed/ir_derivatives_pricing_summary.csv")
    row = summary.iloc[0]
    assert abs(row["payer_swap_npv"] + row["receiver_swap_npv"]) < 1e-6


def test_ir_derivatives_shock_table_has_expected_shocks():
    run_ir_validation_script()

    shock_table = pd.read_csv("data/official/processed/ir_swap_shock_table.csv")
    assert set(shock_table["curve_shift_bp"]) == {-100.0, -50.0, 0.0, 50.0, 100.0}
    assert {"payer_npv_change", "receiver_npv_change"}.issubset(shock_table.columns)


def test_ir_derivatives_report_contains_validation_boundary():
    run_ir_validation_script()

    report = Path("reports/ir_derivatives_pricing_validation_report.md").read_text(encoding="utf-8")
    assert "Scope control" in report
    assert "fixed-for-floating" in report or "Fixed-for-floating" in report
    assert "DV01" in report


def test_ir_derivatives_lifecycle_register_has_model_fields():
    run_ir_validation_script()

    lifecycle = pd.read_csv("data/official/processed/ir_derivatives_model_lifecycle_register.csv")
    required = {
        "model_id",
        "model_name",
        "lifecycle_stage",
        "valuation_status",
        "risk_status",
        "archer_action",
        "mmmrc_action",
        "revalidation_trigger",
        "next_lifecycle_gate",
    }
    assert required.issubset(lifecycle.columns)
    assert lifecycle.iloc[0]["next_lifecycle_gate"] == "v0.9 XVA validation layer"

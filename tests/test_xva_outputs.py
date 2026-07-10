from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pandas as pd


def run_xva_script() -> None:
    subprocess.run([sys.executable, "scripts/run_xva_validation.py"], check=True)


def test_xva_script_generates_outputs():
    run_xva_script()

    assert Path("data/official/processed/xva_exposure_profile.csv").exists()
    assert Path("data/official/processed/xva_summary.csv").exists()
    assert Path("data/official/processed/xva_sensitivity_table.csv").exists()
    assert Path("reports/xva_validation_report.md").exists()
    assert Path("reports/figures/xva_validation_map.png").exists()


def test_xva_summary_contains_required_metrics():
    run_xva_script()

    summary = pd.read_csv("data/official/processed/xva_summary.csv")
    required = {
        "expected_exposure",
        "expected_negative_exposure",
        "pfe_95",
        "cva",
        "dva",
        "fva",
        "xva_reserve",
        "xva_adjusted_payer_value",
        "model_use_decision",
        "next_validation_gate",
    }

    assert required.issubset(summary.columns)
    row = summary.iloc[0]
    assert row["expected_exposure"] >= 0
    assert row["pfe_95"] >= 0
    assert row["cva"] >= 0
    assert row["dva"] >= 0
    assert row["fva"] >= 0


def test_xva_exposure_profile_preserves_shock_grid():
    run_xva_script()

    exposure = pd.read_csv("data/official/processed/xva_exposure_profile.csv")
    assert {-100.0, -50.0, 0.0, 50.0, 100.0}.issubset(set(exposure["curve_shift_bp"].astype(float)))
    assert {"positive_exposure", "negative_exposure", "exposure_state"}.issubset(exposure.columns)


def test_xva_report_documents_cva_dva_fva_and_mrm_action():
    run_xva_script()

    report = Path("reports/xva_validation_report.md").read_text(encoding="utf-8")

    assert "CVA" in report
    assert "DVA" in report
    assert "FVA" in report
    assert "EE" in report
    assert "PFE" in report
    assert "Archer / MRM action" in report
    assert "not a production exposure engine" in report

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pandas as pd


def run_export() -> None:
    subprocess.run([sys.executable, "scripts/export_ir_swap_excel_pack.py"], check=True)


def test_excel_vba_bridge_generates_control_exports():
    run_export()

    control_path = Path("excel_vba/exports/ir_swap_revalidation_control_panel.csv")
    shock_path = Path("excel_vba/exports/ir_swap_revalidation_shock_table.csv")
    lifecycle_path = Path("excel_vba/exports/ir_swap_revalidation_lifecycle_record.csv")

    assert control_path.exists()
    assert shock_path.exists()
    assert lifecycle_path.exists()

    control = pd.read_csv(control_path)
    assert {"field", "value", "type", "decision_meaning"}.issubset(control.columns)
    assert "PV symmetry error" in set(control["field"])
    assert "XVA coverage" in set(control["field"])
    assert "Model-use status" in set(control["field"])


def test_excel_vba_module_contains_revalidation_macros():
    text = Path("excel_vba/vba/Revalidate_IR_Swap.bas").read_text(encoding="utf-8")

    assert "RunIRSwapRevalidation" in text
    assert "CheckPVSymmetry" in text
    assert "CheckDV01Sign" in text
    assert "CheckShockDirection" in text
    assert "AppendRevalidationLog" in text


def test_excel_bridge_report_documents_archer_and_mrm_bridge():
    run_export()

    report = Path("reports/excel_vba_revalidation_bridge.md").read_text(encoding="utf-8")

    assert "Excel/VBA Revalidation Bridge" in report
    assert "Archer/MRM" in report
    assert "PV symmetry" in report
    assert "XVA" in report


def test_excel_bridge_shock_export_preserves_required_shocks():
    run_export()

    shock = pd.read_csv("excel_vba/exports/ir_swap_revalidation_shock_table.csv")
    shock_col = "curve_shift_bp" if "curve_shift_bp" in shock.columns else shock.columns[0]

    assert {-100.0, -50.0, 0.0, 50.0, 100.0}.issubset(set(shock[shock_col].astype(float)))

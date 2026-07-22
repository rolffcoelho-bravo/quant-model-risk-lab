"""Output tests for the FX-option monitoring evidence."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pandas as pd


def run_monitoring() -> None:
    subprocess.run(
        [
            sys.executable,
            "scripts/run_fx_options_validation.py",
        ],
        check=True,
    )

    subprocess.run(
        [
            sys.executable,
            "scripts/run_fx_option_monitoring.py",
            "--initialize-baseline",
        ],
        check=True,
    )

    subprocess.run(
        [
            sys.executable,
            "scripts/run_fx_option_monitoring.py",
        ],
        check=True,
    )


def test_monitoring_outputs_pass_at_baseline() -> None:
    run_monitoring()

    status_path = Path(
        "data/official/processed/"
        "fx_option_monitoring_status.csv"
    )

    baseline_path = Path(
        "data/official/processed/"
        "fx_option_monitoring_baseline.csv"
    )

    report_path = Path(
        "reports/fx_option_monitoring_report.md"
    )

    assert status_path.exists()
    assert baseline_path.exists()
    assert report_path.exists()

    status = pd.read_csv(
        status_path
    ).iloc[0]

    assert status["monitoring_status"] == "PASS"

    assert str(
        status["revalidation_required"]
    ).lower() == "false"

    assert json.loads(
        status["alerts_json"]
    ) == []

    assert (
        status["market_quote_benchmark"]
        == "OPEN_NO_PUBLIC_QUOTE_DATA"
    )

    assert str(
        status["production_approval"]
    ).lower() == "false"


def test_monitoring_report_preserves_boundaries() -> None:
    run_monitoring()

    report = Path(
        "reports/fx_option_monitoring_report.md"
    ).read_text(
        encoding="utf-8"
    )

    assert "Monitoring status: **PASS**" in report
    assert "Production approval: **NO**" in report

    assert (
        "OPEN_NO_PUBLIC_QUOTE_DATA"
        in report
    )

    assert (
        "External alert delivery"
        in report
    )
"""Output tests for the corrected FX input and challenger layers."""

from __future__ import annotations

import math
from pathlib import Path
import subprocess
import sys

import pandas as pd


def run_remediation_outputs() -> None:
    subprocess.run(
        [
            sys.executable,
            "scripts/run_fx_option_challenger_validation.py",
        ],
        check=True,
    )


def test_corrected_fx_sources_and_scale() -> None:
    run_remediation_outputs()

    summary = pd.read_csv(
        "data/official/processed/"
        "fx_option_validation_summary.csv"
    ).iloc[0]

    assert summary["currency_pair"] == "USD/BRL"
    assert summary["quote_convention"] == "BRL per USD"
    assert summary["spot_source_id"] == "BCB_SGS_1"

    assert (
        summary["domestic_rate_source_id"]
        == "BCB_SGS_432"
    )

    assert (
        summary["foreign_rate_source_id"]
        == "FRED_DGS1"
    )

    assert summary["input_contract_status"] == "PASS"

    spot = float(
        summary["spot_rate_brl_per_usd"]
    )

    strike = float(
        summary["strike_rate"]
    )

    domestic = float(
        summary["domestic_rate_brl"]
    )

    foreign = float(
        summary["foreign_rate_usd"]
    )

    maturity = float(
        summary["maturity_years"]
    )

    expected_forward = spot * math.exp(
        (domestic - foreign) * maturity
    )

    assert 1.0 < spot < 20.0
    assert 0.0 <= domestic < 1.0
    assert abs(strike - expected_forward) < 1.0e-10
    assert strike / spot < 2.0


def test_challenger_and_market_boundary_are_explicit() -> None:
    run_remediation_outputs()

    benchmark_path = Path(
        "data/official/processed/"
        "fx_option_challenger_benchmark.csv"
    )

    report_path = Path(
        "reports/"
        "fx_option_challenger_validation_report.md"
    )

    assert benchmark_path.exists()
    assert report_path.exists()

    benchmark = pd.read_csv(
        benchmark_path
    )

    assert set(
        benchmark[
            "implementation_challenger_status"
        ]
    ) == {"PASS"}

    assert set(
        benchmark[
            "market_quote_benchmark_status"
        ]
    ) == {
        "OPEN_NO_PUBLIC_QUOTE_DATA"
    }

    report = report_path.read_text(
        encoding="utf-8"
    )

    assert "Black-76" in report
    assert "finite-difference" in report
    assert "OPEN_NO_PUBLIC_QUOTE_DATA" in report
    assert "not production approved" in report
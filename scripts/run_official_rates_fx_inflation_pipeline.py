"""Official rates, FX and inflation data pipeline.

This script downloads public official data aligned with model-risk validation for
IR, FX and inflation workflows.

Sources:
- FRED CSV endpoint for U.S. Treasury rates and breakeven inflation.
- ECB historical euro foreign exchange reference rates ZIP file.

The script stores raw files, builds processed panels, creates validation summaries,
generates file hashes and writes a model-risk report.
"""

from __future__ import annotations

import hashlib
import json
import zipfile
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

import numpy as np
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "official" / "raw"
PROCESSED_DIR = ROOT / "data" / "official" / "processed"
REPORTS_DIR = ROOT / "reports"

FRED_URL = (
    "https://fred.stlouisfed.org/graph/fredgraph.csv"
    "?id=DGS1,DGS2,DGS5,DGS10,DGS30,T10YIE"
)

ECB_FX_ZIP_URL = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.zip"

RATE_COLUMNS = ["DGS1", "DGS2", "DGS5", "DGS10", "DGS30"]
INFLATION_COLUMNS = ["T10YIE"]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_fred_rates_and_inflation() -> pd.DataFrame:
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    response = requests.get(FRED_URL, timeout=30)
    response.raise_for_status()

    raw_path = RAW_DIR / "fred_us_rates_inflation.csv"
    raw_path.write_bytes(response.content)

    data = pd.read_csv(raw_path)
    data = data.rename(columns={"observation_date": "date"})
    data["date"] = pd.to_datetime(data["date"], errors="raise")

    for column in RATE_COLUMNS + INFLATION_COLUMNS:
        data[column] = pd.to_numeric(data[column], errors="coerce")

    data = data.sort_values("date")
    data.to_csv(raw_path, index=False)
    return data


def download_ecb_fx_rates() -> pd.DataFrame:
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    response = requests.get(ECB_FX_ZIP_URL, timeout=30)
    response.raise_for_status()

    zip_path = RAW_DIR / "ecb_eurofxref_hist.zip"
    zip_path.write_bytes(response.content)

    with zipfile.ZipFile(BytesIO(response.content)) as archive:
        csv_names = [name for name in archive.namelist() if name.endswith(".csv")]
        if not csv_names:
            raise ValueError("ECB ZIP file does not contain a CSV file.")

        with archive.open(csv_names[0]) as file:
            fx = pd.read_csv(file)

    fx.columns = [column.strip() for column in fx.columns]
    fx = fx.rename(columns={"Date": "date"})
    fx["date"] = pd.to_datetime(fx["date"], errors="raise")

    required = ["date", "USD", "GBP", "JPY", "CHF"]
    missing = [column for column in required if column not in fx.columns]
    if missing:
        raise ValueError(f"ECB FX data missing required columns: {missing}")

    for column in ["USD", "GBP", "JPY", "CHF"]:
        fx[column] = pd.to_numeric(fx[column], errors="coerce")

    fx = fx[required].sort_values("date")
    raw_csv_path = RAW_DIR / "ecb_eurofxref_hist.csv"
    fx.to_csv(raw_csv_path, index=False)
    return fx


def build_processed_panels(fred: pd.DataFrame, fx: pd.DataFrame) -> dict[str, pd.DataFrame]:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    rates = fred[["date"] + RATE_COLUMNS].dropna(how="all", subset=RATE_COLUMNS)
    inflation = fred[["date"] + INFLATION_COLUMNS].dropna(how="all", subset=INFLATION_COLUMNS)

    fx = fx.dropna(subset=["USD"])

    combined = rates.merge(inflation, on="date", how="outer")
    combined = combined.merge(fx, on="date", how="inner")
    combined = combined.sort_values("date")

    curve_nodes = rates.copy()
    curve_nodes.to_csv(PROCESSED_DIR / "usd_treasury_curve_nodes.csv", index=False)

    inflation.to_csv(PROCESSED_DIR / "breakeven_inflation_panel.csv", index=False)
    fx.to_csv(PROCESSED_DIR / "ecb_fx_panel.csv", index=False)
    combined.to_csv(PROCESSED_DIR / "official_rates_fx_inflation_panel.csv", index=False)

    fx_returns = fx.set_index("date")[["USD", "GBP", "JPY", "CHF"]].pct_change().dropna()
    fx_returns.to_csv(PROCESSED_DIR / "fx_daily_returns.csv")

    return {
        "curve_nodes": curve_nodes,
        "inflation": inflation,
        "fx": fx,
        "combined": combined,
        "fx_returns": fx_returns.reset_index(),
    }


def build_curve_validation_summary(curve_nodes: pd.DataFrame) -> pd.DataFrame:
    latest = curve_nodes.dropna(subset=RATE_COLUMNS).tail(1)
    if latest.empty:
        raise ValueError("No complete latest yield-curve row available.")

    row = latest.iloc[0]
    maturities = np.array([1, 2, 5, 10, 30], dtype=float)
    yields = np.array([row[column] for column in RATE_COLUMNS], dtype=float)

    summary = pd.DataFrame(
        {
            "maturity_years": maturities,
            "yield_percent": yields,
            "discount_factor_simple": 1 / (1 + yields / 100) ** maturities,
        }
    )

    summary.to_csv(PROCESSED_DIR / "curve_validation_summary.csv", index=False)
    return summary


def build_fx_risk_summary(fx_returns: pd.DataFrame) -> pd.DataFrame:
    rows = []

    for column in ["USD", "GBP", "JPY", "CHF"]:
        series = fx_returns[column].dropna()
        var_95 = float(-np.percentile(series, 5))
        rows.append(
            {
                "currency": column,
                "observations": int(len(series)),
                "mean_return": float(series.mean()),
                "volatility": float(series.std()),
                "historical_var_95": var_95,
                "worst_return": float(series.min()),
                "best_return": float(series.max()),
            }
        )

    summary = pd.DataFrame(rows)
    summary.to_csv(PROCESSED_DIR / "fx_risk_summary.csv", index=False)
    return summary


def markdown_table(data: pd.DataFrame) -> str:
    if data.empty:
        return "_No data available._"

    columns = list(data.columns)
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"

    rows = []
    for _, row in data.iterrows():
        values = []
        for column in columns:
            value = row[column]
            if isinstance(value, float):
                values.append(f"{value:.6f}")
            else:
                values.append(str(value))
        rows.append("| " + " | ".join(values) + " |")

    return "\n".join([header, separator, *rows])


def write_manifest(outputs: dict[str, pd.DataFrame]) -> None:
    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "sources": {
            "fred_rates_inflation": FRED_URL,
            "ecb_fx_rates": ECB_FX_ZIP_URL,
        },
        "raw_files": {
            "fred_us_rates_inflation": {
                "path": "data/official/raw/fred_us_rates_inflation.csv",
                "sha256": sha256_file(RAW_DIR / "fred_us_rates_inflation.csv"),
            },
            "ecb_eurofxref_hist_zip": {
                "path": "data/official/raw/ecb_eurofxref_hist.zip",
                "sha256": sha256_file(RAW_DIR / "ecb_eurofxref_hist.zip"),
            },
            "ecb_eurofxref_hist_csv": {
                "path": "data/official/raw/ecb_eurofxref_hist.csv",
                "sha256": sha256_file(RAW_DIR / "ecb_eurofxref_hist.csv"),
            },
        },
        "processed_files": {
            "usd_treasury_curve_nodes": {
                "path": "data/official/processed/usd_treasury_curve_nodes.csv",
                "rows": int(len(outputs["curve_nodes"])),
                "sha256": sha256_file(PROCESSED_DIR / "usd_treasury_curve_nodes.csv"),
            },
            "breakeven_inflation_panel": {
                "path": "data/official/processed/breakeven_inflation_panel.csv",
                "rows": int(len(outputs["inflation"])),
                "sha256": sha256_file(PROCESSED_DIR / "breakeven_inflation_panel.csv"),
            },
            "ecb_fx_panel": {
                "path": "data/official/processed/ecb_fx_panel.csv",
                "rows": int(len(outputs["fx"])),
                "sha256": sha256_file(PROCESSED_DIR / "ecb_fx_panel.csv"),
            },
            "official_rates_fx_inflation_panel": {
                "path": "data/official/processed/official_rates_fx_inflation_panel.csv",
                "rows": int(len(outputs["combined"])),
                "sha256": sha256_file(PROCESSED_DIR / "official_rates_fx_inflation_panel.csv"),
            },
            "fx_daily_returns": {
                "path": "data/official/processed/fx_daily_returns.csv",
                "rows": int(len(outputs["fx_returns"])),
                "sha256": sha256_file(PROCESSED_DIR / "fx_daily_returns.csv"),
            },
            "curve_validation_summary": {
                "path": "data/official/processed/curve_validation_summary.csv",
                "sha256": sha256_file(PROCESSED_DIR / "curve_validation_summary.csv"),
            },
            "fx_risk_summary": {
                "path": "data/official/processed/fx_risk_summary.csv",
                "sha256": sha256_file(PROCESSED_DIR / "fx_risk_summary.csv"),
            },
        },
    }

    (ROOT / "data" / "official" / "manifest.json").write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )


def write_report(curve_summary: pd.DataFrame, fx_risk_summary: pd.DataFrame, outputs: dict[str, pd.DataFrame]) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    latest_combined = outputs["combined"].dropna().tail(1)

    report = f"""# Official Rates, FX and Inflation Model-Risk Pipeline Report

## Executive summary

This report is generated from a real public official-data pipeline aligned with rates, FX, inflation and derivative-pricing model-risk workflows.

The pipeline downloads official interest-rate, inflation-compensation and FX data, stores raw files, builds processed panels, creates curve-validation summaries, computes FX return-risk metrics and generates reproducibility evidence through hashes and a manifest.

## Data sources

| Data block | Source |
|---|---|
| U.S. Treasury rates | FRED Treasury constant maturity series |
| Inflation compensation | FRED 10-year breakeven inflation |
| FX rates | ECB euro foreign exchange reference rates |

## Latest complete official-data row

{markdown_table(latest_combined)}

## Curve validation summary

{markdown_table(curve_summary)}

## FX risk summary

{markdown_table(fx_risk_summary)}

## Model-risk interpretation

This pipeline does not claim access to proprietary OTC derivative trades, XVA production inputs, internal bank curve systems or confidential model inventories.

It builds the closest public validation harness: real official data, raw-data storage, processed panels, curve checks, FX risk summaries, reproducibility hashes and documentation. This supports model-risk reasoning for IR, FX and inflation workflows without pretending to replicate a bank production environment.

## Generated artifacts

- data/official/raw/fred_us_rates_inflation.csv
- data/official/raw/ecb_eurofxref_hist.zip
- data/official/raw/ecb_eurofxref_hist.csv
- data/official/processed/usd_treasury_curve_nodes.csv
- data/official/processed/breakeven_inflation_panel.csv
- data/official/processed/ecb_fx_panel.csv
- data/official/processed/official_rates_fx_inflation_panel.csv
- data/official/processed/fx_daily_returns.csv
- data/official/processed/curve_validation_summary.csv
- data/official/processed/fx_risk_summary.csv
- data/official/manifest.json
"""

    (REPORTS_DIR / "official_rates_fx_inflation_pipeline_report.md").write_text(
        report,
        encoding="utf-8",
    )


def main() -> None:
    fred = download_fred_rates_and_inflation()
    fx = download_ecb_fx_rates()
    outputs = build_processed_panels(fred=fred, fx=fx)
    curve_summary = build_curve_validation_summary(outputs["curve_nodes"])
    fx_summary = build_fx_risk_summary(outputs["fx_returns"])

    write_manifest(outputs)
    write_report(curve_summary, fx_summary, outputs)

    print("Official rates, FX and inflation pipeline complete.")
    print("Generated report: reports/official_rates_fx_inflation_pipeline_report.md")
    print("Generated manifest: data/official/manifest.json")


if __name__ == "__main__":
    main()

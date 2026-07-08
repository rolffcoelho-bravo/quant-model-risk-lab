"""Run curve pricing validation harness from official public data."""

from __future__ import annotations

from pathlib import Path
import sys
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from qmrl.curve_pricing import (
    build_curve_pricing_result,
    build_discount_curve,
    build_parallel_shock_table,
    fixed_rate_bond_cashflows,
)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OFFICIAL_PROCESSED = ROOT / "data" / "official" / "processed"
REPORTS_DIR = ROOT / "reports"

RATE_COLUMNS = ["DGS1", "DGS2", "DGS5", "DGS10", "DGS30"]
MATURITIES = [1.0, 2.0, 5.0, 10.0, 30.0]
TARGET_MATURITIES = [1.0, 2.0, 3.0, 5.0, 7.0, 10.0, 30.0]


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


def load_latest_curve() -> tuple[str, list[float]]:
    curve_path = OFFICIAL_PROCESSED / "usd_treasury_curve_nodes.csv"
    curve = pd.read_csv(curve_path)
    curve = curve.dropna(subset=RATE_COLUMNS)

    if curve.empty:
        raise ValueError("No complete curve row available in usd_treasury_curve_nodes.csv.")

    latest = curve.tail(1).iloc[0]
    date = str(latest["date"])
    yields = [float(latest[column]) for column in RATE_COLUMNS]
    return date, yields


def write_report(
    latest_date: str,
    discount_curve: pd.DataFrame,
    cashflows: pd.DataFrame,
    shock_table: pd.DataFrame,
    bond_price: float,
    dv01: float,
    coupon_rate: float,
) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    report = f"""# Curve Pricing Validation Harness

## Executive summary

This report validates a simple curve-based pricing workflow using official public U.S. Treasury curve data already stored in the repository.

The harness transforms observed Treasury curve nodes into interpolated zero rates, discount factors, bond cashflows, a fixed-rate bond value, DV01 and parallel-shock valuation evidence.

This is not a production pricing engine. It is a transparent model-risk validation harness designed to show how valuation inputs, assumptions and sensitivities can be reviewed.

## Latest curve date

{latest_date}

## Instrument under review

| Field | Value |
|---|---|
| Instrument type | Fixed-rate bond validation instrument |
| Face value | 100 |
| Maturity | 5 years |
| Coupon rate | {coupon_rate:.6f} |
| Coupon frequency | Semiannual |
| Curve source | Official public Treasury curve nodes |
| Pricing method | Interpolated zero curve with continuous discounting |

## Discount curve

{markdown_table(discount_curve)}

## Bond cashflows

{markdown_table(cashflows)}

## Valuation result

| Metric | Value |
|---|---|
| Base clean-price proxy | {bond_price:.6f} |
| DV01 | {dv01:.6f} |

## Parallel shock table

{markdown_table(shock_table)}

## Model-risk interpretation

A model validator is not only checking whether a price was produced. The review must ask whether the market data are traceable, whether interpolation is documented, whether discounting assumptions are explicit, whether sensitivity behaves in the expected direction and whether valuation outputs can be reproduced.

This harness creates that evidence from public official data:

1. Curve nodes are read from the official-data pipeline.
2. Interpolated zero rates are generated at review maturities.
3. Discount factors are calculated transparently.
4. Bond cashflows are listed.
5. Base price and DV01 are computed.
6. Parallel rate shocks are applied.
7. Outputs are stored as reproducible CSV and markdown evidence.

## Limitation

The harness is intentionally simple. It does not claim to reproduce proprietary bank curve construction, bootstrapping, collateral curves, XVA, multi-curve frameworks, inflation swap curves or production derivative libraries.

Its purpose is public model-risk evidence: transparent inputs, explicit assumptions, sensitivity checks, reproducible outputs and tests.
"""

    (REPORTS_DIR / "curve_pricing_validation_harness.md").write_text(
        report,
        encoding="utf-8",
    )


def main() -> None:
    latest_date, yields = load_latest_curve()

    discount_curve = build_discount_curve(
        maturities_years=MATURITIES,
        yields_percent=yields,
        target_maturities_years=TARGET_MATURITIES,
    )

    coupon_rate = yields[2] / 100.0
    maturity_years = 5.0

    cashflows = fixed_rate_bond_cashflows(
        maturity_years=maturity_years,
        coupon_rate=coupon_rate,
        face_value=100.0,
        frequency=2,
    )

    pricing_result = build_curve_pricing_result(
        maturities_years=MATURITIES,
        yields_percent=yields,
        maturity_years=maturity_years,
        coupon_rate=coupon_rate,
        face_value=100.0,
        frequency=2,
    )

    shock_table = build_parallel_shock_table(
        maturities_years=MATURITIES,
        yields_percent=yields,
        maturity_years=maturity_years,
        coupon_rate=coupon_rate,
        face_value=100.0,
        frequency=2,
    )

    discount_curve.to_csv(
        OFFICIAL_PROCESSED / "curve_pricing_discount_curve.csv",
        index=False,
    )
    cashflows.to_csv(
        OFFICIAL_PROCESSED / "curve_pricing_cashflows.csv",
        index=False,
    )
    shock_table.to_csv(
        OFFICIAL_PROCESSED / "curve_pricing_parallel_shocks.csv",
        index=False,
    )

    pricing_summary = pd.DataFrame(
        [
            {
                "latest_curve_date": latest_date,
                "instrument": "fixed_rate_bond_validation_instrument",
                "maturity_years": maturity_years,
                "coupon_rate": coupon_rate,
                "price": pricing_result.price,
                "dv01": pricing_result.dv01,
            }
        ]
    )
    pricing_summary.to_csv(
        OFFICIAL_PROCESSED / "curve_pricing_summary.csv",
        index=False,
    )

    write_report(
        latest_date=latest_date,
        discount_curve=discount_curve,
        cashflows=cashflows,
        shock_table=shock_table,
        bond_price=pricing_result.price,
        dv01=pricing_result.dv01,
        coupon_rate=coupon_rate,
    )

    print("Curve pricing validation harness complete.")
    print("Generated report: reports/curve_pricing_validation_harness.md")
    print("Generated outputs:")
    print("- data/official/processed/curve_pricing_discount_curve.csv")
    print("- data/official/processed/curve_pricing_cashflows.csv")
    print("- data/official/processed/curve_pricing_parallel_shocks.csv")
    print("- data/official/processed/curve_pricing_summary.csv")


if __name__ == "__main__":
    main()




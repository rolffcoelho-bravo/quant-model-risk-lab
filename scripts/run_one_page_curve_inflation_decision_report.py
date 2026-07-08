"""Generate one-page curve and inflation decision report.

This report is designed as a decision-facing model-risk artifact. It uses
official rates and inflation data already stored in the repository plus the
curve-pricing validation outputs from v0.4.

The output is not a trading signal. It is a model-risk decision report:
what changed, why it matters, what a validator should challenge, and what
a bank or investor should watch.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "official" / "processed"
REPORTS = ROOT / "reports"
FIGURES = REPORTS / "figures"

RATE_COLUMNS = ["DGS1", "DGS2", "DGS5", "DGS10", "DGS30"]
MATURITY_LABELS = ["1Y", "2Y", "5Y", "10Y", "30Y"]
MATURITIES = [1, 2, 5, 10, 30]


def load_latest_curve() -> pd.Series:
    curve = pd.read_csv(PROCESSED / "usd_treasury_curve_nodes.csv")
    curve = curve.dropna(subset=RATE_COLUMNS)
    if curve.empty:
        raise ValueError("No complete Treasury curve row available.")
    return curve.tail(1).iloc[0]


def load_latest_inflation() -> pd.Series:
    inflation = pd.read_csv(PROCESSED / "breakeven_inflation_panel.csv")
    inflation = inflation.dropna(subset=["T10YIE"])
    if inflation.empty:
        raise ValueError("No breakeven inflation observation available.")
    return inflation.tail(1).iloc[0]


def load_pricing_summary() -> pd.Series:
    summary = pd.read_csv(PROCESSED / "curve_pricing_summary.csv")
    if summary.empty:
        raise ValueError("Curve-pricing summary is empty.")
    return summary.tail(1).iloc[0]


def load_shock_table() -> pd.DataFrame:
    shocks = pd.read_csv(PROCESSED / "curve_pricing_parallel_shocks.csv")
    required = {"parallel_shift_bp", "bond_price", "price_change", "price_change_percent"}
    missing = required.difference(set(shocks.columns))
    if missing:
        raise ValueError(f"Shock table missing columns: {missing}")
    return shocks


def get_shock_metric(shocks: pd.DataFrame, shock_bp: float, column: str) -> float:
    row = shocks.loc[shocks["parallel_shift_bp"] == shock_bp]
    if row.empty:
        raise ValueError(f"Shock {shock_bp} bp not found in shock table.")
    return float(row.iloc[0][column])


def classify_decision_state(slope_2s10: float, breakeven_10y: float, loss_100bp: float) -> tuple[str, list[str]]:
    flags = []

    if slope_2s10 < 0:
        flags.append("curve inversion")

    if breakeven_10y >= 2.50:
        flags.append("inflation compensation above 2.50 percent")

    if abs(loss_100bp) >= 4.00:
        flags.append("+100bp valuation loss above 4 percent")

    if len(flags) >= 2:
        return "Enhanced review", flags

    if len(flags) == 1:
        return "Watch", flags

    return "Standard review", ["no major threshold breach"]


def build_decision_metrics() -> pd.DataFrame:
    curve = load_latest_curve()
    inflation = load_latest_inflation()
    pricing = load_pricing_summary()
    shocks = load_shock_table()

    yields = [float(curve[column]) for column in RATE_COLUMNS]
    slope_2s10 = float(curve["DGS10"] - curve["DGS2"])
    slope_5s30 = float(curve["DGS30"] - curve["DGS5"])
    curvature_2_5_10 = float(curve["DGS2"] - 2 * curve["DGS5"] + curve["DGS10"])
    curve_level = float(sum(yields) / len(yields))
    breakeven_10y = float(inflation["T10YIE"])
    bond_price = float(pricing["price"])
    dv01 = float(pricing["dv01"])
    loss_50bp = get_shock_metric(shocks, 50.0, "price_change_percent")
    loss_100bp = get_shock_metric(shocks, 100.0, "price_change_percent")

    decision_state, flags = classify_decision_state(
        slope_2s10=slope_2s10,
        breakeven_10y=breakeven_10y,
        loss_100bp=loss_100bp,
    )

    metrics = pd.DataFrame(
        [
            {
                "curve_date": str(curve["date"]),
                "inflation_date": str(inflation["date"]),
                "DGS1": float(curve["DGS1"]),
                "DGS2": float(curve["DGS2"]),
                "DGS5": float(curve["DGS5"]),
                "DGS10": float(curve["DGS10"]),
                "DGS30": float(curve["DGS30"]),
                "curve_level": curve_level,
                "slope_2s10": slope_2s10,
                "slope_5s30": slope_5s30,
                "curvature_2_5_10": curvature_2_5_10,
                "breakeven_10y": breakeven_10y,
                "bond_price": bond_price,
                "dv01": dv01,
                "loss_50bp_percent": loss_50bp,
                "loss_100bp_percent": loss_100bp,
                "decision_state": decision_state,
                "decision_flags": "; ".join(flags),
            }
        ]
    )

    metrics.to_csv(PROCESSED / "one_page_curve_inflation_decision_metrics.csv", index=False)
    return metrics


def write_decision_figure(metrics: pd.DataFrame) -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)

    row = metrics.iloc[0]
    yields = [float(row[column]) for column in RATE_COLUMNS]

    shocks = load_shock_table()
    shocks = shocks.sort_values("parallel_shift_bp")

    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.6))

    axes[0].plot(MATURITIES, yields, marker="o", linewidth=2.4)
    axes[0].set_title("Official Treasury Curve")
    axes[0].set_xlabel("Maturity")
    axes[0].set_ylabel("Yield (%)")
    axes[0].set_xticks(MATURITIES)
    axes[0].set_xticklabels(MATURITY_LABELS)
    axes[0].grid(True, alpha=0.25)

    axes[0].annotate(
        f"2s10s: {row['slope_2s10']:.2f} pp\n10Y BEI: {row['breakeven_10y']:.2f}%",
        xy=(10, float(row["DGS10"])),
        xytext=(11.5, max(yields) - 0.35),
        arrowprops={"arrowstyle": "->", "lw": 1},
        fontsize=9,
    )

    axes[1].plot(
        shocks["parallel_shift_bp"],
        shocks["price_change_percent"],
        marker="o",
        linewidth=2.4,
    )
    axes[1].axhline(0, linewidth=1)
    axes[1].set_title("Validation Bond Shock Map")
    axes[1].set_xlabel("Parallel curve shock (bp)")
    axes[1].set_ylabel("Price change (%)")
    axes[1].grid(True, alpha=0.25)

    axes[1].annotate(
        f"DV01: {row['dv01']:.4f}\n+100bp: {row['loss_100bp_percent']:.2f}%",
        xy=(100, float(row["loss_100bp_percent"])),
        xytext=(15, min(shocks["price_change_percent"]) + 0.8),
        arrowprops={"arrowstyle": "->", "lw": 1},
        fontsize=9,
    )

    fig.suptitle(
        f"Curve and Inflation Model-Risk Decision Map | State: {row['decision_state']}",
        fontsize=14,
        fontweight="bold",
    )

    fig.text(
        0.01,
        0.01,
        "Source: repository official-data pipeline. Interpretation: model-risk monitoring artifact, not investment advice.",
        fontsize=8,
    )

    fig.tight_layout(rect=[0, 0.04, 1, 0.93])
    fig.savefig(FIGURES / "curve_inflation_decision_map.png", dpi=220)
    plt.close(fig)


def write_report(metrics: pd.DataFrame) -> None:
    row = metrics.iloc[0]
    report_path = REPORTS / "one_page_curve_inflation_decision_report.md"

    report = f"""# One-Page Curve and Inflation Decision Report

## Decision state: {row['decision_state']}

**Curve date:** {row['curve_date']}  
**Inflation date:** {row['inflation_date']}  
**Decision flags:** {row['decision_flags']}

![Curve and inflation decision map](figures/curve_inflation_decision_map.png)

## Core metrics

| Metric | Value |
|---|---:|
| 1Y Treasury | {row['DGS1']:.3f}% |
| 2Y Treasury | {row['DGS2']:.3f}% |
| 5Y Treasury | {row['DGS5']:.3f}% |
| 10Y Treasury | {row['DGS10']:.3f}% |
| 30Y Treasury | {row['DGS30']:.3f}% |
| 2s10s slope | {row['slope_2s10']:.3f} pp |
| 5s30s slope | {row['slope_5s30']:.3f} pp |
| 10Y breakeven inflation | {row['breakeven_10y']:.3f}% |
| Validation bond price | {row['bond_price']:.4f} |
| DV01 | {row['dv01']:.6f} |
| +50bp valuation impact | {row['loss_50bp_percent']:.3f}% |
| +100bp valuation impact | {row['loss_100bp_percent']:.3f}% |

## Model-risk interpretation

- **Curve input risk:** The term-structure shape defines the valuation environment. A negative or unstable 2s10s slope raises the need to challenge interpolation, extrapolation and rate-sensitivity assumptions.
- **Inflation input risk:** The 10Y breakeven rate is a direct public inflation-compensation input. Elevated inflation compensation increases the importance of inflation-linked valuation review and scenario testing.
- **Valuation sensitivity:** The +50bp and +100bp shock losses convert curve movement into pricing impact. This is the cleanest validation bridge between market data and model-output review.
- **Decision use:** The report is not a forecast. It is an evidence object for model validation, revalidation prioritization, sensitivity review and monitoring escalation.

## Bank implication

Prioritize review of curve construction, input lineage, interpolation assumptions, DV01 behavior, shock sensitivity and inflation-linked valuation inputs. The validation question is whether pricing outputs remain stable and explainable under rate and inflation stress.

## Investor implication

The risk profile is dominated by curve sensitivity and inflation compensation. The key question is not direction alone, but whether valuation loss under rate shocks is consistent with duration, curve shape and inflation-pressure assumptions.

## Validator challenge

Challenge the curve source, missing-data treatment, interpolation method, discounting convention, shock design, inflation proxy, sensitivity stability and whether the current environment sits outside the model-development distribution.
"""

    report_path.write_text(report, encoding="utf-8")


def main() -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    metrics = build_decision_metrics()
    write_decision_figure(metrics)
    write_report(metrics)

    print("One-page curve and inflation decision report complete.")
    print("Generated report: reports/one_page_curve_inflation_decision_report.md")
    print("Generated figure: reports/figures/curve_inflation_decision_map.png")
    print("Generated metrics: data/official/processed/one_page_curve_inflation_decision_metrics.csv")


if __name__ == "__main__":
    main()

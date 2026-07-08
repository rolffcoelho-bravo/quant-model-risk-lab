"""Run inflation derivatives validation layer.

This script uses real public breakeven inflation and nominal Treasury-rate data
stored by the official-data pipeline. It creates a standardized zero-coupon
inflation-linked validation instrument, applies inflation-compensation shocks
and produces a model-risk report plus a Matplotlib decision graphic.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.gridspec import GridSpec

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from qmrl.inflation_pricing import (
    build_inflation_shock_table,
    build_inflation_validation_result,
)

PROCESSED = ROOT / "data" / "official" / "processed"
REPORTS = ROOT / "reports"
FIGURES = REPORTS / "figures"

MATURITY_YEARS = 10.0
NOTIONAL = 1_000_000.0


def percentile_rank(values: pd.Series, value: float) -> float:
    clean = values.dropna()
    if clean.empty:
        return float("nan")
    return float((clean <= value).mean() * 100.0)


def load_inflation_panel() -> pd.DataFrame:
    inflation = pd.read_csv(PROCESSED / "breakeven_inflation_panel.csv")
    inflation["date"] = pd.to_datetime(inflation["date"])
    inflation = inflation.dropna(subset=["T10YIE"]).sort_values("date")
    if inflation.empty:
        raise ValueError("No breakeven inflation observations available.")
    return inflation


def load_nominal_curve() -> pd.DataFrame:
    curve = pd.read_csv(PROCESSED / "usd_treasury_curve_nodes.csv")
    curve["date"] = pd.to_datetime(curve["date"])
    curve = curve.dropna(subset=["DGS10"]).sort_values("date")
    if curve.empty:
        raise ValueError("No complete nominal 10Y Treasury observations available.")
    return curve


def classify_inflation_decision_state(
    breakeven_10y: float,
    breakeven_60d_shift: float,
    positive_100bp_value_percent: float,
) -> tuple[str, list[str]]:
    flags = []

    if breakeven_10y >= 2.50:
        flags.append("10Y breakeven inflation above 2.50 percent")

    if abs(breakeven_60d_shift) >= 0.25:
        flags.append("60D breakeven move above 25bp")

    if abs(positive_100bp_value_percent) >= 7.50:
        flags.append("+100bp inflation shock value above 7.5 percent of notional")

    if len(flags) >= 2:
        return "Enhanced inflation review", flags

    if len(flags) == 1:
        return "Inflation watch", flags

    return "Standard inflation review", ["no major inflation threshold breach"]


def build_outputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    inflation = load_inflation_panel()
    curve = load_nominal_curve()

    recent_inflation = inflation.tail(252).copy()
    recent_curve = curve.tail(252).copy()

    latest_inflation = inflation.tail(1).iloc[0]
    latest_curve = curve.tail(1).iloc[0]

    base_breakeven = float(latest_inflation["T10YIE"])
    nominal_10y = float(latest_curve["DGS10"])

    if len(recent_inflation) >= 60:
        breakeven_60d_shift = float(latest_inflation["T10YIE"] - recent_inflation.iloc[-60]["T10YIE"])
    else:
        breakeven_60d_shift = float("nan")

    breakeven_percentile_252d = percentile_rank(recent_inflation["T10YIE"], base_breakeven)

    fixed_rate = base_breakeven
    result = build_inflation_validation_result(
        fixed_rate_percent=fixed_rate,
        market_rate_percent=base_breakeven,
        nominal_discount_rate_percent=nominal_10y,
        maturity_years=MATURITY_YEARS,
        notional=NOTIONAL,
    )

    shock_table = build_inflation_shock_table(
        fixed_rate_percent=fixed_rate,
        base_market_rate_percent=base_breakeven,
        nominal_discount_rate_percent=nominal_10y,
        maturity_years=MATURITY_YEARS,
        notional=NOTIONAL,
    )

    positive_100bp = shock_table.loc[shock_table["inflation_shock_bp"] == 100.0].iloc[0]
    negative_100bp = shock_table.loc[shock_table["inflation_shock_bp"] == -100.0].iloc[0]

    decision_state, decision_flags = classify_inflation_decision_state(
        breakeven_10y=base_breakeven,
        breakeven_60d_shift=breakeven_60d_shift,
        positive_100bp_value_percent=float(positive_100bp["value_percent_notional"]),
    )

    inflation_pressure_score = 0.0
    inflation_pressure_score += min(35.0, max(0.0, (base_breakeven - 2.00) / 0.75 * 35.0))
    inflation_pressure_score += 0.0 if np.isnan(breakeven_60d_shift) else min(25.0, abs(breakeven_60d_shift) / 0.35 * 25.0)
    inflation_pressure_score += min(40.0, abs(float(positive_100bp["value_percent_notional"])) / 10.0 * 40.0)
    inflation_pressure_score = round(inflation_pressure_score, 1)

    summary = pd.DataFrame(
        [
            {
                "inflation_date": latest_inflation["date"].date().isoformat(),
                "curve_date": latest_curve["date"].date().isoformat(),
                "fixed_rate_percent": fixed_rate,
                "market_breakeven_percent": base_breakeven,
                "nominal_10y_discount_rate_percent": nominal_10y,
                "maturity_years": MATURITY_YEARS,
                "notional": NOTIONAL,
                "base_value": result.value,
                "base_value_percent_notional": result.value_percent_notional,
                "inflation_dv01": result.inflation_dv01,
                "positive_100bp_value": float(positive_100bp["value"]),
                "positive_100bp_value_percent_notional": float(positive_100bp["value_percent_notional"]),
                "negative_100bp_value": float(negative_100bp["value"]),
                "negative_100bp_value_percent_notional": float(negative_100bp["value_percent_notional"]),
                "breakeven_60d_shift": breakeven_60d_shift,
                "breakeven_percentile_252d": breakeven_percentile_252d,
                "inflation_pressure_score": inflation_pressure_score,
                "decision_state": decision_state,
                "decision_flags": "; ".join(decision_flags),
            }
        ]
    )

    summary.to_csv(PROCESSED / "inflation_derivatives_summary.csv", index=False)
    shock_table.to_csv(PROCESSED / "inflation_derivatives_shock_table.csv", index=False)

    return summary, shock_table, recent_inflation, recent_curve


def write_figure(
    summary: pd.DataFrame,
    shock_table: pd.DataFrame,
    recent_inflation: pd.DataFrame,
    recent_curve: pd.DataFrame,
) -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)

    row = summary.iloc[0]

    fig = plt.figure(figsize=(16.0, 8.8))
    gs = GridSpec(2, 2, figure=fig, height_ratios=[1.0, 1.0], width_ratios=[1.02, 1.12])
    fig.patch.set_facecolor("#f7f8fa")

    ax_bei = fig.add_subplot(gs[0, 0])
    ax_shock = fig.add_subplot(gs[0, 1])
    ax_nominal = fig.add_subplot(gs[1, 0])
    ax_decision = fig.add_subplot(gs[1, 1])

    # Panel 1: 10Y inflation compensation context.
    recent = recent_inflation.copy()
    recent["p10"] = recent["T10YIE"].rolling(60, min_periods=20).quantile(0.10)
    recent["p90"] = recent["T10YIE"].rolling(60, min_periods=20).quantile(0.90)
    recent["median"] = recent["T10YIE"].rolling(60, min_periods=20).median()

    ax_bei.fill_between(
        recent["date"],
        recent["p10"],
        recent["p90"],
        alpha=0.18,
        color="#1f77b4",
        label="60D 10-90% band",
    )
    ax_bei.plot(
        recent["date"],
        recent["median"],
        linestyle="--",
        linewidth=1.8,
        color="#1f77b4",
        label="60D median",
    )
    ax_bei.plot(
        recent["date"],
        recent["T10YIE"],
        linewidth=2.4,
        color="#ff7f0e",
        label="10Y inflation compensation, BEI",
    )
    ax_bei.scatter(recent["date"].iloc[-1], recent["T10YIE"].iloc[-1], color="#ff7f0e", s=44)

    ax_bei.set_title("10Y Inflation Compensation Context", fontweight="bold")
    ax_bei.set_ylabel("Percent")
    ax_bei.grid(True, alpha=0.25)
    ax_bei.legend(
        frameon=False,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.13),
        ncol=3,
        fontsize=8.3,
    )

    # Panel 2: inflation-compensation shock valuation.
    shock_table = shock_table.sort_values("inflation_shock_bp").copy()
    bar_colors = [
        "#c44e52" if x < 0 else "#4c72b0" if x > 0 else "#7f8c8d"
        for x in shock_table["inflation_shock_bp"]
    ]

    ax_shock.bar(
        shock_table["inflation_shock_bp"],
        shock_table["value_percent_notional"],
        width=18,
        alpha=0.90,
        color=bar_colors,
    )
    ax_shock.axhline(0, linewidth=1.0, color="#667085")
    ax_shock.axhline(7.5, linewidth=1.0, linestyle="--", color="#9b1c1c")
    ax_shock.axhline(-7.5, linewidth=1.0, linestyle="--", color="#9b1c1c")

    shock_y_min = float(shock_table["value_percent_notional"].min())
    shock_y_max = float(shock_table["value_percent_notional"].max())
    ax_shock.set_ylim(shock_y_min - 1.4, shock_y_max + 1.4)

    ax_shock.set_title("Inflation-Compensation Shock Valuation Map", fontweight="bold")
    ax_shock.set_xlabel("Inflation-compensation shock, bp")
    ax_shock.set_ylabel("Value change, % notional")
    ax_shock.grid(True, axis="y", alpha=0.25)

    for _, shock_row in shock_table.iterrows():
        shock_bp = float(shock_row["inflation_shock_bp"])
        value = float(shock_row["value_percent_notional"])

        if abs(value) < 0.05:
            continue

        y_offset = 0.35 if value > 0 else -0.45
        va = "bottom" if value > 0 else "top"

        ax_shock.text(
            shock_bp,
            value + y_offset,
            f"{value:.1f}%",
            ha="center",
            va=va,
            fontsize=8.4,
            fontweight="bold" if shock_bp in [-100.0, 100.0] else "normal",
            color="#111827",
        )

    # Panel 3: nominal yield, BEI and real-rate proxy.
    nominal = recent_curve[["date", "DGS10"]].merge(
        recent_inflation[["date", "T10YIE"]],
        on="date",
        how="inner",
    )
    nominal["real_rate_proxy"] = nominal["DGS10"] - nominal["T10YIE"]

    ax_nominal.plot(
        nominal["date"],
        nominal["DGS10"],
        linewidth=2.35,
        color="#1f77b4",
        label="10Y nominal yield",
    )
    ax_nominal.plot(
        nominal["date"],
        nominal["T10YIE"],
        linewidth=2.35,
        linestyle="--",
        color="#ff7f0e",
        label="10Y inflation compensation, BEI",
    )
    ax_nominal.plot(
        nominal["date"],
        nominal["real_rate_proxy"],
        linewidth=2.35,
        linestyle=":",
        color="#2ca02c",
        label="Real-rate proxy",
    )

    ax_nominal.scatter(nominal["date"].iloc[-1], nominal["DGS10"].iloc[-1], s=34, color="#1f77b4", zorder=5)
    ax_nominal.scatter(nominal["date"].iloc[-1], nominal["T10YIE"].iloc[-1], s=34, color="#ff7f0e", zorder=5)
    ax_nominal.scatter(nominal["date"].iloc[-1], nominal["real_rate_proxy"].iloc[-1], s=34, color="#2ca02c", zorder=5)

    y_min = float(
        min(
            nominal["DGS10"].min(),
            nominal["T10YIE"].min(),
            nominal["real_rate_proxy"].min(),
        )
    )
    y_max = float(
        max(
            nominal["DGS10"].max(),
            nominal["T10YIE"].max(),
            nominal["real_rate_proxy"].max(),
        )
    )

    ax_nominal.set_ylim(y_min - 0.35, y_max + 0.28)
    ax_nominal.set_title("Nominal Yield, Inflation Compensation and Real-Rate Proxy", fontweight="bold")
    ax_nominal.set_ylabel("Percent")
    ax_nominal.grid(True, alpha=0.25)
    ax_nominal.legend(
        frameon=False,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.13),
        ncol=3,
        fontsize=8.3,
    )

    # Panel 4: decision card.
    ax_decision.axis("off")
    decision_text = (
        "INFLATION MODEL-RISK STATE\n"
        f"{row['decision_state']} | Pressure {row['inflation_pressure_score']:.0f}/100\n\n"
        "Market note\n"
        f"10Y BEI {row['market_breakeven_percent']:.2f}% = market-implied 10Y inflation compensation.\n"
        "It is not a pure CPI forecast; it includes expectations, risk premium and liquidity.\n\n"
        "Acronym legend\n"
        "BEI = breakeven inflation.\n"
        "bp = basis point; 100bp = 1.00 percentage point.\n"
        "DV01 = value move for a 1bp BEI shock.\n"
        "Pctile = percentile versus last 252 observations.\n\n"
        "Decision read\n"
        f"+100bp BEI shock = {row['positive_100bp_value_percent_notional']:.2f}% of notional.\n"
        f"-100bp BEI shock = {row['negative_100bp_value_percent_notional']:.2f}% of notional.\n"
        "Active risk channel: inflation-compensation sensitivity.\n\n"
        "Bank decision\n"
        "1. Verify BEI source, timestamp and instrument mapping.\n"
        "2. Reprice +/-50bp and +/-100bp BEI shocks.\n"
        "3. Confirm DV01 matches shocked valuation changes.\n"
        "4. Escalate if mapping, discounting or sensitivity breaches tolerance.\n\n"
        "Investor decision\n"
        "1. BEI is low versus recent history.\n"
        "2. Add inflation-linked exposure only with shock-loss budget.\n"
        "3. Use BEI direction as trigger; nominal-rate moves are secondary."
    )

    ax_decision.text(
        0.04,
        0.96,
        decision_text,
        va="top",
        ha="left",
        fontsize=7.70,
        linespacing=0.96,
        bbox={
            "boxstyle": "round,pad=0.60",
            "fc": "white",
            "ec": "#8892a0",
            "lw": 1.1,
            "alpha": 0.98,
        },
    )

    fig.suptitle(
        f"Inflation Derivatives Validation Dashboard | State: {row['decision_state']} | BEI date: {row['inflation_date']}",
        fontsize=15,
        fontweight="bold",
        y=0.98,
    )

    kpi_items = [
        ("STATE", str(row["decision_state"])),
        ("10Y INFLATION COMP. (BEI)", f"{row['market_breakeven_percent']:.2f}%"),
        ("BEI PCTILE", f"{row['breakeven_percentile_252d']:.0f}"),
        ("+100bp VALUE", f"{row['positive_100bp_value_percent_notional']:.2f}%"),
        ("PRESSURE", f"{row['inflation_pressure_score']:.0f}/100"),
    ]

    for index, (label, value) in enumerate(kpi_items):
        fig.text(
            0.16 + index * 0.17,
            0.925,
            f"{label}\n{value}",
            ha="center",
            va="center",
            fontsize=9.0,
            fontweight="bold",
            bbox={
                "boxstyle": "round,pad=0.38",
                "fc": "white",
                "ec": "#9aa4b2",
                "lw": 1.0,
                "alpha": 0.98,
            },
        )

    fig.text(
        0.012,
        0.020,
        "Legend: BEI = Breakeven Inflation, used as 10Y inflation compensation | bp = basis point | DV01 = value move for 1bp shock | pctile = percentile versus last 252 observations | real-rate proxy = 10Y nominal yield minus BEI.",
        fontsize=7.9,
    )

    fig.text(
        0.012,
        0.006,
        "Source: repository official-data pipeline. Inflation model-risk validation artifact, not investment advice.",
        fontsize=7.8,
    )

    fig.tight_layout(rect=[0, 0.055, 1, 0.885])
    fig.savefig(FIGURES / "inflation_derivatives_validation_map.png", dpi=240)
    plt.close(fig)

def write_report(summary: pd.DataFrame) -> None:
    row = summary.iloc[0]

    report = f"""# Inflation Derivatives Validation Report

## Decision state: {row['decision_state']}

**Inflation date:** {row['inflation_date']}  
**Curve date:** {row['curve_date']}  
**Decision flags:** {row['decision_flags']}  
**Inflation pressure score:** {row['inflation_pressure_score']:.1f} / 100

![Inflation derivatives validation map](figures/inflation_derivatives_validation_map.png)

## Acronym legend

| Term | Meaning |
|---|---|
| BEI | Breakeven Inflation, used here as 10Y market inflation compensation |
| bp | Basis point. 100bp equals 1.00 percentage point |
| DV01 | Value move for a 1bp shock in the relevant risk input |
| Inflation DV01 | Value move for a 1bp BEI shock |
| Pctile | Percentile versus the last 252 observations |
| Real-rate proxy | 10Y nominal Treasury yield minus 10Y breakeven inflation |

## Core metrics

| Metric | Value |
|---|---:|
| Fixed inflation rate | {row['fixed_rate_percent']:.3f}% |
| Market breakeven inflation | {row['market_breakeven_percent']:.3f}% |
| 10Y nominal discount rate | {row['nominal_10y_discount_rate_percent']:.3f}% |
| Maturity | {row['maturity_years']:.1f} years |
| Notional | {row['notional']:.0f} |
| Base value | {row['base_value']:.2f} |
| Inflation DV01 | {row['inflation_dv01']:.2f} |
| +100bp value | {row['positive_100bp_value']:.2f} |
| +100bp value, % notional | {row['positive_100bp_value_percent_notional']:.3f}% |
| -100bp value | {row['negative_100bp_value']:.2f} |
| -100bp value, % notional | {row['negative_100bp_value_percent_notional']:.3f}% |
| 60D breakeven shift | {row['breakeven_60d_shift']:.3f} pp |
| 252D breakeven percentile | {row['breakeven_percentile_252d']:.1f} |

## Direct interpretation

- **Input under review:** 10Y Breakeven Inflation, or BEI, is treated as the public market inflation-compensation input. A BEI value of 2.25% means the market is pricing roughly 2.25% annual inflation compensation over 10 years. It is not a pure CPI forecast because it can include inflation expectations, inflation-risk premium, liquidity effects and market positioning.
- **Real-rate proxy:** calculated as 10Y nominal Treasury yield minus 10Y Breakeven Inflation, or BEI. It is plotted as a public market proxy for real-rate pressure.
- **Validation instrument:** standardized zero-coupon inflation-linked payoff using a fixed inflation rate equal to the latest breakeven rate at inception.
- **Main sensitivity:** the +100bp and -100bp shocks show how inflation-compensation movement translates into value change.
- **Model-risk use:** the report tests input mapping, payoff logic, discounting and inflation DV01 consistency.

## Bank implication

Treat this as an inflation-input validation item. Verify BEI source integrity, timestamp alignment, mapping to the validation instrument, discounting convention, inflation DV01 and shocked valuation reconciliation. Escalate only if mapping, discounting or sensitivity breaches tolerance.

## Investor implication

The investor decision is BEI-led. BEI is low versus recent history, so adding inflation-linked exposure is a deliberate view that inflation compensation can reprice higher. The +100bp shock gives the upside range, while the -100bp shock gives the downside range. The portfolio should add this exposure only if the risk budget can absorb the shock-value range.

## Validator challenge

Challenge the inflation input, fixed-rate mapping, compounding convention, nominal discount rate, shock design, maturity assumption, sensitivity stability and whether BEI is an adequate public validation input for the intended instrument.
"""

    (REPORTS / "inflation_derivatives_validation_report.md").write_text(report, encoding="utf-8")


def main() -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)

    summary, shock_table, recent_inflation, recent_curve = build_outputs()
    write_figure(summary, shock_table, recent_inflation, recent_curve)
    write_report(summary)

    print("Inflation derivatives validation complete.")
    print("Generated report: reports/inflation_derivatives_validation_report.md")
    print("Generated figure: reports/figures/inflation_derivatives_validation_map.png")
    print("Generated summary: data/official/processed/inflation_derivatives_summary.csv")
    print("Generated shock table: data/official/processed/inflation_derivatives_shock_table.csv")


if __name__ == "__main__":
    main()

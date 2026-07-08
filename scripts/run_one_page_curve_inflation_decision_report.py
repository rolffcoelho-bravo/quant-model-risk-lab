"""Generate one-page curve and inflation decision report.

Bank-facing model-risk dashboard using real official rates and inflation data
already stored in the repository.

This is not a trading signal. It is a validation and monitoring artifact:
curve context, inflation pressure, valuation sensitivity, shock surface and
decision escalation.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.gridspec import GridSpec
from matplotlib.patches import Rectangle

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from qmrl.curve_pricing import interpolate_zero_rate, price_fixed_rate_bond_from_curve

PROCESSED = ROOT / "data" / "official" / "processed"
REPORTS = ROOT / "reports"
FIGURES = REPORTS / "figures"

RATE_COLUMNS = ["DGS1", "DGS2", "DGS5", "DGS10", "DGS30"]
MATURITY_LABELS = ["1Y", "2Y", "5Y", "10Y", "30Y"]
MATURITIES = [1.0, 2.0, 5.0, 10.0, 30.0]


def load_curve_panel() -> pd.DataFrame:
    curve = pd.read_csv(PROCESSED / "usd_treasury_curve_nodes.csv")
    curve["date"] = pd.to_datetime(curve["date"])
    curve = curve.dropna(subset=RATE_COLUMNS).sort_values("date")
    if curve.empty:
        raise ValueError("No complete Treasury curve rows available.")
    return curve


def load_inflation_panel() -> pd.DataFrame:
    inflation = pd.read_csv(PROCESSED / "breakeven_inflation_panel.csv")
    inflation["date"] = pd.to_datetime(inflation["date"])
    inflation = inflation.dropna(subset=["T10YIE"]).sort_values("date")
    if inflation.empty:
        raise ValueError("No breakeven inflation observations available.")
    return inflation


def load_pricing_summary() -> pd.Series:
    summary = pd.read_csv(PROCESSED / "curve_pricing_summary.csv")
    if summary.empty:
        raise ValueError("Curve-pricing summary is empty.")
    return summary.tail(1).iloc[0]


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


def percentile_rank(values: pd.Series, value: float) -> float:
    clean = values.dropna()
    if clean.empty:
        return float("nan")
    return float((clean <= value).mean() * 100.0)


def build_validation_shock_surface(yields: list[float]) -> pd.DataFrame:
    tenors = [2.0, 5.0, 10.0, 30.0]
    shocks = [-150.0, -100.0, -50.0, 0.0, 50.0, 100.0, 150.0]

    rows = []
    for tenor in tenors:
        coupon_rate = interpolate_zero_rate(MATURITIES, yields, tenor) / 100.0
        base_price = price_fixed_rate_bond_from_curve(
            maturities_years=MATURITIES,
            yields_percent=yields,
            maturity_years=tenor,
            coupon_rate=coupon_rate,
            face_value=100.0,
            frequency=2,
            parallel_shift_bp=0.0,
        )

        for shock in shocks:
            shocked_price = price_fixed_rate_bond_from_curve(
                maturities_years=MATURITIES,
                yields_percent=yields,
                maturity_years=tenor,
                coupon_rate=coupon_rate,
                face_value=100.0,
                frequency=2,
                parallel_shift_bp=shock,
            )
            rows.append(
                {
                    "tenor_years": tenor,
                    "parallel_shift_bp": shock,
                    "base_price": base_price,
                    "shocked_price": shocked_price,
                    "price_change_percent": (shocked_price / base_price - 1.0) * 100.0,
                }
            )

    surface = pd.DataFrame(rows)
    surface.to_csv(PROCESSED / "curve_inflation_decision_shock_surface.csv", index=False)
    return surface


def build_decision_metrics() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    curve = load_curve_panel()
    inflation = load_inflation_panel()
    pricing = load_pricing_summary()

    latest_curve = curve.tail(1).iloc[0]
    latest_inflation = inflation.tail(1).iloc[0]

    recent_curve = curve.tail(252).copy()
    recent_inflation = inflation.tail(252).copy()

    yields = [float(latest_curve[column]) for column in RATE_COLUMNS]
    surface = build_validation_shock_surface(yields)

    validation_5y = surface.loc[surface["tenor_years"] == 5.0].copy()

    slope_2s10 = float(latest_curve["DGS10"] - latest_curve["DGS2"])
    slope_5s30 = float(latest_curve["DGS30"] - latest_curve["DGS5"])
    curvature_2_5_10 = float(latest_curve["DGS2"] - 2 * latest_curve["DGS5"] + latest_curve["DGS10"])
    curve_level = float(np.mean(yields))

    breakeven_10y = float(latest_inflation["T10YIE"])
    bond_price = float(pricing["price"])
    dv01 = float(pricing["dv01"])
    loss_50bp = get_shock_metric(validation_5y, 50.0, "price_change_percent")
    loss_100bp = get_shock_metric(validation_5y, 100.0, "price_change_percent")

    decision_state, flags = classify_decision_state(
        slope_2s10=slope_2s10,
        breakeven_10y=breakeven_10y,
        loss_100bp=loss_100bp,
    )

    dgs10_60d_shift = float(latest_curve["DGS10"] - recent_curve.iloc[-60]["DGS10"]) if len(recent_curve) >= 60 else np.nan
    breakeven_60d_shift = float(latest_inflation["T10YIE"] - recent_inflation.iloc[-60]["T10YIE"]) if len(recent_inflation) >= 60 else np.nan

    recent_curve["slope_2s10"] = recent_curve["DGS10"] - recent_curve["DGS2"]

    dgs10_percentile_252d = percentile_rank(recent_curve["DGS10"], float(latest_curve["DGS10"]))
    slope_2s10_percentile_252d = percentile_rank(recent_curve["slope_2s10"], slope_2s10)
    breakeven_percentile_252d = percentile_rank(recent_inflation["T10YIE"], breakeven_10y)

    loss_score = min(40.0, abs(loss_100bp) / 6.0 * 40.0)
    inflation_score = min(25.0, max(0.0, (breakeven_10y - 2.00) / 0.75 * 25.0))
    slope_score = 20.0 if slope_2s10 < 0 else max(0.0, min(20.0, (0.50 - slope_2s10) / 0.50 * 20.0))
    move_score = 0.0 if np.isnan(dgs10_60d_shift) else min(15.0, abs(dgs10_60d_shift) / 0.50 * 15.0)
    validation_pressure_score = round(loss_score + inflation_score + slope_score + move_score, 1)

    metrics = pd.DataFrame(
        [
            {
                "curve_date": latest_curve["date"].date().isoformat(),
                "inflation_date": latest_inflation["date"].date().isoformat(),
                "DGS1": float(latest_curve["DGS1"]),
                "DGS2": float(latest_curve["DGS2"]),
                "DGS5": float(latest_curve["DGS5"]),
                "DGS10": float(latest_curve["DGS10"]),
                "DGS30": float(latest_curve["DGS30"]),
                "curve_level": curve_level,
                "slope_2s10": slope_2s10,
                "slope_5s30": slope_5s30,
                "curvature_2_5_10": curvature_2_5_10,
                "dgs10_60d_shift": dgs10_60d_shift,
                "breakeven_10y": breakeven_10y,
                "breakeven_60d_shift": breakeven_60d_shift,
                "dgs10_percentile_252d": dgs10_percentile_252d,
                "slope_2s10_percentile_252d": slope_2s10_percentile_252d,
                "breakeven_percentile_252d": breakeven_percentile_252d,
                "validation_pressure_score": validation_pressure_score,
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
    return metrics, recent_curve, recent_inflation, surface


def write_decision_figure(
    metrics: pd.DataFrame,
    recent_curve: pd.DataFrame,
    recent_inflation: pd.DataFrame,
    surface: pd.DataFrame,
) -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)

    row = metrics.iloc[0]
    latest_yields = [float(row[column]) for column in RATE_COLUMNS]

    historical_matrix = recent_curve[RATE_COLUMNS].to_numpy()
    p10 = np.nanpercentile(historical_matrix, 10, axis=0)
    p90 = np.nanpercentile(historical_matrix, 90, axis=0)
    median = np.nanmedian(historical_matrix, axis=0)

    surface_pivot = surface.pivot(
        index="tenor_years",
        columns="parallel_shift_bp",
        values="price_change_percent",
    ).sort_index()

    fig = plt.figure(figsize=(16.2, 10.4))
    gs = GridSpec(2, 2, figure=fig, height_ratios=[1.05, 1.0], width_ratios=[1.12, 1.08])
    fig.patch.set_facecolor("#f7f8fa")

    ax_curve = fig.add_subplot(gs[0, 0])
    ax_surface = fig.add_subplot(gs[0, 1])
    ax_macro = fig.add_subplot(gs[1, 0])
    ax_decision = fig.add_subplot(gs[1, 1])

    ax_curve.fill_between(MATURITIES, p10, p90, alpha=0.18, color="#1f77b4", label="252D 10-90% range")
    ax_curve.plot(MATURITIES, median, linewidth=1.8, linestyle="--", color="#1f77b4", label="252D median")
    ax_curve.plot(MATURITIES, latest_yields, marker="o", linewidth=2.8, color="#ff7f0e", label="Latest curve")
    ax_curve.set_title("Treasury Curve Context", fontweight="bold")
    ax_curve.set_xlabel("Maturity")
    ax_curve.set_ylabel("Yield (%)")
    ax_curve.set_xticks(MATURITIES)
    ax_curve.set_xticklabels(MATURITY_LABELS)
    ax_curve.grid(True, alpha=0.25)
    ax_curve.legend(frameon=False, loc="upper left")

    ax_curve.annotate(
        f"2s10s: {row['slope_2s10']:.2f} pp\n5s30s: {row['slope_5s30']:.2f} pp\n10Y pctile: {row['dgs10_percentile_252d']:.0f}",
        xy=(10, float(row["DGS10"])),
        xytext=(11.5, max(latest_yields) - 0.28),
        arrowprops={"arrowstyle": "->", "lw": 1.2},
        fontsize=9,
        bbox={"boxstyle": "round,pad=0.35", "fc": "white", "ec": "#c9ced6", "alpha": 0.95},
    )

    limit = max(abs(surface_pivot.min().min()), abs(surface_pivot.max().max()))
    heatmap = ax_surface.imshow(
        surface_pivot.values,
        aspect="auto",
        cmap="RdYlGn",
        vmin=-limit,
        vmax=limit,
    )
    ax_surface.set_title("Rate-Shock Loss Surface", fontweight="bold")
    ax_surface.set_xlabel("Parallel curve shock (bp)")
    ax_surface.set_ylabel("Validation tenor")
    ax_surface.set_xticks(range(len(surface_pivot.columns)))
    ax_surface.set_xticklabels([f"{int(x)}" for x in surface_pivot.columns])
    ax_surface.set_yticks(range(len(surface_pivot.index)))
    ax_surface.set_yticklabels([f"{int(x)}Y" for x in surface_pivot.index])

    for i in range(surface_pivot.shape[0]):
        for j in range(surface_pivot.shape[1]):
            value = surface_pivot.values[i, j]
            ax_surface.text(j, i, f"{value:.1f}", ha="center", va="center", fontsize=8.2, color="black")

    try:
        trigger_row = list(surface_pivot.index).index(5.0)
        trigger_col = list(surface_pivot.columns).index(100.0)
        ax_surface.add_patch(
            Rectangle(
                (trigger_col - 0.5, trigger_row - 0.5),
                1,
                1,
                fill=False,
                edgecolor="black",
                linewidth=2.2,
            )
        )
    except ValueError:
        pass

    cbar = fig.colorbar(heatmap, ax=ax_surface, fraction=0.046, pad=0.04)
    cbar.set_label("Price change (%)")

    macro = recent_curve[["date", "DGS2", "DGS10"]].copy()
    macro["slope_2s10"] = macro["DGS10"] - macro["DGS2"]
    macro = macro.merge(recent_inflation[["date", "T10YIE"]], on="date", how="inner")

    line_slope = ax_macro.plot(
        macro["date"],
        macro["slope_2s10"],
        linewidth=2.1,
        color="#1f77b4",
        label="2s10s slope",
    )[0]
    ax_macro.scatter(macro["date"].iloc[-1], macro["slope_2s10"].iloc[-1], color="#1f77b4", s=34)
    ax_macro.axhline(0.0, linewidth=1.0, color="#667085")
    ax_macro.set_title("Curve Slope and Inflation Compensation Monitor", fontweight="bold")
    ax_macro.set_ylabel("2s10s slope (pp)")
    ax_macro.grid(True, alpha=0.25)

    ax_macro_2 = ax_macro.twinx()
    line_bei = ax_macro_2.plot(
        macro["date"],
        macro["T10YIE"],
        linewidth=2.0,
        linestyle="--",
        color="#ff7f0e",
        label="10Y breakeven inflation",
    )[0]
    ax_macro_2.scatter(macro["date"].iloc[-1], macro["T10YIE"].iloc[-1], color="#ff7f0e", s=34)
    ax_macro_2.set_ylabel("10Y breakeven inflation (%)")

    ax_macro.legend([line_slope, line_bei], ["2s10s slope", "10Y breakeven inflation"], frameon=False, loc="lower center", bbox_to_anchor=(0.5, 0.02), ncol=2)

    ax_macro.text(
        0.01,
        0.86,
        f"10Y 60D shift: {row['dgs10_60d_shift']:.2f} pp\nBEI 60D shift: {row['breakeven_60d_shift']:.2f} pp",
        transform=ax_macro.transAxes,
        fontsize=9,
        bbox={"boxstyle": "round,pad=0.35", "fc": "white", "ec": "#c9ced6", "alpha": 0.95},
    )

    ax_decision.axis("off")
    decision_text = (
        "MODEL-RISK STATE\n"
        f"{row['decision_state']} | Pressure {row['validation_pressure_score']:.0f}/100\n\n"
        "Why it matters\n"
        f"+100bp curve shock = {row['loss_100bp_percent']:.2f}% price loss on 5Y validation bond.\n"
        "Active risk channel: duration. Inflation is secondary monitor.\n\n"
        "Read the numbers\n"
        f"DV01 {row['dv01']:.5f}: price change for 1bp rate move.\n"
        f"BEI {row['breakeven_10y']:.2f}%: 10Y breakeven inflation input.\n"
        f"Pctile: 10Y yield {row['dgs10_percentile_252d']:.0f} high | "
        f"2s10s {row['slope_2s10_percentile_252d']:.0f} flat | "
        f"BEI {row['breakeven_percentile_252d']:.0f} subdued.\n\n"
        "Bank decision\n"
        "1. Rebuild the 5Y curve point from source data.\n"
        "2. Reprice +50bp and +100bp shocks independently.\n"
        "3. Confirm DV01 explains the shocked loss.\n"
        "4. Keep inflation-linked review open; BEI is not main trigger.\n"
        "5. Escalate if loss or DV01 mismatch exceeds tolerance.\n\n"
        "Investor decision\n"
        "1. Treat duration as the active risk, not inflation.\n"
        "2. Do not add duration unless the risk budget absorbs ~4.5% shock loss.\n"
        "3. Use BEI as a monitor only; current loss route is rates.\n"
        "4. Watch 10Y percentile, DV01 stability and +100bp loss threshold."
    )

    ax_decision.text(
        0.04,
        0.96,
        decision_text,
        va="top",
        ha="left",
        fontsize=8.45,
        linespacing=1.08,
        bbox={
            "boxstyle": "round,pad=0.55",
            "fc": "white",
            "ec": "#8892a0",
            "lw": 1.1,
            "alpha": 0.98,
        },
    )

    fig.suptitle(
        f"Curve and Inflation Model-Risk Decision Dashboard | State: {row['decision_state']} | Curve: {row['curve_date']}",
        fontsize=15,
        fontweight="bold",
        y=0.982,
    )

    kpi_items = [
        ("STATE", str(row["decision_state"])),
        ("2s10s", f"{row['slope_2s10']:.2f} pp"),
        ("10Y BEI", f"{row['breakeven_10y']:.2f}%"),
        ("+100bp LOSS", f"{row['loss_100bp_percent']:.2f}%"),
        ("PRESSURE", f"{row['validation_pressure_score']:.0f}/100"),
    ]

    for index, (label, value) in enumerate(kpi_items):
        fig.text(
            0.16 + index * 0.17,
            0.925,
            f"{label}\n{value}",
            ha="center",
            va="center",
            fontsize=9.2,
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
        0.012,
        "Source: repository official-data pipeline. This is a model-risk monitoring artifact, not investment advice.",
        fontsize=8.5,
    )

    fig.tight_layout(rect=[0, 0.04, 1, 0.885])
    fig.savefig(FIGURES / "curve_inflation_decision_map.png", dpi=240)
    plt.close(fig)


def write_report(metrics: pd.DataFrame) -> None:
    row = metrics.iloc[0]
    report_path = REPORTS / "one_page_curve_inflation_decision_report.md"

    report = f"""# One-Page Curve and Inflation Decision Report

## Decision state: {row['decision_state']}

**Curve date:** {row['curve_date']}  
**Inflation date:** {row['inflation_date']}  
**Decision flags:** {row['decision_flags']}  
**Validation pressure score:** {row['validation_pressure_score']:.1f} / 100

![Curve and inflation decision map](figures/curve_inflation_decision_map.png)

## Decision metrics

| Metric | Value |
|---|---:|
| 1Y Treasury | {row['DGS1']:.3f}% |
| 2Y Treasury | {row['DGS2']:.3f}% |
| 5Y Treasury | {row['DGS5']:.3f}% |
| 10Y Treasury | {row['DGS10']:.3f}% |
| 30Y Treasury | {row['DGS30']:.3f}% |
| Curve level | {row['curve_level']:.3f}% |
| 2s10s slope | {row['slope_2s10']:.3f} pp |
| 5s30s slope | {row['slope_5s30']:.3f} pp |
| 10Y breakeven inflation | {row['breakeven_10y']:.3f}% |
| 10Y yield 60D shift | {row['dgs10_60d_shift']:.3f} pp |
| Breakeven inflation 60D shift | {row['breakeven_60d_shift']:.3f} pp |
| 10Y yield percentile, 252D | {row['dgs10_percentile_252d']:.1f} |
| 2s10s percentile, 252D | {row['slope_2s10_percentile_252d']:.1f} |
| Breakeven percentile, 252D | {row['breakeven_percentile_252d']:.1f} |
| Validation bond price | {row['bond_price']:.4f} |
| DV01 | {row['dv01']:.6f} |
| +50bp valuation impact | {row['loss_50bp_percent']:.3f}% |
| +100bp valuation impact | {row['loss_100bp_percent']:.3f}% |

## Direct interpretation

- **Primary validation trigger:** {row['decision_flags']}.
- **Curve channel:** valuation loss is driven by duration exposure to parallel curve shocks. The 2s10s and 5s30s slopes define the term-structure context that a validator must challenge.
- **Inflation channel:** 10Y breakeven inflation is the public inflation-compensation input. It anchors the next layer of inflation-linked valuation review.
- **Decision use:** this is not a market call. It is a reproducible evidence object for model validation, revalidation prioritization, sensitivity review and monitoring escalation.

## Bank implication

Treat this as a curve-validation watch item. Rebuild the 5Y curve point from source data, reprice the +50bp and +100bp shocks independently, and verify that DV01 explains the shocked valuation loss. Keep the inflation-linked review open, but current evidence points first to duration sensitivity, not inflation compensation.

## Investor implication

The investor decision is duration-first. A +100bp rate shock creates a material loss on the validation instrument, so adding duration requires enough risk budget to absorb that loss. BEI is subdued versus recent history, so inflation compensation should be monitored, but it is not the active loss driver in the current state. The next watch points are the 10Y yield percentile, DV01 stability and whether the +100bp shock loss remains above the review threshold.

## Validator challenge

Challenge the curve source, missing-data treatment, interpolation method, discounting convention, shock design, inflation proxy, sensitivity stability and whether the current input environment sits outside the model-development distribution.
"""

    report_path.write_text(report, encoding="utf-8")


def main() -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)

    metrics, recent_curve, recent_inflation, surface = build_decision_metrics()
    write_decision_figure(metrics, recent_curve, recent_inflation, surface)
    write_report(metrics)

    print("One-page curve and inflation decision report complete.")
    print("Generated report: reports/one_page_curve_inflation_decision_report.md")
    print("Generated figure: reports/figures/curve_inflation_decision_map.png")
    print("Generated metrics: data/official/processed/one_page_curve_inflation_decision_metrics.csv")
    print("Generated shock surface: data/official/processed/curve_inflation_decision_shock_surface.csv")


if __name__ == "__main__":
    main()

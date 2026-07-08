"""Generate one-page curve and inflation decision report.

This script creates a bank-facing model-risk decision artifact from real public
data already stored in the repository.

The report is not a trading signal. It is a validation and monitoring object:
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


def load_shock_table() -> pd.DataFrame:
    shocks = pd.read_csv(PROCESSED / "curve_pricing_parallel_shocks.csv")
    required = {"parallel_shift_bp", "bond_price", "price_change", "price_change_percent"}
    missing = required.difference(set(shocks.columns))
    if missing:
        raise ValueError(f"Shock table missing columns: {missing}")
    return shocks.sort_values("parallel_shift_bp")


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
    shocks = load_shock_table()

    latest_curve = curve.tail(1).iloc[0]
    latest_inflation = inflation.tail(1).iloc[0]

    recent_curve = curve.tail(252).copy()
    recent_inflation = inflation.tail(252).copy()

    yields = [float(latest_curve[column]) for column in RATE_COLUMNS]

    slope_2s10 = float(latest_curve["DGS10"] - latest_curve["DGS2"])
    slope_5s30 = float(latest_curve["DGS30"] - latest_curve["DGS5"])
    curvature_2_5_10 = float(latest_curve["DGS2"] - 2 * latest_curve["DGS5"] + latest_curve["DGS10"])
    curve_level = float(np.mean(yields))

    breakeven_10y = float(latest_inflation["T10YIE"])
    bond_price = float(pricing["price"])
    dv01 = float(pricing["dv01"])
    loss_50bp = get_shock_metric(shocks, 50.0, "price_change_percent")
    loss_100bp = get_shock_metric(shocks, 100.0, "price_change_percent")

    decision_state, flags = classify_decision_state(
        slope_2s10=slope_2s10,
        breakeven_10y=breakeven_10y,
        loss_100bp=loss_100bp,
    )

    if len(recent_curve) >= 60:
        dgs10_60d_shift = float(latest_curve["DGS10"] - recent_curve.iloc[-60]["DGS10"])
    else:
        dgs10_60d_shift = np.nan

    if len(recent_inflation) >= 60:
        breakeven_60d_shift = float(latest_inflation["T10YIE"] - recent_inflation.iloc[-60]["T10YIE"])
    else:
        breakeven_60d_shift = np.nan

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

    surface = build_validation_shock_surface(yields)
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

    fig = plt.figure(figsize=(16, 9.5))
    gs = GridSpec(2, 2, figure=fig, height_ratios=[1.05, 1.0], width_ratios=[1.18, 1.0])

    ax_curve = fig.add_subplot(gs[0, 0])
    ax_surface = fig.add_subplot(gs[0, 1])
    ax_macro = fig.add_subplot(gs[1, 0])
    ax_decision = fig.add_subplot(gs[1, 1])

    fig.patch.set_facecolor("#f7f8fa")

    ax_curve.fill_between(
        MATURITIES,
        p10,
        p90,
        alpha=0.18,
        label="252D 10-90% range",
    )
    ax_curve.plot(MATURITIES, median, linewidth=1.8, linestyle="--", label="252D median")
    ax_curve.plot(MATURITIES, latest_yields, marker="o", linewidth=2.8, label="Latest curve")
    ax_curve.set_title("Treasury Curve Context", fontweight="bold")
    ax_curve.set_xlabel("Maturity")
    ax_curve.set_ylabel("Yield (%)")
    ax_curve.set_xticks(MATURITIES)
    ax_curve.set_xticklabels(MATURITY_LABELS)
    ax_curve.grid(True, alpha=0.25)
    ax_curve.legend(frameon=False, loc="upper left")

    ax_curve.annotate(
        f"2s10s: {row['slope_2s10']:.2f} pp\n5s30s: {row['slope_5s30']:.2f} pp\nCurve level: {row['curve_level']:.2f}%",
        xy=(10, float(row["DGS10"])),
        xytext=(11.5, max(latest_yields) - 0.25),
        arrowprops={"arrowstyle": "->", "lw": 1.2},
        fontsize=9,
        bbox={"boxstyle": "round,pad=0.35", "fc": "white", "ec": "#c9ced6", "alpha": 0.95},
    )

    heatmap = ax_surface.imshow(
        surface_pivot.values,
        aspect="auto",
        cmap="RdYlGn",
        vmin=-max(abs(surface_pivot.min().min()), abs(surface_pivot.max().max())),
        vmax=max(abs(surface_pivot.min().min()), abs(surface_pivot.max().max())),
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
            ax_surface.text(
                j,
                i,
                f"{value:.1f}",
                ha="center",
                va="center",
                fontsize=8,
                color="black",
            )

    cbar = fig.colorbar(heatmap, ax=ax_surface, fraction=0.046, pad=0.04)
    cbar.set_label("Price change (%)")

    macro = recent_curve[["date", "DGS2", "DGS10"]].copy()
    macro["slope_2s10"] = macro["DGS10"] - macro["DGS2"]
    macro = macro.merge(
        recent_inflation[["date", "T10YIE"]],
        on="date",
        how="inner",
    )

    ax_macro.plot(macro["date"], macro["slope_2s10"], linewidth=2.0, label="2s10s slope")
    ax_macro.axhline(0.0, linewidth=1.0)
    ax_macro.set_title("Curve Slope and Inflation Compensation Monitor", fontweight="bold")
    ax_macro.set_ylabel("2s10s slope (pp)")
    ax_macro.grid(True, alpha=0.25)

    ax_macro_2 = ax_macro.twinx()
    ax_macro_2.plot(macro["date"], macro["T10YIE"], linewidth=2.0, linestyle="--", label="10Y breakeven inflation")
    ax_macro_2.set_ylabel("10Y breakeven inflation (%)")

    ax_macro.text(
        0.01,
        0.92,
        f"10Y 60D shift: {row['dgs10_60d_shift']:.2f} pp\nBEI 60D shift: {row['breakeven_60d_shift']:.2f} pp",
        transform=ax_macro.transAxes,
        fontsize=9,
        bbox={"boxstyle": "round,pad=0.35", "fc": "white", "ec": "#c9ced6", "alpha": 0.95},
    )

    ax_decision.axis("off")
    decision_text = (
        f"Decision state: {row['decision_state']}\n\n"
        f"Primary trigger:\n{row['decision_flags']}\n\n"
        f"Validation bond price: {row['bond_price']:.4f}\n"
        f"DV01: {row['dv01']:.5f}\n"
        f"+50bp impact: {row['loss_50bp_percent']:.2f}%\n"
        f"+100bp impact: {row['loss_100bp_percent']:.2f}%\n\n"
        "Bank action:\n"
        "Review curve lineage, interpolation, discounting convention,\n"
        "DV01 behavior, shock design and inflation-linked inputs.\n\n"
        "Investor read-through:\n"
        "Duration exposure is the dominant loss channel. Inflation\n"
        "compensation defines the second validation route."
    )

    ax_decision.text(
        0.03,
        0.95,
        decision_text,
        va="top",
        ha="left",
        fontsize=10.5,
        linespacing=1.35,
        bbox={
            "boxstyle": "round,pad=0.65",
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
    )

    fig.text(
        0.012,
        0.012,
        "Source: repository official-data pipeline. This is a model-risk monitoring artifact, not investment advice.",
        fontsize=8.5,
    )

    fig.tight_layout(rect=[0, 0.035, 1, 0.94])
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

Prioritize review of curve construction, input lineage, interpolation assumptions, discounting convention, DV01 behavior, shock design and inflation-linked valuation inputs. The validation question is whether pricing outputs remain stable, explainable and reproducible under rate and inflation stress.

## Investor implication

The risk profile is dominated by duration sensitivity and inflation compensation. The relevant question is whether shock losses are consistent with duration, curve shape and inflation-pressure assumptions.

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

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import pandas as pd

from qmrl.fx_derivatives import (
    normalise_rate,
    price_fx_forward,
    spot_shock_table,
)
from qmrl.fx_market_inputs import load_market_input_snapshot


MARKET_INPUT_PATH = (
    ROOT
    / "data"
    / "official"
    / "processed"
    / "usd_brl_market_inputs.csv"
)
PANEL_PATH = ROOT / "data" / "official" / "processed" / "official_rates_fx_inflation_panel.csv"
USD_CURVE_PATH = ROOT / "data" / "official" / "processed" / "usd_treasury_curve_nodes.csv"
USD_FRED_PATH = ROOT / "data" / "official" / "raw" / "fred_us_rates_inflation.csv"

SUMMARY_PATH = ROOT / "data" / "official" / "processed" / "fx_forward_validation_summary.csv"
SHOCK_PATH = ROOT / "data" / "official" / "processed" / "fx_forward_shock_table.csv"
LIFECYCLE_PATH = ROOT / "data" / "official" / "processed" / "fx_model_lifecycle_register.csv"
REPORT_PATH = ROOT / "reports" / "fx_forward_validation_report.md"
FIGURE_PATH = ROOT / "reports" / "figures" / "fx_forward_validation_map.png"


def money(value: float) -> str:
    return f"{float(value):,.0f}"


def pct(value: float) -> str:
    return f"{100.0 * float(value):.4f}%"


def number(value: float) -> str:
    return f"{float(value):,.6f}"


def to_numeric_series(frame: pd.DataFrame, column: str) -> pd.Series:
    return pd.to_numeric(frame[column], errors="coerce")


def latest_numeric_value(frame: pd.DataFrame, column: str) -> float:
    work = frame.copy()
    date_columns = [col for col in work.columns if "date" in col.lower()]
    if date_columns:
        work[date_columns[0]] = pd.to_datetime(work[date_columns[0]], errors="coerce")
        work = work.sort_values(date_columns[0])

    values = pd.to_numeric(work[column], errors="coerce").dropna()
    if values.empty:
        raise ValueError(f"No numeric values found in column {column}.")
    return float(values.iloc[-1])


def find_fx_spot_column(frame: pd.DataFrame) -> str:
    """Locate the USD/BRL spot column without assuming one exact name.

    The official panel has changed names across pipeline versions. This detector
    first uses semantic column names, then falls back to a numerical profile:
    USD/BRL spot is usually a positive series around 3 to 8 in the Brazil sample,
    while SELIC/IPCA/rates are excluded by name.
    """

    columns = list(frame.columns)
    lower = {col: col.lower().replace(" ", "_").replace("-", "_").replace("/", "_") for col in columns}

    strong_terms = [
        "usd_brl",
        "usdbrl",
        "brl_usd",
        "usdb_rl",
        "dollar_brl",
        "dolar_brl",
        "dolar",
        "dollar",
        "cambio",
        "exchange",
        "fx",
        "ptax",
        "venda",
        "sell",
    ]

    exclusions = [
        "selic",
        "ipca",
        "inflation",
        "cpi",
        "rate",
        "interest",
        "yield",
        "treasury",
        "real_rate",
    ]

    semantic_candidates = []
    for col in columns:
        name = lower[col]
        if any(term in name for term in strong_terms) and not any(term in name for term in exclusions):
            values = pd.to_numeric(frame[col], errors="coerce").dropna()
            if not values.empty and values.median() > 1.0:
                semantic_candidates.append(col)

    if semantic_candidates:
        return semantic_candidates[0]

    numeric_candidates = []
    for col in columns:
        name = lower[col]
        if "date" in name or any(term in name for term in exclusions):
            continue

        values = pd.to_numeric(frame[col], errors="coerce").dropna()
        if values.empty:
            continue

        median = float(values.median())
        min_value = float(values.min())
        max_value = float(values.max())

        if min_value > 0.0 and 2.0 <= median <= 10.0 and max_value <= 20.0:
            numeric_candidates.append((col, median, values.notna().sum()))

    if numeric_candidates:
        numeric_candidates.sort(key=lambda item: (-item[2], abs(item[1] - 5.0)))
        return numeric_candidates[0][0]

    diagnostic = ", ".join(columns)
    raise KeyError(f"Could not locate USD/BRL or FX spot column in official panel. Available columns: {diagnostic}")


def find_brl_rate_column(frame: pd.DataFrame) -> str:
    """Locate the BRL domestic rate column.

    Prefer SELIC or policy-rate naming. If names are not explicit, use the
    highest plausible positive rate-like numerical column after excluding FX,
    inflation and date fields.
    """

    columns = list(frame.columns)
    lower = {col: col.lower().replace(" ", "_").replace("-", "_").replace("/", "_") for col in columns}

    preferred_terms = ["selic", "policy", "brl_rate", "domestic_rate", "interest_rate"]
    for col in columns:
        name = lower[col]
        if any(term in name for term in preferred_terms):
            values = pd.to_numeric(frame[col], errors="coerce").dropna()
            if not values.empty:
                return col

    exclusions = [
        "date",
        "usd",
        "brl_usd",
        "usd_brl",
        "usdbrl",
        "dolar",
        "dollar",
        "cambio",
        "exchange",
        "fx",
        "ipca",
        "inflation",
        "cpi",
        "treasury",
    ]

    numeric_candidates = []
    for col in columns:
        name = lower[col]
        if any(term in name for term in exclusions):
            continue

        values = pd.to_numeric(frame[col], errors="coerce").dropna()
        if values.empty:
            continue

        median = float(values.median())
        if median > 0.0:
            numeric_candidates.append((col, median, values.notna().sum()))

    if numeric_candidates:
        numeric_candidates.sort(key=lambda item: (-item[1], -item[2]))
        return numeric_candidates[0][0]

    diagnostic = ", ".join(columns)
    raise KeyError(f"Could not locate BRL domestic interest-rate column in official panel. Available columns: {diagnostic}")


def read_usd_rate() -> float:
    if USD_CURVE_PATH.exists():
        curve = pd.read_csv(USD_CURVE_PATH)

        lower = {col: col.lower() for col in curve.columns}

        tenor_cols = [col for col in curve.columns if "tenor" in lower[col]]
        rate_cols = [col for col in curve.columns if "rate" in lower[col] or "yield" in lower[col] or "zero" in lower[col]]

        if tenor_cols and rate_cols:
            tenor_col = tenor_cols[0]
            rate_col = rate_cols[0]
            curve[tenor_col] = pd.to_numeric(curve[tenor_col], errors="coerce")
            curve[rate_col] = pd.to_numeric(curve[rate_col], errors="coerce")
            curve = curve.dropna(subset=[tenor_col, rate_col])
            if not curve.empty:
                idx = (curve[tenor_col] - 1.0).abs().idxmin()
                return normalise_rate(float(curve.loc[idx, rate_col]))

        preferred = [
            col for col in curve.columns
            if any(token in lower[col] for token in ["1y", "1_yr", "one_year", "dgs1"])
        ]
        if preferred:
            return normalise_rate(latest_numeric_value(curve, preferred[0]))

        numeric_cols = [
            col for col in curve.columns
            if pd.to_numeric(curve[col], errors="coerce").notna().sum() > 0 and "date" not in lower[col]
        ]
        if numeric_cols:
            return normalise_rate(latest_numeric_value(curve, numeric_cols[0]))

    if USD_FRED_PATH.exists():
        fred = pd.read_csv(USD_FRED_PATH)
        lower = {col: col.lower() for col in fred.columns}

        preferred = [
            col for col in fred.columns
            if any(token in lower[col] for token in ["dgs1", "1y", "1_yr", "one_year"])
        ]
        if preferred:
            return normalise_rate(latest_numeric_value(fred, preferred[0]))

        numeric_cols = [
            col for col in fred.columns
            if pd.to_numeric(fred[col], errors="coerce").notna().sum() > 0 and "date" not in lower[col]
        ]
        if numeric_cols:
            return normalise_rate(latest_numeric_value(fred, numeric_cols[0]))

    raise FileNotFoundError("Could not locate USD foreign rate input from USD curve or FRED files.")


def run_fx_validation() -> None:
    if not MARKET_INPUT_PATH.exists():
        raise FileNotFoundError(
            "Governed USD/BRL market inputs are missing. "
            "Run scripts/build_usd_brl_market_inputs.py first."
        )

    market = load_market_input_snapshot(
        MARKET_INPUT_PATH
    )

    spot_rate = market.spot_rate_brl_per_usd
    domestic_rate = market.domestic_rate_brl
    foreign_rate = market.foreign_rate_usd

    fx_col = market.spot_source_id
    brl_rate_col = market.domestic_rate_source_id

    maturity_years = 1.0
    notional_usd = 1_000_000.0

    model_at_par = price_fx_forward(
        spot_rate=spot_rate,
        domestic_rate=domestic_rate,
        foreign_rate=foreign_rate,
        maturity_years=maturity_years,
        contract_forward_rate=spot_rate,
        notional_foreign=notional_usd,
    )

    contract_forward_rate = model_at_par.model_forward_rate * 1.005

    valuation = price_fx_forward(
        spot_rate=spot_rate,
        domestic_rate=domestic_rate,
        foreign_rate=foreign_rate,
        maturity_years=maturity_years,
        contract_forward_rate=contract_forward_rate,
        notional_foreign=notional_usd,
    )

    shocks = spot_shock_table(
        spot_rate=spot_rate,
        domestic_rate=domestic_rate,
        foreign_rate=foreign_rate,
        maturity_years=maturity_years,
        contract_forward_rate=contract_forward_rate,
        notional_foreign=notional_usd,
    )

    summary = pd.DataFrame(
        [
            {
                "model_id": "QMRL-FX-FWD-001",
            "currency_pair": market.currency_pair,
            "quote_convention": market.quote_convention,
            "as_of_date": market.as_of_date.isoformat(),
            "spot_source_id": market.spot_source_id,
            "domestic_rate_source_id": market.domestic_rate_source_id,
            "foreign_rate_source_id": market.foreign_rate_source_id,
            "spot_observation_date": market.spot_observation_date.isoformat(),
            "domestic_rate_observation_date": market.domestic_rate_observation_date.isoformat(),
            "foreign_rate_observation_date": market.foreign_rate_observation_date.isoformat(),
            "input_contract_status": market.input_contract_status,
                "product": "USD/BRL FX forward",
                "spot_input_column": fx_col,
                "domestic_rate_column": brl_rate_col,
                "spot_rate_brl_per_usd": spot_rate,
                "domestic_rate_brl": domestic_rate,
                "foreign_rate_usd": foreign_rate,
                "maturity_years": maturity_years,
                "notional_usd": notional_usd,
                "model_forward_rate": valuation.model_forward_rate,
                "contract_forward_rate": valuation.contract_forward_rate,
                "long_usd_forward_value_brl": valuation.long_foreign_forward_value,
                "short_usd_forward_value_brl": valuation.short_foreign_forward_value,
                "fx_delta": valuation.fx_delta,
                "carry_basis": valuation.carry_basis,
                "model_use_decision": "Base FX forward pricing and first-order spot-shock validation available for review.",
                "next_validation_gate": "FX option valuation, volatility surface and cross-currency basis extension",
            }
        ]
    )

    lifecycle = pd.DataFrame(
        [
            {
                "model_id": "QMRL-FX-FWD-001",
                "product": "USD/BRL FX forward",
                "stage": "Base FX forward pricing and spot-risk validation",
                "validation_status": "Forward parity, PV sign, FX delta and shock direction available",
                "monitoring_trigger": "USD/BRL spot change, BRL rate change, USD rate change, contract forward change",
                "archer_mrm_action": "Create or update FX derivatives model record and attach validation outputs",
                "next_gate": "FX options and cross-currency basis validation",
            }
        ]
    )

    write_report(summary.iloc[0], shocks, lifecycle.iloc[0])
    write_figure(shocks, summary.iloc[0])

    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    FIGURE_PATH.parent.mkdir(parents=True, exist_ok=True)

    summary.to_csv(SUMMARY_PATH, index=False)
    shocks.to_csv(SHOCK_PATH, index=False)
    lifecycle.to_csv(LIFECYCLE_PATH, index=False)

    print("FX derivatives validation complete.")
    print(f"Generated summary: {SUMMARY_PATH.relative_to(ROOT)}")
    print(f"Generated shock table: {SHOCK_PATH.relative_to(ROOT)}")
    print(f"Generated lifecycle register: {LIFECYCLE_PATH.relative_to(ROOT)}")
    print(f"Generated report: {REPORT_PATH.relative_to(ROOT)}")
    print(f"Generated figure: {FIGURE_PATH.relative_to(ROOT)}")


def write_report(summary: pd.Series, shocks: pd.DataFrame, lifecycle: pd.Series) -> None:
    report = f"""# FX Forward Validation Report

## Purpose

This layer adds a base Foreign Exchange (FX) derivatives validation layer.

The model prices a USD/BRL FX forward using spot FX, a BRL domestic rate, a USD foreign rate and covered-interest-parity logic. It then produces a spot-shock table, FX delta and lifecycle record.

## Acronyms

| Acronym | Meaning | Use in this layer |
|---|---|---|
| FX | Foreign Exchange | USD/BRL exchange-rate derivative |
| PV | Present Value | Discounted value of the forward payoff |
| NPV | Net Present Value | Forward value after discounting |
| BRL | Brazilian Real | Domestic currency |
| USD | United States Dollar | Foreign currency |
| MRM | Model Risk Management | Lifecycle governance and validation record |

## Base valuation

| Metric | Value |
|---|---:|
| Spot USD/BRL, BRL per USD | {number(summary["spot_rate_brl_per_usd"])} |
| BRL domestic rate | {pct(summary["domestic_rate_brl"])} |
| USD foreign rate | {pct(summary["foreign_rate_usd"])} |
| Model forward rate, BRL per USD | {number(summary["model_forward_rate"])} |
| Contract forward rate | {number(summary["contract_forward_rate"])} |
| Long USD forward value, BRL | {money(summary["long_usd_forward_value_brl"])} |
| FX delta | {money(summary["fx_delta"])} |
| Carry basis | {number(summary["carry_basis"])} |

## Model-use decision

The FX forward layer is available for governed base forward-pricing validation, first-order spot-risk review and lifecycle evidence.

It is not an FX options model, volatility-surface model or cross-currency-basis model. Those remain the next validation gates.

## Archer / MRM action

| Field | Record |
|---|---|
| Model ID | {lifecycle["model_id"]} |
| Product | {lifecycle["product"]} |
| Stage | {lifecycle["stage"]} |
| Validation status | {lifecycle["validation_status"]} |
| Monitoring trigger | {lifecycle["monitoring_trigger"]} |
| Next gate | {lifecycle["next_gate"]} |

## Spot-shock table

{shocks.to_markdown(index=False)}
"""
    REPORT_PATH.write_text(report, encoding="utf-8")


def write_figure(shocks: pd.DataFrame, summary: pd.Series) -> None:
    plt.close("all")
    fig, axes = plt.subplots(1, 2, figsize=(14.5, 5.6))
    fig.patch.set_facecolor("#f6f8fb")

    for ax in axes:
        ax.set_facecolor("white")
        ax.grid(True, color="#d7dde7", linewidth=0.8, alpha=0.75)
        for spine in ax.spines.values():
            spine.set_color("#9ca3af")

    x = shocks["spot_shock_pct"].astype(float)
    pnl = shocks["long_foreign_forward_pnl"].astype(float)
    value = shocks["long_foreign_forward_value"].astype(float)

    colors = ["#b42318" if val < 0 else "#15803d" if val > 0 else "#9ca3af" for val in pnl]

    axes[0].bar(x, pnl, width=3.8, color=colors, alpha=0.90, edgecolor="white")
    axes[0].axhline(0, color="#374151", linewidth=1.0)
    axes[0].set_title("USD/BRL Forward Spot-Shock P&L", loc="left", fontweight="bold")
    axes[0].set_xlabel("Spot shock, %")
    axes[0].set_ylabel("Long USD forward P&L, BRL")
    axes[0].yaxis.set_major_formatter(FuncFormatter(lambda value, _pos: f"{int(value):,}"))

    axes[1].plot(x, value, marker="o", linewidth=2.4, color="#374151")
    axes[1].axhline(0, color="#374151", linewidth=1.0)
    axes[1].set_title("Forward Value Across Spot Shocks", loc="left", fontweight="bold")
    axes[1].set_xlabel("Spot shock, %")
    axes[1].set_ylabel("Long USD forward value, BRL")
    axes[1].yaxis.set_major_formatter(FuncFormatter(lambda value, _pos: f"{int(value):,}"))

    fig.suptitle("FX Forward Validation Layer: Pricing, Delta and Spot-Shock Behaviour", fontsize=15.5, fontweight="bold", x=0.03, ha="left")
    fig.text(
        0.03,
        0.02,
        "Model-use decision: base USD/BRL forward pricing and first-order FX spot-risk validation. Next gate: FX options, volatility surface and cross-currency basis.",
        fontsize=9.3,
        color="#111827",
    )

    fig.tight_layout(rect=[0.02, 0.06, 0.98, 0.88])
    FIGURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURE_PATH, dpi=110, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


if __name__ == "__main__":
    run_fx_validation()

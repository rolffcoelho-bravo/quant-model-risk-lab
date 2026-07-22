from __future__ import annotations

from pathlib import Path
import sys
import subprocess
import math

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import pandas as pd

from qmrl.fx_options import (
    forward_rate,
    garman_kohlhagen_price,
    put_call_parity_gap,
    spot_vol_surface,
)


FX_FORWARD_SUMMARY_PATH = ROOT / "data" / "official" / "processed" / "fx_forward_validation_summary.csv"
OFFICIAL_PANEL_PATH = ROOT / "data" / "official" / "processed" / "official_rates_fx_inflation_panel.csv"

SUMMARY_PATH = ROOT / "data" / "official" / "processed" / "fx_option_validation_summary.csv"
SURFACE_PATH = ROOT / "data" / "official" / "processed" / "fx_option_spot_vol_surface.csv"
PARITY_PATH = ROOT / "data" / "official" / "processed" / "fx_option_put_call_parity_table.csv"
LIFECYCLE_PATH = ROOT / "data" / "official" / "processed" / "fx_option_lifecycle_register.csv"
REPORT_PATH = ROOT / "reports" / "fx_option_validation_report.md"
FIGURE_PATH = ROOT / "reports" / "figures" / "fx_option_validation_map.png"


def money(value: float) -> str:
    return f"{float(value):,.0f}"


def pct(value: float) -> str:
    return f"{100.0 * float(value):.4f}%"


def number(value: float) -> str:
    return f"{float(value):,.6f}"


def realised_fx_volatility(panel: pd.DataFrame, spot_column: str) -> float:
    if spot_column not in panel.columns:
        numeric_candidates = []
        for col in panel.columns:
            name = col.lower()
            if "date" in name or "selic" in name or "ipca" in name or "rate" in name:
                continue
            values = pd.to_numeric(panel[col], errors="coerce").dropna()
            if values.empty:
                continue
            median = float(values.median())
            if 2.0 <= median <= 10.0:
                numeric_candidates.append(col)
        if not numeric_candidates:
            return 0.15
        spot_column = numeric_candidates[0]

    work = panel.copy()
    date_cols = [col for col in work.columns if "date" in col.lower()]
    if date_cols:
        work[date_cols[0]] = pd.to_datetime(work[date_cols[0]], errors="coerce")
        work = work.sort_values(date_cols[0])

    spot = pd.to_numeric(work[spot_column], errors="coerce").dropna()
    returns = (spot / spot.shift(1)).apply(lambda value: math.log(value) if value and value > 0 else None).dropna()

    if len(returns) < 20:
        return 0.15

    sample = returns.tail(min(len(returns), 252))
    vol = float(sample.std(ddof=1)) * math.sqrt(252.0)

    if not math.isfinite(vol) or vol <= 0:
        return 0.15

    return max(min(vol, 0.60), 0.05)


def ensure_fx_forward_outputs() -> None:
    subprocess.run(
        [
            sys.executable,
            "scripts/run_fx_derivatives_validation.py",
        ],
        check=True,
    )



def run_fx_option_validation() -> None:
    ensure_fx_forward_outputs()

    fx_forward = pd.read_csv(FX_FORWARD_SUMMARY_PATH).iloc[0]
    panel = pd.read_csv(OFFICIAL_PANEL_PATH)

    spot = float(fx_forward["spot_rate_brl_per_usd"])
    domestic_rate = float(fx_forward["domestic_rate_brl"])
    foreign_rate = float(fx_forward["foreign_rate_usd"])
    maturity = float(fx_forward["maturity_years"])
    notional = float(fx_forward["notional_usd"])
    strike = float(fx_forward["model_forward_rate"])

    spot_column = str(fx_forward["spot_input_column"])
    volatility = realised_fx_volatility(panel, spot_column)

    call = garman_kohlhagen_price(
        "call",
        spot_rate=spot,
        strike_rate=strike,
        domestic_rate=domestic_rate,
        foreign_rate=foreign_rate,
        volatility=volatility,
        maturity_years=maturity,
        notional_foreign=notional,
    )
    put = garman_kohlhagen_price(
        "put",
        spot_rate=spot,
        strike_rate=strike,
        domestic_rate=domestic_rate,
        foreign_rate=foreign_rate,
        volatility=volatility,
        maturity_years=maturity,
        notional_foreign=notional,
    )

    parity_gap = put_call_parity_gap(
        call.premium_domestic,
        put.premium_domestic,
        spot,
        strike,
        domestic_rate,
        foreign_rate,
        maturity,
        notional,
    )

    forward = forward_rate(spot, domestic_rate, foreign_rate, maturity)
    surface = spot_vol_surface(
        spot_rate=spot,
        strike_rate=strike,
        domestic_rate=domestic_rate,
        foreign_rate=foreign_rate,
        base_volatility=volatility,
        maturity_years=maturity,
        notional_foreign=notional,
    )

    parity_table = pd.DataFrame(
        [
            {
                "check": "put_call_parity",
                "call_value_domestic": call.premium_domestic,
                "put_value_domestic": put.premium_domestic,
                "discounted_spot_leg": notional * spot * math.exp(-foreign_rate * maturity),
                "discounted_strike_leg": notional * strike * math.exp(-domestic_rate * maturity),
                "parity_gap": parity_gap,
                "status": "PASS" if abs(parity_gap) <= 1e-6 * max(abs(call.premium_domestic), 1.0) else "REVIEW",
            }
        ]
    )

    summary = pd.DataFrame(
        [
            {
                "model_id": "QMRL-FX-OPT-001",
            "currency_pair": str(fx_forward["currency_pair"]),
            "quote_convention": str(fx_forward["quote_convention"]),
            "as_of_date": str(fx_forward["as_of_date"]),
            "spot_source_id": str(fx_forward["spot_source_id"]),
            "domestic_rate_source_id": str(fx_forward["domestic_rate_source_id"]),
            "foreign_rate_source_id": str(fx_forward["foreign_rate_source_id"]),
            "spot_observation_date": str(fx_forward["spot_observation_date"]),
            "domestic_rate_observation_date": str(fx_forward["domestic_rate_observation_date"]),
            "foreign_rate_observation_date": str(fx_forward["foreign_rate_observation_date"]),
            "input_contract_status": str(fx_forward["input_contract_status"]),
                "source_model": "QMRL-FX-FWD-001",
                "product": "USD/BRL European FX option",
                "pricing_model": "Garman-Kohlhagen lognormal FX option model",
                "spot_rate_brl_per_usd": spot,
                "strike_rate": strike,
                "model_forward_rate": forward,
                "domestic_rate_brl": domestic_rate,
                "foreign_rate_usd": foreign_rate,
                "realised_volatility_input": volatility,
                "maturity_years": maturity,
                "notional_usd": notional,
                "call_value_brl": call.premium_domestic,
                "put_value_brl": put.premium_domestic,
                "call_delta": call.delta,
                "put_delta": put.delta,
                "call_gamma": call.gamma,
                "put_gamma": put.gamma,
                "call_vega": call.vega,
                "put_vega": put.vega,
                "put_call_parity_gap": parity_gap,
                "model_use_decision": "Vanilla European FX option pricing, Greeks and parity checks available for model validation review.",
                "next_validation_gate": "volatility smile, SABR calibration, barrier/path-dependent options and cross-currency basis",
            }
        ]
    )

    lifecycle = pd.DataFrame(
        [
            {
                "model_id": "QMRL-FX-OPT-001",
                "product": "USD/BRL European FX option",
                "stage": "Vanilla FX option validation",
                "validation_status": "Garman-Kohlhagen price, Greeks, put-call parity, spot and volatility shocks available",
                "monitoring_trigger": "spot move, realised volatility change, rate change, parity gap, delta/vega sign change",
                "archer_mrm_action": "Create FX option model record linked to FX forward model and attach validation outputs",
                "next_gate": "SABR smile and path-dependent FX option validation",
            }
        ]
    )

    write_report(summary.iloc[0], parity_table.iloc[0], surface, lifecycle.iloc[0])
    write_figure(surface, summary.iloc[0])

    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    FIGURE_PATH.parent.mkdir(parents=True, exist_ok=True)

    summary.to_csv(SUMMARY_PATH, index=False)
    surface.to_csv(SURFACE_PATH, index=False)
    parity_table.to_csv(PARITY_PATH, index=False)
    lifecycle.to_csv(LIFECYCLE_PATH, index=False)

    print("FX options validation complete.")
    print(f"Generated summary: {SUMMARY_PATH.relative_to(ROOT)}")
    print(f"Generated spot-vol surface: {SURFACE_PATH.relative_to(ROOT)}")
    print(f"Generated put-call parity table: {PARITY_PATH.relative_to(ROOT)}")
    print(f"Generated lifecycle register: {LIFECYCLE_PATH.relative_to(ROOT)}")
    print(f"Generated report: {REPORT_PATH.relative_to(ROOT)}")
    print(f"Generated figure: {FIGURE_PATH.relative_to(ROOT)}")


def write_report(summary: pd.Series, parity: pd.Series, surface: pd.DataFrame, lifecycle: pd.Series) -> None:
    report = f"""# FX Options Validation Report

## Purpose

This layer adds vanilla FX option validation on top of the USD/BRL FX forward layer.

The pricing engine uses the Garman-Kohlhagen lognormal FX option model. The validation evidence covers call and put values, Greeks, put-call parity, spot shocks, volatility shocks and model lifecycle controls.

## Acronyms

| Acronym | Meaning | Use in this layer |
|---|---|---|
| FX | Foreign Exchange | USD/BRL option exposure |
| GK | Garman-Kohlhagen | Lognormal FX option pricing model |
| PV | Present Value | Discounted option premium |
| Delta | Spot sensitivity | First-order FX risk |
| Gamma | Delta convexity | Second-order spot risk |
| Vega | Volatility sensitivity | Volatility-risk control |
| SABR | Stochastic Alpha Beta Rho | Next smile-calibration gate |
| MRM | Model Risk Management | Lifecycle governance record |

## Base valuation

| Metric | Value |
|---|---:|
| Spot USD/BRL, BRL per USD | {number(summary["spot_rate_brl_per_usd"])} |
| Strike, BRL per USD | {number(summary["strike_rate"])} |
| Model forward, BRL per USD | {number(summary["model_forward_rate"])} |
| BRL domestic rate | {pct(summary["domestic_rate_brl"])} |
| USD foreign rate | {pct(summary["foreign_rate_usd"])} |
| Realised volatility input | {pct(summary["realised_volatility_input"])} |
| Call value, BRL | {money(summary["call_value_brl"])} |
| Put value, BRL | {money(summary["put_value_brl"])} |
| Call delta | {money(summary["call_delta"])} |
| Put delta | {money(summary["put_delta"])} |
| Call gamma | {money(summary["call_gamma"])} |
| Call vega | {money(summary["call_vega"])} |
| Put-call parity gap | {number(summary["put_call_parity_gap"])} |

## Put-call parity control

| Check | Status | Gap |
|---|---|---:|
| Put-call parity | {parity["status"]} | {number(parity["parity_gap"])} |

## Model-use decision

The layer is available for governed validation review of vanilla European USD/BRL FX option pricing, Greeks, put-call parity and first-order scenario review.

It is not a smile-calibrated volatility-surface model, SABR model, barrier-option model or path-dependent option engine. Those remain the next validation gates.

## Archer / MRM action

| Field | Record |
|---|---|
| Model ID | {lifecycle["model_id"]} |
| Product | {lifecycle["product"]} |
| Stage | {lifecycle["stage"]} |
| Validation status | {lifecycle["validation_status"]} |
| Monitoring trigger | {lifecycle["monitoring_trigger"]} |
| Next gate | {lifecycle["next_gate"]} |

## Spot and volatility shock surface

{surface.to_markdown(index=False)}
"""
    REPORT_PATH.write_text(report, encoding="utf-8")


def write_figure(surface: pd.DataFrame, summary: pd.Series) -> None:
    plt.close("all")
    fig, axes = plt.subplots(1, 3, figsize=(17.0, 5.8))
    fig.patch.set_facecolor("#f6f8fb")

    for ax in axes:
        ax.set_facecolor("white")
        ax.grid(True, color="#d7dde7", linewidth=0.8, alpha=0.75)
        for spine in ax.spines.values():
            spine.set_color("#9ca3af")

    base = surface[surface["vol_shock_abs"].abs() < 1e-12].copy()
    base = base.sort_values("spot_shock_pct")

    axes[0].plot(base["spot_shock_pct"], base["call_value_domestic"], marker="o", linewidth=2.2, label="Call")
    axes[0].plot(base["spot_shock_pct"], base["put_value_domestic"], marker="o", linewidth=2.2, label="Put")
    axes[0].set_title("Option Value Across Spot Shocks", loc="left", fontweight="bold")
    axes[0].set_xlabel("Spot shock, %")
    axes[0].set_ylabel("Option value, BRL")
    axes[0].yaxis.set_major_formatter(FuncFormatter(lambda value, _pos: f"{int(value):,}"))
    axes[0].legend(frameon=True, fontsize=8)

    vol_surface = surface[surface["spot_shock_pct"].abs() < 1e-12].copy()
    vol_surface = vol_surface.sort_values("vol_shock_abs")
    axes[1].bar(vol_surface["vol_shock_abs"] * 100.0, vol_surface["call_value_domestic"], width=3.2, alpha=0.88)
    axes[1].set_title("Call Value Across Volatility Shocks", loc="left", fontweight="bold")
    axes[1].set_xlabel("Volatility shock, percentage points")
    axes[1].set_ylabel("Call value, BRL")
    axes[1].yaxis.set_major_formatter(FuncFormatter(lambda value, _pos: f"{int(value):,}"))

    axes[2].plot(base["spot_shock_pct"], base["call_delta"], marker="o", linewidth=2.2, label="Call delta")
    axes[2].plot(base["spot_shock_pct"], base["put_delta"], marker="o", linewidth=2.2, label="Put delta")
    axes[2].axhline(0, linewidth=1.0)
    axes[2].set_title("Delta Across Spot Shocks", loc="left", fontweight="bold")
    axes[2].set_xlabel("Spot shock, %")
    axes[2].set_ylabel("Delta")
    axes[2].yaxis.set_major_formatter(FuncFormatter(lambda value, _pos: f"{int(value):,}"))
    axes[2].legend(frameon=True, fontsize=8)

    fig.suptitle("FX Options Validation Layer: Garman-Kohlhagen, Greeks, Parity and Shock Controls", fontsize=15.5, fontweight="bold", x=0.03, ha="left")
    fig.text(
        0.03,
        0.02,
        "Model-use decision: vanilla European FX option validation. Next gate: SABR smile, barrier options and path-dependent FX options.",
        fontsize=9.3,
        color="#111827",
    )

    fig.tight_layout(rect=[0.02, 0.06, 0.98, 0.88])
    FIGURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURE_PATH, dpi=110, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


if __name__ == "__main__":
    run_fx_option_validation()

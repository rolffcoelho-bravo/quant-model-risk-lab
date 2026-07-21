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
import pandas as pd

from qmrl.xva import XVAAssumptions, compute_xva_from_clean_values, scenario_exposures


SUMMARY_PATH = ROOT / "data" / "official" / "processed" / "ir_derivatives_pricing_summary.csv"
SHOCK_PATH = ROOT / "data" / "official" / "processed" / "ir_swap_shock_table.csv"

EXPOSURE_PATH = ROOT / "data" / "official" / "processed" / "xva_exposure_profile.csv"
SUMMARY_OUT_PATH = ROOT / "data" / "official" / "processed" / "xva_summary.csv"
SENSITIVITY_PATH = ROOT / "data" / "official" / "processed" / "xva_sensitivity_table.csv"
REPORT_PATH = ROOT / "reports" / "xva_validation_report.md"
FIGURE_PATH = ROOT / "reports" / "figures" / "xva_validation_map.png"


def pick(row: pd.Series, *names: str, default=None):
    for name in names:
        if name in row.index and pd.notna(row[name]):
            return row[name]
    return default


def pick_col(df: pd.DataFrame, *names: str) -> str:
    for name in names:
        if name in df.columns:
            return name
    raise KeyError(f"None of these columns exist: {names}")


def money(value: float) -> str:
    return f"{float(value):,.0f}"


def pct(value: float) -> str:
    return f"{100.0 * float(value):.4f}%"


def run_xva_validation() -> None:
    if not SUMMARY_PATH.exists() or not SHOCK_PATH.exists():
        raise FileNotFoundError("Run scripts/run_ir_derivatives_pricing_validation.py before XVA validation.")

    summary = pd.read_csv(SUMMARY_PATH).iloc[0]
    shock = pd.read_csv(SHOCK_PATH).copy()

    shock_col = pick_col(shock, "curve_shift_bp", "shock_bp", "parallel_curve_shock_bp", "curve_shock_bp")
    payer_col = pick_col(shock, "payer_swap_npv", "payer_npv", "payer_swap_value")

    shock = shock.sort_values(shock_col).reset_index(drop=True)
    clean_values = shock[payer_col].astype(float).to_numpy()

    curve_shifts = shock[shock_col].astype(float)
    positive_exposure, negative_exposure = scenario_exposures(clean_values)

    clean_value_at_base = float(pick(summary, "payer_swap_npv", "payer_npv", default=0.0))
    discount_rate = float(pick(summary, "par_swap_rate", default=0.0))

    assumptions = XVAAssumptions()
    xva = compute_xva_from_clean_values(
        clean_values=clean_values,
        clean_value_at_base=clean_value_at_base,
        discount_rate=discount_rate,
        assumptions=assumptions,
    )

    exposure = pd.DataFrame(
        {
            "curve_shift_bp": curve_shifts,
            "payer_clean_npv": clean_values,
            "positive_exposure": positive_exposure,
            "negative_exposure": negative_exposure,
            "exposure_state": [
                "asset_exposure" if value > 0 else "liability_exposure" if value < 0 else "flat"
                for value in clean_values
            ],
        }
    )

    summary_out = pd.DataFrame(
        [
            {
                "model_id": "QMRL-XVA-IR-SWAP-001",
                "source_clean_model": "QMRL-IR-SWAP-001",
                "product": "fixed-for-floating interest-rate swap",
                "valuation_date": pick(summary, "valuation_date", default=""),
                "clean_payer_npv": clean_value_at_base,
                "expected_exposure": xva["expected_exposure"],
                "expected_negative_exposure": xva["expected_negative_exposure"],
                "pfe_95": xva["pfe_95"],
                "counterparty_spread_bps": assumptions.counterparty_spread_bps,
                "own_spread_bps": assumptions.own_spread_bps,
                "funding_spread_bps": assumptions.funding_spread_bps,
                "recovery_rate": assumptions.recovery_rate,
                "horizon_years": assumptions.horizon_years,
                "counterparty_pd": xva["counterparty_pd"],
                "own_pd": xva["own_pd"],
                "discount_factor": xva["discount_factor"],
                "cva": xva["cva"],
                "dva": xva["dva"],
                "fva": xva["fva"],
                "xva_reserve": xva["xva_reserve"],
                "xva_adjusted_payer_value": xva["xva_adjusted_value"],
                "model_use_decision": "XVA layer available for transparent scenario-based CVA/DVA/FVA review; not a production exposure engine.",
                "next_validation_gate": "time-grid exposure simulation and counterparty-specific calibration",
            }
        ]
    )

    sensitivity = build_sensitivity_table(clean_values, clean_value_at_base, discount_rate)
    write_report(summary_out.iloc[0], exposure, sensitivity)
    write_figure(exposure, summary_out.iloc[0], sensitivity)

    EXPOSURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    FIGURE_PATH.parent.mkdir(parents=True, exist_ok=True)

    exposure.to_csv(EXPOSURE_PATH, index=False)
    summary_out.to_csv(SUMMARY_OUT_PATH, index=False)
    sensitivity.to_csv(SENSITIVITY_PATH, index=False)

    print("XVA validation complete.")
    print(f"Generated exposure profile: {EXPOSURE_PATH.relative_to(ROOT)}")
    print(f"Generated XVA summary: {SUMMARY_OUT_PATH.relative_to(ROOT)}")
    print(f"Generated XVA sensitivity table: {SENSITIVITY_PATH.relative_to(ROOT)}")
    print(f"Generated report: {REPORT_PATH.relative_to(ROOT)}")
    print(f"Generated figure: {FIGURE_PATH.relative_to(ROOT)}")


def build_sensitivity_table(clean_values, clean_value_at_base: float, discount_rate: float) -> pd.DataFrame:
    cases = [
        ("base", XVAAssumptions()),
        ("counterparty_spread_plus_50bp", XVAAssumptions(counterparty_spread_bps=150.0)),
        ("counterparty_spread_minus_50bp", XVAAssumptions(counterparty_spread_bps=50.0)),
        ("own_spread_plus_50bp", XVAAssumptions(own_spread_bps=130.0)),
        ("funding_spread_plus_25bp", XVAAssumptions(funding_spread_bps=75.0)),
        ("recovery_20pct", XVAAssumptions(recovery_rate=0.20)),
        ("recovery_60pct", XVAAssumptions(recovery_rate=0.60)),
    ]

    rows = []
    for case_name, assumptions in cases:
        result = compute_xva_from_clean_values(clean_values, clean_value_at_base, discount_rate, assumptions)
        rows.append(
            {
                "case": case_name,
                "counterparty_spread_bps": assumptions.counterparty_spread_bps,
                "own_spread_bps": assumptions.own_spread_bps,
                "funding_spread_bps": assumptions.funding_spread_bps,
                "recovery_rate": assumptions.recovery_rate,
                "expected_exposure": result["expected_exposure"],
                "pfe_95": result["pfe_95"],
                "cva": result["cva"],
                "dva": result["dva"],
                "fva": result["fva"],
                "xva_reserve": result["xva_reserve"],
                "xva_adjusted_payer_value": result["xva_adjusted_value"],
            }
        )
    return pd.DataFrame(rows)


def write_report(xva: pd.Series, exposure: pd.DataFrame, sensitivity: pd.DataFrame) -> None:
    report = f"""# XVA Validation Report

## Purpose

This layer extends the clean IR swap validation engine into transparent XVA review.

The objective is not to claim a production XVA engine. The objective is to show the validation path: exposure profile, expected exposure, PFE, CVA, DVA, FVA, sensitivities and model-use decision.

## Acronyms

| Acronym | Meaning | Use in this layer |
|---|---|---|
| EE | Expected Exposure | Average positive exposure across rate-shock scenarios |
| PFE | Potential Future Exposure | High-percentile positive exposure proxy |
| CVA | Credit Valuation Adjustment | Counterparty default-risk charge |
| DVA | Debit Valuation Adjustment | Own default-risk valuation benefit |
| FVA | Funding Valuation Adjustment | Funding-spread adjustment on positive exposure |
| XVA | Valuation adjustment framework | Combined CVA, DVA and FVA review layer |

## Base XVA result

| Metric | Value |
|---|---:|
| Clean payer NPV | {money(xva["clean_payer_npv"])} |
| Expected exposure | {money(xva["expected_exposure"])} |
| Expected negative exposure | {money(xva["expected_negative_exposure"])} |
| PFE 95 | {money(xva["pfe_95"])} |
| Counterparty PD | {pct(xva["counterparty_pd"])} |
| Own PD | {pct(xva["own_pd"])} |
| CVA | {money(xva["cva"])} |
| DVA | {money(xva["dva"])} |
| FVA | {money(xva["fva"])} |
| XVA reserve | {money(xva["xva_reserve"])} |
| XVA-adjusted payer value | {money(xva["xva_adjusted_payer_value"])} |

## Model-use decision

The XVA layer is available for transparent CVA, DVA and FVA review using the scenario exposure profile produced by the clean IR swap engine.

It is not a production exposure engine. The next validation gate is a time-grid exposure simulation with counterparty-specific credit calibration, collateral terms and netting-set treatment.

## Archer / MRM action

Create a linked XVA model record:

| Field | Record |
|---|---|
| Model ID | QMRL-XVA-IR-SWAP-001 |
| Source model | QMRL-IR-SWAP-001 |
| Product | Fixed-for-floating interest-rate swap |
| Stage | Transparent XVA validation layer |
| Monitoring trigger | Spread change, exposure sign change, funding spread change, recovery assumption change |
| Next gate | Time-grid EE/PFE simulation and counterparty-specific calibration |

## Sensitivity summary

{sensitivity.to_markdown(index=False)}
"""

    REPORT_PATH.write_text(report, encoding="utf-8")


def write_figure(exposure: pd.DataFrame, xva: pd.Series, sensitivity: pd.DataFrame) -> None:
    plt.close("all")
    fig, axes = plt.subplots(1, 3, figsize=(16.5, 5.8))
    fig.patch.set_facecolor("#f6f8fb")

    for ax in axes:
        ax.set_facecolor("white")
        ax.grid(True, color="#d7dde7", linewidth=0.8, alpha=0.75)
        for spine in ax.spines.values():
            spine.set_color("#9ca3af")

    shifts = exposure["curve_shift_bp"].astype(float)
    pos = exposure["positive_exposure"].astype(float)
    neg = exposure["negative_exposure"].astype(float)

    axes[0].bar(shifts, pos, width=28, label="Positive exposure", color="#15803d", alpha=0.85)
    axes[0].bar(shifts, -neg, width=28, label="Negative exposure", color="#b42318", alpha=0.80)
    axes[0].axhline(0, color="#374151", linewidth=1.0)
    axes[0].set_title("Scenario Exposure Profile", loc="left", fontweight="bold")
    axes[0].set_xlabel("Parallel curve shock, bp")
    axes[0].set_ylabel("Exposure")
    axes[0].legend(frameon=True, fontsize=8)

    components = pd.Series(
        {
            "CVA": float(xva["cva"]),
            "DVA": -float(xva["dva"]),
            "FVA": float(xva["fva"]),
            "Net reserve": float(xva["xva_reserve"]),
        }
    )
    colors = ["#b42318", "#15803d", "#b45309", "#374151"]
    axes[1].bar(components.index, components.values, color=colors, alpha=0.88)
    axes[1].axhline(0, color="#374151", linewidth=1.0)
    axes[1].set_title("XVA Components", loc="left", fontweight="bold")
    axes[1].set_ylabel("Value adjustment")

    axes[2].barh(sensitivity["case"], sensitivity["xva_reserve"], color="#374151", alpha=0.86)
    axes[2].axvline(float(xva["xva_reserve"]), color="#b42318", linewidth=1.2, linestyle="--", label="base")
    axes[2].set_title("XVA Reserve Sensitivity", loc="left", fontweight="bold")
    axes[2].set_xlabel("XVA reserve")
    axes[2].legend(frameon=True, fontsize=8)

    fig.suptitle("XVA Validation Layer: EE, PFE, CVA, DVA, FVA and Sensitivities", fontsize=16, fontweight="bold", x=0.03, ha="left")
    fig.text(
        0.03,
        0.02,
        "Model-use decision: transparent XVA review layer. Next gate: time-grid exposure simulation and counterparty-specific calibration.",
        fontsize=9.5,
        color="#111827",
    )

    fig.tight_layout(rect=[0.02, 0.06, 0.98, 0.90])
    FIGURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURE_PATH, dpi=220, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


if __name__ == "__main__":
    run_xva_validation()

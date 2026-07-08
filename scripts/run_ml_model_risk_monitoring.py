"""Run the ML model-risk monitoring layer.

This script builds official-data features, applies transparent model-risk
monitoring diagnostics, writes a report and creates a dashboard.

The layer is not a forecasting system. It is a validation and monitoring layer
for rates, FX and inflation input environments.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.gridspec import GridSpec

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from qmrl.ml_features import build_feature_panel_from_processed, build_model_risk_signals
from qmrl.model_selection import recommendation_records, select_active_monitoring_stack

PROCESSED = ROOT / "data" / "official" / "processed"
REPORTS = ROOT / "reports"
FIGURES = REPORTS / "figures"


def write_figure(signals: pd.DataFrame, score_table: pd.DataFrame, feature_panel: pd.DataFrame) -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)

    row = signals.iloc[0]

    def feature_label(name: str) -> str:
        labels = {
            "real_rate_proxy": "Real-rate proxy",
            "d_dgs10_bp": "10Y yield daily move",
            "d_slope_2s10_bp": "2s10s slope daily move",
            "d_slope_5s30_bp": "5s30s slope daily move",
            "d_bei_bp": "10Y BEI daily move",
            "d_real_rate_proxy_bp": "Real-rate proxy daily move",
            "fx_mean_abs_return": "FX mean absolute return",
            "fx_max_abs_return": "FX max absolute return",
        }
        return labels.get(str(name), str(name))

    fig = plt.figure(figsize=(16.0, 8.8))
    gs = GridSpec(2, 2, figure=fig, height_ratios=[1.0, 1.0], width_ratios=[1.06, 1.10])
    fig.patch.set_facecolor("#f7f8fa")

    ax_features = fig.add_subplot(gs[0, 0])
    ax_distance = fig.add_subplot(gs[0, 1])
    ax_pca = fig.add_subplot(gs[1, 0])
    ax_decision = fig.add_subplot(gs[1, 1])

    selected_features = str(row["selected_features"]).split("; ")
    latest_features = feature_panel.dropna(subset=selected_features).tail(252).copy()

    z_data = latest_features[selected_features]
    z_latest = ((z_data - z_data.mean()) / z_data.std().replace(0.0, 1.0)).tail(1).iloc[0]
    z_latest = z_latest.sort_values()

    z_plot = z_latest.copy()
    z_plot.index = [feature_label(name) for name in z_plot.index]

    ax_features.barh(z_plot.index, z_plot.values, alpha=0.88)
    ax_features.axvline(0, linewidth=1.0)
    ax_features.axvline(2, linewidth=1.0, linestyle="--")
    ax_features.axvline(-2, linewidth=1.0, linestyle="--")
    ax_features.set_title("Latest Standardized Input Moves", fontweight="bold")
    ax_features.set_xlabel("z-score versus recent official-data window")
    ax_features.grid(True, axis="x", alpha=0.25)

    for index, value in enumerate(z_plot.values):
        ax_features.text(
            value + (0.06 if value >= 0 else -0.06),
            index,
            f"{value:.2f}",
            va="center",
            ha="left" if value >= 0 else "right",
            fontsize=8.4,
        )

    ax_distance.plot(
        score_table["date"],
        score_table["mahalanobis_distance"],
        linewidth=2.2,
        label="Shrinkage Mahalanobis distance",
    )
    ax_distance.axhline(
        score_table["mahalanobis_distance"].quantile(0.95),
        linewidth=1.0,
        linestyle="--",
        label="95th percentile",
    )
    ax_distance.set_title("Multivariate Input Abnormality", fontweight="bold")
    ax_distance.set_ylabel("Distance")
    ax_distance.grid(True, alpha=0.25)
    ax_distance.legend(frameon=False, loc="upper left", fontsize=8.6)

    ax_pca.plot(
        score_table["date"],
        score_table["pca_reconstruction_error"],
        linewidth=2.2,
        label="PCA reconstruction error",
    )
    ax_pca.axhline(
        score_table["pca_reconstruction_error"].quantile(0.90),
        linewidth=1.0,
        linestyle="--",
        label="90th percentile",
    )
    ax_pca.set_title("Input-Structure Drift Monitor", fontweight="bold")
    ax_pca.set_ylabel("PCA reconstruction error")
    ax_pca.grid(True, alpha=0.25)
    ax_pca.legend(frameon=False, loc="upper left", fontsize=8.6)

    ax_decision.axis("off")

    max_z = float(row["max_abs_zscore"])
    mahala_pctile = float(row["mahalanobis_percentile"])
    pca_pctile = float(row["pca_error_percentile"])

    if pca_pctile >= 90 and mahala_pctile < 95 and max_z < 3:
        gate = "AMBER REVIEW"
        active_warning = "Factor-structure drift"
        blocked_action = "New exposure signoff, limit change, auto recalibration"
        allowed_action = "Monitoring, validation note, manual reviewer context"
    elif mahala_pctile >= 95 or max_z >= 3:
        gate = "RED REVIEW"
        active_warning = "Hard input abnormality"
        blocked_action = "Model-use signoff until formal review"
        allowed_action = "Exception reporting only"
    else:
        gate = "GREEN WATCH"
        active_warning = "No major breach"
        blocked_action = "None from this ML layer"
        allowed_action = "Normal monitoring"

    decision_lines = [
        "ML DECISION INTELLIGENCE",
        f"{gate} | Pressure {row['ml_pressure_score']:.0f}/100",
        "",
        "Current read",
        f"Active warning: {active_warning}.",
        f"Max z {max_z:.2f}: no hard single-input breach.",
        f"Mahalanobis pctile {mahala_pctile:.0f}: elevated, below 95 stop level.",
        f"PCA drift pctile {pca_pctile:.0f}: main decision driver.",
        f"Regime: {row['kmeans_regime']}.",
        "",
        "Decision matrix",
        f"Allowed now: {allowed_action}.",
        f"Blocked now: {blocked_action}.",
        "Model stop: no, unless Mahalanobis >=95 or max z >=3.",
        "",
        "Bank next action",
        "1. Write validation note: PCA drift active, no hard input breach.",
        "2. Decompose drift by rates, BEI, real-rate proxy and FX.",
        "3. Rerun 126D and 252D windows before signoff changes.",
        "4. Escalate only if drift persists or stop thresholds breach.",
        "",
        "Investor next action",
        "1. Do not add risk from this ML layer.",
        "2. Add exposure only if curve and inflation dashboards agree.",
        "3. If dashboards conflict, reduce size, widen bands or delay.",
    ]

    decision_text = chr(10).join(decision_lines)

    ax_decision.text(
        0.04,
        0.96,
        decision_text,
        va="top",
        ha="left",
        fontsize=7.45,
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
        f"ML Model-Risk Monitoring Dashboard | State: {row['decision_state']} | Date: {row['date']}",
        fontsize=15,
        fontweight="bold",
        y=0.98,
    )

    kpi_items = [
        ("STATE", str(row["decision_state"])),
        ("PRESSURE", f"{row['ml_pressure_score']:.0f}/100"),
        ("MAX Z", f"{row['max_abs_zscore']:.2f}"),
        ("MAHALA PCTILE", f"{row['mahalanobis_percentile']:.0f}"),
        ("PCA PCTILE", f"{row['pca_error_percentile']:.0f}"),
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
        "Legend: z-score = standardized input move | Mahalanobis = covariance-adjusted abnormality | PCA error = input-structure drift | KMeans = static regime label.",
        fontsize=8.0,
    )

    fig.text(
        0.012,
        0.006,
        "Source: repository official-data pipeline. ML model-risk monitoring artifact, not a forecasting model or investment advice.",
        fontsize=7.9,
    )

    fig.tight_layout(rect=[0, 0.055, 1, 0.885])
    fig.savefig(FIGURES / "ml_model_risk_monitoring_map.png", dpi=240)
    plt.close(fig)

def write_report(signals: pd.DataFrame, selected_records: list[dict[str, object]]) -> None:
    row = signals.iloc[0]

    selection_rows = "\n".join(
        [
            "| {validation_question} | {primary_tool} | {challenger_tool} | {implemented_in_v07} | {rationale} |".format(**record)
            for record in selected_records
        ]
    )

    report = f"""# ML Model-Risk Monitoring Report

## Decision state: {row['decision_state']}

**Monitoring date:** {row['date']}  
**ML pressure score:** {row['ml_pressure_score']:.1f} / 100  
**Decision flags:** {row['decision_flags']}  
**Static regime:** {row['kmeans_regime']}

![ML model-risk monitoring map](figures/ml_model_risk_monitoring_map.png)

## Direct interpretation

This layer does not forecast markets. It creates a model-risk decision gate from official rates, FX and inflation inputs.

**Decision gate: AMBER REVIEW.**

The active warning is input-structure drift, not a hard single-variable shock. The latest maximum z-score is below the hard breach threshold, and the Mahalanobis percentile is elevated but below the stop-review level. PCA drift is the main issue because the recent factor structure is less stable than usual.

Decision consequence:

| Action | Decision |
|---|---|
| Use model output for monitoring | Allowed |
| New exposure signoff from this ML layer | Blocked |
| Automatic threshold recalibration | Blocked |
| Limit change | Blocked |
| Formal model stop | Not triggered |
| Escalation trigger | PCA drift persistence, Mahalanobis >= 95, or max z >= 3 |

## Latest signals

| Signal | Value |
|---|---:|
| Max absolute rolling z-score | {row['max_abs_zscore']:.3f} |
| Main z-score feature | {row['max_abs_zscore_feature']} |
| Mahalanobis distance | {row['mahalanobis_distance']:.3f} |
| Mahalanobis percentile | {row['mahalanobis_percentile']:.1f} |
| PCA reconstruction error | {row['pca_reconstruction_error']:.3f} |
| PCA error percentile | {row['pca_error_percentile']:.1f} |
| Static regime | {row['kmeans_regime']} |

## Model-selection table

| Validation question | Primary tool | Challenger tool | Implemented in v0.7 | Rationale |
|---|---|---|---:|---|
{selection_rows}

## Bank implication

The bank decision is an Amber Review gate. Keep the model available for monitoring and reviewer context, but block new exposure signoff, automatic threshold recalibration and limit changes from this ML layer. The validation note should state: PCA drift is active, no hard single-input breach is present, and the joint input state is elevated but below the stop-review threshold. The next task is to decompose the drift into rates, BEI, real-rate proxy and FX drivers, then rerun the monitoring stack under 126D and 252D windows. Escalate only if PCA drift persists across refreshes, Mahalanobis distance crosses the 95th percentile, or the maximum z-score breaches 3.

## Investor implication

The investor decision is to avoid adding risk from this ML layer alone. The ML layer is warning that the input structure is unstable, not giving an exposure direction. Exposure can be increased only if the curve dashboard and the inflation-derivatives dashboard confirm the same direction. If those dashboards disagree, reduce sizing, widen risk bands or delay the trade.

## Validator challenge

Challenge whether the selected tool matches the validation question. A univariate breach should not be treated the same as covariance instability. PCA drift should not be treated as a trading signal. KMeans regime labels are static monitoring labels, not causal explanations. Isolation Forest and Gaussian HMM remain challenger roadmap tools until separately implemented and tested.

## Limitations

This v0.7 layer uses transparent dependency-light diagnostics: rolling z-scores, percentile ranks, shrinkage Mahalanobis distance, PCA reconstruction error and deterministic KMeans clustering. It does not yet implement Isolation Forest, Gaussian Mixture Models or Gaussian Hidden Markov Models.
"""

    (REPORTS / "ml_model_risk_monitoring_report.md").write_text(report, encoding="utf-8")


def main() -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)
    PROCESSED.mkdir(parents=True, exist_ok=True)

    feature_panel = build_feature_panel_from_processed(PROCESSED)
    signals, score_table, selected_features = build_model_risk_signals(feature_panel)

    feature_panel.to_csv(PROCESSED / "ml_model_risk_features.csv", index=False)
    signals.to_csv(PROCESSED / "ml_model_risk_signals.csv", index=False)
    score_table.to_csv(PROCESSED / "ml_model_risk_score_table.csv", index=False)

    records = recommendation_records()
    pd.DataFrame(records).to_csv(PROCESSED / "ml_model_selection_table.csv", index=False)

    write_figure(signals, score_table, feature_panel)
    write_report(signals, records)

    print("ML model-risk monitoring complete.")
    print("Generated report: reports/ml_model_risk_monitoring_report.md")
    print("Generated figure: reports/figures/ml_model_risk_monitoring_map.png")
    print("Generated features: data/official/processed/ml_model_risk_features.csv")
    print("Generated signals: data/official/processed/ml_model_risk_signals.csv")
    print("Generated score table: data/official/processed/ml_model_risk_score_table.csv")
    print("Generated model-selection table: data/official/processed/ml_model_selection_table.csv")


if __name__ == "__main__":
    main()

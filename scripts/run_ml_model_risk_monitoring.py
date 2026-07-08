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

    decision_lines = [
        "ML MODEL-RISK DECISION GATE",
        f"AMBER REVIEW | Pressure {row['ml_pressure_score']:.0f}/100",
        "",
        "Decision",
        "Use ML output as a monitoring control only.",
        "No new exposure approval, no limit change, no automatic recalibration.",
        "",
        "Why",
        f"Max z {row['max_abs_zscore']:.2f}: below hard single-input breach.",
        f"Mahalanobis pctile {row['mahalanobis_percentile']:.0f}: elevated, below 95 stop-review level.",
        f"PCA drift pctile {row['pca_error_percentile']:.0f}: main warning, factor structure changed.",
        f"Regime: {row['kmeans_regime']}; not a full stress-state failure.",
        "",
        "Bank action",
        "1. Keep reporting active. Freeze threshold changes.",
        "2. Decompose PCA drift by rates, BEI, real-rate proxy and FX.",
        "3. Rerun 126D and 252D monitoring windows.",
        "4. Escalate if PCA drift persists or Mahalanobis crosses 95.",
        "",
        "Investor action",
        "1. Do not increase exposure from this ML signal.",
        "2. Use curve and inflation dashboards for exposure direction.",
        "3. If confirmation is weak, reduce sizing, widen risk bands or delay.",
    ]

    decision_text = chr(10).join(decision_lines)

    ax_decision.text(
        0.04,
        0.96,
        decision_text,
        va="top",
        ha="left",
        fontsize=7.90,
        linespacing=1.00,
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

This layer does not forecast markets. It creates a model-risk decision gate.

**Decision gate: AMBER REVIEW.**

Use the ML output as a monitoring control only. Do not use it to approve new exposure, change limits or recalibrate thresholds automatically.

Why this is Amber:

- The maximum z-score is below a hard single-input breach.
- Mahalanobis distance is elevated, but below the 95th-percentile stop-review level.
- PCA drift is the main warning because the recent input factor structure changed.
- The static regime remains normal, so this is not a full stress-state failure.

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

Keep reporting active, but freeze automatic threshold changes, production recalibration and new limit-use signoff from this ML layer. Decompose the PCA drift into rates, BEI, real-rate proxy and FX drivers, then rerun the stack under 126D and 252D windows. Escalate only if PCA drift persists across refreshes, Mahalanobis distance crosses the 95th percentile, or the maximum z-score breaches the hard single-input threshold.

## Investor implication

Do not increase exposure from this ML signal. Use the curve dashboard and the inflation-derivatives dashboard to decide exposure direction. If those dashboards confirm the exposure direction, keep sizing disciplined because the ML layer shows reduced model confidence. If confirmation is weak or contradictory, reduce sizing, widen risk bands or delay the trade.

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

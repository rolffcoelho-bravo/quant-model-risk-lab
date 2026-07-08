"""Dynamic model-selection logic for model-risk monitoring.

This module explains which monitoring tools are appropriate for each validation
question. It is deliberately transparent: the selected tool is tied to the
model-risk question, not to a black-box forecasting objective.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelToolRecommendation:
    validation_question: str
    primary_tool: str
    challenger_tool: str
    implemented_in_v07: bool
    rationale: str


def build_model_selection_table() -> list[ModelToolRecommendation]:
    return [
        ModelToolRecommendation(
            validation_question="Is the current input move abnormal in one variable?",
            primary_tool="Rolling z-score",
            challenger_tool="Rolling percentile rank",
            implemented_in_v07=True,
            rationale="Useful for direct input-level breaches and easy validation audit trails.",
        ),
        ModelToolRecommendation(
            validation_question="Is the joint rates, FX and inflation state abnormal?",
            primary_tool="Shrinkage Mahalanobis distance",
            challenger_tool="Robust covariance / Elliptic Envelope",
            implemented_in_v07=True,
            rationale="Captures covariance-adjusted multivariate abnormality with stabilized covariance estimates.",
        ),
        ModelToolRecommendation(
            validation_question="Has the input factor structure drifted?",
            primary_tool="PCA reconstruction error",
            challenger_tool="Kernel PCA",
            implemented_in_v07=True,
            rationale="Detects whether current inputs are poorly explained by the recent factor structure.",
        ),
        ModelToolRecommendation(
            validation_question="Which static monitoring regime is active?",
            primary_tool="KMeans regime clustering",
            challenger_tool="Gaussian Mixture Model",
            implemented_in_v07=True,
            rationale="Provides a transparent static input-regime classification for monitoring reports.",
        ),
        ModelToolRecommendation(
            validation_question="Is there nonlinear anomaly behavior beyond distance metrics?",
            primary_tool="Isolation Forest",
            challenger_tool="Local Outlier Factor",
            implemented_in_v07=False,
            rationale="Planned challenger for nonlinear anomaly detection once dependency policy is expanded.",
        ),
        ModelToolRecommendation(
            validation_question="Is the system switching dynamically between latent regimes?",
            primary_tool="Gaussian Hidden Markov Model",
            challenger_tool="Kalman/state-space model",
            implemented_in_v07=False,
            rationale="Reserved for the dynamic regime layer after static monitoring is validated.",
        ),
    ]


def recommendation_records() -> list[dict[str, object]]:
    return [
        {
            "validation_question": item.validation_question,
            "primary_tool": item.primary_tool,
            "challenger_tool": item.challenger_tool,
            "implemented_in_v07": item.implemented_in_v07,
            "rationale": item.rationale,
        }
        for item in build_model_selection_table()
    ]


def select_active_monitoring_stack(pressure_score: float, pca_percentile: float, mahalanobis_percentile: float) -> list[str]:
    stack = ["Rolling z-score", "Rolling percentile rank", "Shrinkage Mahalanobis distance"]

    if pca_percentile >= 80.0:
        stack.append("PCA reconstruction error")

    if mahalanobis_percentile >= 85.0:
        stack.append("Static regime clustering")

    if pressure_score >= 70.0:
        stack.append("Enhanced validation review")

    return stack

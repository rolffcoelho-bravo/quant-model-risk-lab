"""Quantitative monitoring and revalidation controls for FX options."""

from __future__ import annotations

from dataclasses import dataclass
import math

from qmrl.fx_option_governance import MonitoringPolicy


@dataclass(frozen=True)
class FXOptionMonitoringSnapshot:
    spot_rate: float
    realised_volatility: float
    domestic_rate: float
    foreign_rate: float
    parity_relative_gap: float
    call_delta: float
    vega: float


@dataclass(frozen=True)
class FXOptionMonitoringResult:
    monitoring_status: str
    revalidation_required: bool
    alerts: tuple[str, ...]
    spot_move_relative: float
    realised_volatility_change_absolute: float
    domestic_rate_change_absolute: float
    foreign_rate_change_absolute: float
    parity_relative_gap: float
    delta_sign_change: bool
    vega_sign_change: bool


def _relative_change(
    current: float,
    baseline: float,
) -> float:
    denominator = max(
        abs(float(baseline)),
        1.0e-12,
    )

    return abs(
        float(current)
        - float(baseline)
    ) / denominator


def _sign_change(
    current: float,
    baseline: float,
) -> bool:
    current_value = float(current)
    baseline_value = float(baseline)

    if (
        math.isclose(current_value, 0.0)
        or math.isclose(baseline_value, 0.0)
    ):
        return False

    return (
        current_value > 0.0
    ) != (
        baseline_value > 0.0
    )


def evaluate_fx_option_monitoring(
    *,
    current: FXOptionMonitoringSnapshot,
    baseline: FXOptionMonitoringSnapshot,
    policy: MonitoringPolicy,
) -> FXOptionMonitoringResult:
    """Evaluate quantitative alerts and the revalidation decision."""
    spot_move = _relative_change(
        current.spot_rate,
        baseline.spot_rate,
    )

    volatility_change = abs(
        float(current.realised_volatility)
        - float(baseline.realised_volatility)
    )

    domestic_rate_change = abs(
        float(current.domestic_rate)
        - float(baseline.domestic_rate)
    )

    foreign_rate_change = abs(
        float(current.foreign_rate)
        - float(baseline.foreign_rate)
    )

    parity_relative_gap = abs(
        float(current.parity_relative_gap)
    )

    delta_sign_change = (
        policy.monitor_delta_sign_change
        and _sign_change(
            current.call_delta,
            baseline.call_delta,
        )
    )

    vega_sign_change = (
        policy.monitor_vega_sign_change
        and _sign_change(
            current.vega,
            baseline.vega,
        )
    )

    alerts: list[str] = []

    if (
        spot_move
        >= policy.spot_move_relative_threshold
    ):
        alerts.append("SPOT_MOVE_THRESHOLD_BREACH")

    if (
        volatility_change
        >= policy.realised_volatility_change_absolute_threshold
    ):
        alerts.append(
            "REALISED_VOLATILITY_THRESHOLD_BREACH"
        )

    if (
        domestic_rate_change
        >= policy.domestic_rate_change_absolute_threshold
    ):
        alerts.append(
            "DOMESTIC_RATE_THRESHOLD_BREACH"
        )

    if (
        foreign_rate_change
        >= policy.foreign_rate_change_absolute_threshold
    ):
        alerts.append(
            "FOREIGN_RATE_THRESHOLD_BREACH"
        )

    if (
        parity_relative_gap
        >= policy.parity_relative_gap_threshold
    ):
        alerts.append(
            "PARITY_RELATIVE_GAP_THRESHOLD_BREACH"
        )

    if delta_sign_change:
        alerts.append("CALL_DELTA_SIGN_CHANGE")

    if vega_sign_change:
        alerts.append("VEGA_SIGN_CHANGE")

    revalidation_required = bool(alerts)

    return FXOptionMonitoringResult(
        monitoring_status=(
            policy.revalidation_status_on_breach
            if revalidation_required
            else "PASS"
        ),
        revalidation_required=revalidation_required,
        alerts=tuple(alerts),
        spot_move_relative=spot_move,
        realised_volatility_change_absolute=(
            volatility_change
        ),
        domestic_rate_change_absolute=(
            domestic_rate_change
        ),
        foreign_rate_change_absolute=(
            foreign_rate_change
        ),
        parity_relative_gap=parity_relative_gap,
        delta_sign_change=delta_sign_change,
        vega_sign_change=vega_sign_change,
    )
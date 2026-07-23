"""Initial-margin proxy calculations for v1.4 Gate 3."""

from __future__ import annotations

import hashlib
import json
import math
from statistics import NormalDist

from .domain import (
    InitialMarginProfile,
    MarginPolicy,
    ParametricMarginInput,
    PathwiseMarginInput,
)


def policy_hash(policy: MarginPolicy) -> str:
    payload = {
        "method": policy.method,
        "confidence_level": policy.confidence_level,
        "margin_period_days": policy.margin_period_days,
        "base_margin_days": policy.base_margin_days,
        "addon_rate": policy.addon_rate,
        "minimum_margin": policy.minimum_margin,
        "received_margin_reusable": policy.received_margin_reusable,
        "posted_margin_segregated": policy.posted_margin_segregated,
        "integration_rule": policy.integration_rule,
        "survival_treatment": policy.survival_treatment,
        "proxy_label": policy.proxy_label,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def empirical_quantile(values: tuple[float, ...], probability: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(float(value) for value in values)
    if len(ordered) == 1:
        return ordered[0]
    location = probability * (len(ordered) - 1)
    lower = int(math.floor(location))
    upper = int(math.ceil(location))
    if lower == upper:
        return ordered[lower]
    weight = location - lower
    return ordered[lower] + weight * (ordered[upper] - ordered[lower])


def _horizon_index(times: tuple[float, ...], index: int, margin_period_days: int) -> int:
    target = times[index] + margin_period_days / 365.0
    for candidate in range(index + 1, len(times)):
        if times[candidate] + 1e-15 >= target:
            return candidate
    return len(times) - 1


def calculate_historical_initial_margin(
    risk_input: PathwiseMarginInput,
    policy: MarginPolicy,
) -> InitialMarginProfile:
    if policy.method != "historical_simulation":
        raise ValueError("Historical calculation requires historical_simulation policy.")
    posted: list[float] = []
    received: list[float] = []
    for index in range(len(risk_input.times)):
        horizon = _horizon_index(
            risk_input.times,
            index,
            policy.margin_period_days,
        )
        if horizon == index:
            posted.append(0.0)
            received.append(0.0)
            continue
        losses = tuple(
            max(path[index] - path[horizon], 0.0)
            for path in risk_input.values
        )
        gains = tuple(
            max(path[horizon] - path[index], 0.0)
            for path in risk_input.values
        )
        gross_scale = sum(abs(path[index]) for path in risk_input.values) / risk_input.path_count
        addon = policy.addon_rate * gross_scale
        posted.append(
            max(
                policy.minimum_margin,
                empirical_quantile(losses, policy.confidence_level) + addon,
            )
        )
        received.append(
            max(
                policy.minimum_margin,
                empirical_quantile(gains, policy.confidence_level) + addon,
            )
        )
    return InitialMarginProfile(
        netting_set_id=risk_input.netting_set_id,
        currency=risk_input.currency,
        times=risk_input.times,
        posted_margin=tuple(posted),
        received_margin=tuple(received),
        method=policy.method,
        policy_hash=policy_hash(policy),
        received_margin_reusable=policy.received_margin_reusable,
        proxy_label=policy.proxy_label,
    )


def _quadratic_form(vector: tuple[float, ...], matrix: tuple[tuple[float, ...], ...]) -> float:
    value = 0.0
    for i, left in enumerate(vector):
        for j, right in enumerate(vector):
            value += left * matrix[i][j] * right
    if value < -1e-10:
        raise ValueError("Covariance produces a negative portfolio variance.")
    return max(value, 0.0)


def calculate_parametric_initial_margin(
    risk_input: ParametricMarginInput,
    policy: MarginPolicy,
) -> InitialMarginProfile:
    if policy.method != "parametric":
        raise ValueError("Parametric calculation requires parametric policy.")
    quantile = NormalDist().inv_cdf(policy.confidence_level)
    horizon_scale = math.sqrt(policy.margin_period_days / policy.base_margin_days)
    posted: list[float] = []
    received: list[float] = []
    for sensitivities in risk_input.sensitivities:
        sigma = math.sqrt(_quadratic_form(sensitivities, risk_input.covariance))
        base = quantile * sigma * horizon_scale * risk_input.volatility_scale
        addon = policy.addon_rate * sum(abs(value) for value in sensitivities)
        posted.append(
            max(
                policy.minimum_margin,
                base * risk_input.posted_multiplier + addon,
            )
        )
        received.append(
            max(
                policy.minimum_margin,
                base * risk_input.received_multiplier + addon,
            )
        )
    return InitialMarginProfile(
        netting_set_id=risk_input.netting_set_id,
        currency=risk_input.currency,
        times=risk_input.times,
        posted_margin=tuple(posted),
        received_margin=tuple(received),
        method=policy.method,
        policy_hash=policy_hash(policy),
        received_margin_reusable=policy.received_margin_reusable,
        proxy_label=policy.proxy_label,
    )


def scale_margin_profile(
    profile: InitialMarginProfile,
    factor: float,
) -> InitialMarginProfile:
    scale = float(factor)
    if scale < 0.0 or not math.isfinite(scale):
        raise ValueError("Margin scale must be finite and non-negative.")
    return InitialMarginProfile(
        netting_set_id=profile.netting_set_id,
        currency=profile.currency,
        times=profile.times,
        posted_margin=tuple(value * scale for value in profile.posted_margin),
        received_margin=tuple(value * scale for value in profile.received_margin),
        method=profile.method,
        policy_hash=profile.policy_hash,
        received_margin_reusable=profile.received_margin_reusable,
        proxy_label=profile.proxy_label,
    )

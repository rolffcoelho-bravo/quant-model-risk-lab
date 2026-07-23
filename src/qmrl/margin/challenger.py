"""Independent loop challenger for Gate 3 MVA."""

from __future__ import annotations

from qmrl.multicurrency import CurrencyCurveSet

from .domain import (
    InitialMarginProfile,
    MarginPolicy,
    MVAChallengeReport,
    SurvivalProfile,
)


def independent_mva(
    profile: InitialMarginProfile,
    curve_set: CurrencyCurveSet,
    policy: MarginPolicy,
    *,
    survival: SurvivalProfile | None = None,
) -> float:
    posted_total = 0.0
    benefit_total = 0.0
    for index in range(len(profile.times) - 1):
        right = index + 1
        dt = profile.times[right] - profile.times[index]
        if policy.integration_rule == "endpoint":
            posted = profile.posted_margin[right]
            received = profile.received_margin[right]
        else:
            posted = (profile.posted_margin[index] + profile.posted_margin[right]) / 2.0
            received = (profile.received_margin[index] + profile.received_margin[right]) / 2.0
        spread = max(
            curve_set.funding_spread(profile.currency, profile.times[right])
            - curve_set.collateral_rate(profile.currency, profile.times[right]),
            0.0,
        )
        if survival is None or policy.survival_treatment == "none":
            survival_weight = 1.0
        elif policy.survival_treatment == "joint":
            survival_weight = (
                survival.own_survival[right]
                * survival.counterparty_survival[right]
            )
        elif policy.survival_treatment == "own":
            survival_weight = survival.own_survival[right]
        else:
            survival_weight = survival.counterparty_survival[right]
        common = (
            curve_set.discount_factor(profile.currency, profile.times[right])
            * spread
            * survival_weight
            * dt
        )
        posted_total += common * posted
        if profile.received_margin_reusable:
            benefit_total += common * received
    return posted_total - benefit_total


def challenge_mva(
    primary_net_mva: float,
    profile: InitialMarginProfile,
    curve_set: CurrencyCurveSet,
    policy: MarginPolicy,
    *,
    survival: SurvivalProfile | None = None,
    tolerance: float = 1e-10,
) -> MVAChallengeReport:
    challenger = independent_mva(
        profile,
        curve_set,
        policy,
        survival=survival,
    )
    absolute = abs(primary_net_mva - challenger)
    scale = max(abs(primary_net_mva), abs(challenger), 1e-15)
    relative = absolute / scale
    return MVAChallengeReport(
        status="PASS" if absolute <= tolerance else "REMEDIATE",
        primary_net_mva=primary_net_mva,
        challenger_net_mva=challenger,
        absolute_difference=absolute,
        relative_difference=relative,
        tolerance=tolerance,
    )

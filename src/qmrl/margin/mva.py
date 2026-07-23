"""Margin Valuation Adjustment integration for v1.4 Gate 3."""

from __future__ import annotations

from qmrl.multicurrency import CurrencyCurveSet

from .domain import (
    InitialMarginProfile,
    MarginPolicy,
    MVABucket,
    MVAResult,
    SurvivalProfile,
)


def _survival_multiplier(
    survival: SurvivalProfile | None,
    index: int,
    treatment: str,
) -> float:
    if survival is None or treatment == "none":
        return 1.0
    own = survival.own_survival[index]
    counterparty = survival.counterparty_survival[index]
    if treatment == "joint":
        return own * counterparty
    if treatment == "own":
        return own
    if treatment == "counterparty":
        return counterparty
    raise ValueError("Unsupported survival treatment.")


def _interval_amount(values: tuple[float, ...], index: int, rule: str) -> float:
    if rule == "endpoint":
        return values[index]
    return 0.5 * (values[index - 1] + values[index])


def calculate_mva(
    profile: InitialMarginProfile,
    curve_set: CurrencyCurveSet,
    policy: MarginPolicy,
    *,
    survival: SurvivalProfile | None = None,
    funding_spread_shift_bps: float = 0.0,
    remuneration_shift_bps: float = 0.0,
    margin_scale: float = 1.0,
) -> MVAResult:
    if profile.policy_hash == "":
        raise ValueError("Margin profile requires a policy hash.")
    if survival is not None and survival.times != profile.times:
        raise ValueError("Survival and margin time grids must agree.")
    if margin_scale < 0.0:
        raise ValueError("margin_scale cannot be negative.")
    funding_shift = float(funding_spread_shift_bps) / 10000.0
    remuneration_shift = float(remuneration_shift_bps) / 10000.0
    buckets: list[MVABucket] = []
    posted_total = 0.0
    received_total = 0.0
    for index in range(1, len(profile.times)):
        start = profile.times[index - 1]
        end = profile.times[index]
        dt = end - start
        posted = _interval_amount(profile.posted_margin, index, policy.integration_rule) * margin_scale
        received = _interval_amount(profile.received_margin, index, policy.integration_rule) * margin_scale
        discount = curve_set.discount_factor(profile.currency, end)
        funding = curve_set.funding_spread(profile.currency, end) + funding_shift
        remuneration = curve_set.collateral_rate(profile.currency, end) + remuneration_shift
        effective_spread = max(funding - remuneration, 0.0)
        survival_weight = _survival_multiplier(survival, index, policy.survival_treatment)
        common = discount * survival_weight * effective_spread * dt
        posted_cost = common * posted
        received_benefit = common * received if profile.received_margin_reusable else 0.0
        net = posted_cost - received_benefit
        posted_total += posted_cost
        received_total += received_benefit
        buckets.append(
            MVABucket(
                start_time=start,
                end_time=end,
                posted_cost=posted_cost,
                received_benefit=received_benefit,
                net_mva=net,
            )
        )
    return MVAResult(
        netting_set_id=profile.netting_set_id,
        currency=profile.currency,
        posted_mva=posted_total,
        received_margin_benefit=received_total,
        net_mva=posted_total - received_total,
        buckets=tuple(buckets),
        policy_hash=profile.policy_hash,
        fva_embedded=False,
        proxy_label=profile.proxy_label,
    )

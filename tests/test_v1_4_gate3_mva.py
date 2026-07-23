import math

from qmrl.margin import calculate_mva

from v1_4_gate3_helpers import curves, historical_policy, margin_profile, survival


def test_mva_is_positive_for_posted_margin_and_positive_spread():
    result = calculate_mva(margin_profile(), curves(), historical_policy())
    assert result.posted_mva > 0.0
    assert result.net_mva > 0.0


def test_zero_effective_spread_produces_zero_mva():
    result = calculate_mva(
        margin_profile(),
        curves(funding=(0.005, 0.005, 0.005), remuneration=(0.005, 0.005, 0.005)),
        historical_policy(),
    )
    assert result.net_mva == 0.0


def test_received_margin_benefit_requires_reuse():
    non_reusable = calculate_mva(margin_profile(reusable=False), curves(), historical_policy())
    reusable = calculate_mva(
        margin_profile(reusable=True),
        curves(),
        historical_policy(received_margin_reusable=True),
    )
    assert non_reusable.received_margin_benefit == 0.0
    assert reusable.received_margin_benefit > 0.0


def test_funding_spread_bump_increases_mva():
    base = calculate_mva(margin_profile(), curves(), historical_policy())
    bumped = calculate_mva(
        margin_profile(), curves(), historical_policy(), funding_spread_shift_bps=10.0
    )
    assert bumped.net_mva > base.net_mva


def test_remuneration_bump_reduces_mva():
    base = calculate_mva(margin_profile(), curves(), historical_policy())
    bumped = calculate_mva(
        margin_profile(), curves(), historical_policy(), remuneration_shift_bps=10.0
    )
    assert bumped.net_mva < base.net_mva


def test_margin_scale_is_linear():
    base = calculate_mva(margin_profile(), curves(), historical_policy())
    scaled = calculate_mva(
        margin_profile(), curves(), historical_policy(), margin_scale=1.25
    )
    assert math.isclose(scaled.net_mva, base.net_mva * 1.25, rel_tol=1e-12)


def test_joint_survival_reduces_mva():
    no_survival = calculate_mva(margin_profile(), curves(), historical_policy())
    joint = calculate_mva(
        margin_profile(),
        curves(),
        historical_policy(survival_treatment="joint"),
        survival=survival(),
    )
    assert joint.net_mva < no_survival.net_mva


def test_mva_is_explicitly_separate_from_fva():
    result = calculate_mva(margin_profile(), curves(), historical_policy())
    assert result.fva_embedded is False
    assert math.isclose(
        result.net_mva,
        result.posted_mva - result.received_margin_benefit,
    )

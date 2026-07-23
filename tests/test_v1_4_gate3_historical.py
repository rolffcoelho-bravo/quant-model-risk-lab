from qmrl.margin import (
    MarginPolicy,
    PathwiseMarginInput,
    calculate_historical_initial_margin,
    empirical_quantile,
    scale_margin_profile,
)

from v1_4_gate3_helpers import historical_input, historical_policy


def test_empirical_quantile_linear_interpolation():
    assert empirical_quantile((0.0, 10.0), 0.75) == 7.5


def test_historical_profile_is_deterministic():
    first = calculate_historical_initial_margin(historical_input(), historical_policy())
    second = calculate_historical_initial_margin(historical_input(), historical_policy())
    assert first == second


def test_historical_profile_produces_posted_and_received_margin():
    profile = calculate_historical_initial_margin(historical_input(), historical_policy())
    assert profile.posted_margin[0] > 0.0
    assert profile.received_margin[0] > 0.0


def test_historical_final_margin_is_zero_at_maturity():
    profile = calculate_historical_initial_margin(historical_input(), historical_policy())
    assert profile.posted_margin[-1] == 0.0
    assert profile.received_margin[-1] == 0.0


def test_higher_confidence_does_not_reduce_posted_margin():
    low = calculate_historical_initial_margin(
        historical_input(), historical_policy(confidence_level=0.60)
    )
    high = calculate_historical_initial_margin(
        historical_input(), historical_policy(confidence_level=0.95)
    )
    assert high.posted_margin[0] >= low.posted_margin[0]


def test_addon_increases_margin():
    base = calculate_historical_initial_margin(historical_input(), historical_policy())
    addon = calculate_historical_initial_margin(
        historical_input(), historical_policy(addon_rate=0.10)
    )
    assert addon.posted_margin[0] > base.posted_margin[0]


def test_minimum_margin_is_enforced():
    zero = PathwiseMarginInput("NS", "USD", (0.0, 1.0), ((0.0, 0.0),))
    profile = calculate_historical_initial_margin(
        zero,
        MarginPolicy(
            method="historical_simulation",
            confidence_level=0.99,
            margin_period_days=365,
            minimum_margin=25.0,
        ),
    )
    assert profile.posted_margin[0] == 25.0


def test_scale_margin_profile_is_linear():
    profile = calculate_historical_initial_margin(historical_input(), historical_policy())
    scaled = scale_margin_profile(profile, 1.5)
    assert scaled.posted_margin[0] == profile.posted_margin[0] * 1.5

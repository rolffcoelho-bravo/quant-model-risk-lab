from src.qmrl.inflation_pricing import (
    build_inflation_shock_table,
    build_inflation_validation_result,
    compounded_inflation_factor,
    inflation_dv01,
    zero_coupon_inflation_value,
)


def test_compounded_inflation_factor_above_one_for_positive_rate():
    factor = compounded_inflation_factor(rate_percent=2.5, maturity_years=10.0)

    assert factor > 1.0


def test_zero_coupon_inflation_value_is_zero_at_inception_when_market_equals_fixed():
    value = zero_coupon_inflation_value(
        fixed_rate_percent=2.25,
        market_rate_percent=2.25,
        nominal_discount_rate_percent=4.50,
        maturity_years=10.0,
        notional=1_000_000.0,
    )

    assert abs(value) < 1e-6


def test_positive_inflation_shock_increases_receiver_value():
    value = zero_coupon_inflation_value(
        fixed_rate_percent=2.25,
        market_rate_percent=3.25,
        nominal_discount_rate_percent=4.50,
        maturity_years=10.0,
        notional=1_000_000.0,
    )

    assert value > 0.0


def test_inflation_dv01_is_positive_for_receiver_inflation_exposure():
    dv01 = inflation_dv01(
        fixed_rate_percent=2.25,
        market_rate_percent=2.25,
        nominal_discount_rate_percent=4.50,
        maturity_years=10.0,
        notional=1_000_000.0,
    )

    assert dv01 > 0.0


def test_inflation_shock_table_contains_base_and_extreme_shocks():
    table = build_inflation_shock_table(
        fixed_rate_percent=2.25,
        base_market_rate_percent=2.25,
        nominal_discount_rate_percent=4.50,
        maturity_years=10.0,
        notional=1_000_000.0,
        shock_basis_points=[-100.0, 0.0, 100.0],
    )

    assert set(table["inflation_shock_bp"]) == {-100.0, 0.0, 100.0}
    assert len(table) == 3


def test_inflation_validation_result_has_expected_fields():
    result = build_inflation_validation_result(
        fixed_rate_percent=2.25,
        market_rate_percent=2.25,
        nominal_discount_rate_percent=4.50,
        maturity_years=10.0,
        notional=1_000_000.0,
    )

    assert result.maturity_years == 10.0
    assert result.notional == 1_000_000.0
    assert result.inflation_dv01 > 0.0

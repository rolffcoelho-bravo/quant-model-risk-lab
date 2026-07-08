from src.qmrl.curve_pricing import (
    bond_dv01_from_curve,
    build_discount_curve,
    build_parallel_shock_table,
    discount_factor_continuous,
    interpolate_zero_rate,
    price_fixed_rate_bond_from_curve,
)


def test_interpolated_rate_sits_between_adjacent_nodes():
    maturities = [1.0, 2.0, 5.0, 10.0, 30.0]
    rates = [4.0, 4.2, 4.5, 4.7, 5.0]

    interpolated = interpolate_zero_rate(maturities, rates, 3.0)

    assert 4.2 <= interpolated <= 4.5


def test_discount_factor_positive_and_below_one_for_positive_rate():
    discount_factor = discount_factor_continuous(rate_percent=5.0, maturity_years=2.0)

    assert 0.0 < discount_factor < 1.0


def test_discount_curve_contains_target_maturities():
    maturities = [1.0, 2.0, 5.0, 10.0, 30.0]
    rates = [4.0, 4.2, 4.5, 4.7, 5.0]

    curve = build_discount_curve(maturities, rates, [1.0, 3.0, 5.0])

    assert list(curve["maturity_years"]) == [1.0, 3.0, 5.0]
    assert "discount_factor_continuous" in curve.columns


def test_fixed_rate_bond_price_is_positive():
    maturities = [1.0, 2.0, 5.0, 10.0, 30.0]
    rates = [4.0, 4.2, 4.5, 4.7, 5.0]

    price = price_fixed_rate_bond_from_curve(
        maturities_years=maturities,
        yields_percent=rates,
        maturity_years=5.0,
        coupon_rate=0.045,
        face_value=100.0,
        frequency=2,
    )

    assert price > 0.0


def test_dv01_is_positive_for_plain_fixed_rate_bond():
    maturities = [1.0, 2.0, 5.0, 10.0, 30.0]
    rates = [4.0, 4.2, 4.5, 4.7, 5.0]

    dv01 = bond_dv01_from_curve(
        maturities_years=maturities,
        yields_percent=rates,
        maturity_years=5.0,
        coupon_rate=0.045,
        face_value=100.0,
        frequency=2,
    )

    assert dv01 > 0.0


def test_parallel_rate_shock_table_contains_base_and_shocks():
    maturities = [1.0, 2.0, 5.0, 10.0, 30.0]
    rates = [4.0, 4.2, 4.5, 4.7, 5.0]

    table = build_parallel_shock_table(
        maturities_years=maturities,
        yields_percent=rates,
        maturity_years=5.0,
        coupon_rate=0.045,
        shock_basis_points=[-100.0, 0.0, 100.0],
    )

    assert set(table["parallel_shift_bp"]) == {-100.0, 0.0, 100.0}
    assert len(table) == 3

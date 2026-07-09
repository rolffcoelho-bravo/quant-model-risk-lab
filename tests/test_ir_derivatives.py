import numpy as np

from qmrl.ir_derivatives import (
    discount_factors_from_zero_rates,
    parallel_shift_dv01,
    parallel_shift_table,
    par_swap_rate,
    payment_times,
    price_fixed_float_swap,
)


TENORS = [2.0, 5.0, 10.0]
RATES = [0.035, 0.038, 0.041]


def test_payment_times_are_semiannual_for_five_year_swap():
    times = payment_times(5.0, 2)
    assert len(times) == 10
    assert times[0] == 0.5
    assert times[-1] == 5.0


def test_discount_factors_are_positive_and_decreasing():
    times = payment_times(5.0, 2)
    dfs = discount_factors_from_zero_rates(times, TENORS, RATES)
    assert np.all(dfs > 0)
    assert np.all(np.diff(dfs) < 0)


def test_par_swap_rate_prices_swap_at_zero():
    times = payment_times(5.0, 2)
    dfs = discount_factors_from_zero_rates(times, TENORS, RATES)
    par = par_swap_rate(dfs, 2)
    result = price_fixed_float_swap(1_000_000, par, 5.0, 2, TENORS, RATES)
    assert abs(result.payer_swap_npv) < 1e-6
    assert abs(result.receiver_swap_npv) < 1e-6


def test_payer_and_receiver_values_are_symmetric():
    result = price_fixed_float_swap(1_000_000, 0.045, 5.0, 2, TENORS, RATES)
    assert abs(result.payer_swap_npv + result.receiver_swap_npv) < 1e-8


def test_dv01_has_opposite_signs_for_payer_and_receiver():
    result = price_fixed_float_swap(1_000_000, None, 5.0, 2, TENORS, RATES)
    dv01 = parallel_shift_dv01(1_000_000, result.par_rate + 0.0025, 5.0, 2, TENORS, RATES)
    assert dv01["payer_dv01"] > 0
    assert dv01["receiver_dv01"] < 0


def test_parallel_shift_table_contains_shock_results():
    result = price_fixed_float_swap(1_000_000, None, 5.0, 2, TENORS, RATES)
    table = parallel_shift_table(
        1_000_000,
        result.par_rate + 0.0025,
        5.0,
        2,
        TENORS,
        RATES,
        [-50, 0, 50],
    )
    assert list(table["curve_shift_bp"]) == [-50.0, 0.0, 50.0]
    assert {"payer_swap_npv", "receiver_swap_npv", "payer_npv_change"}.issubset(table.columns)

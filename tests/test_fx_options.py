from __future__ import annotations

from qmrl.fx_options import (
    forward_rate,
    garman_kohlhagen_price,
    put_call_parity_gap,
    spot_vol_surface,
)


def test_garman_kohlhagen_call_and_put_are_positive():
    call = garman_kohlhagen_price("call", 5.0, 5.1, 0.10, 0.04, 0.15, 1.0, 1_000_000)
    put = garman_kohlhagen_price("put", 5.0, 5.1, 0.10, 0.04, 0.15, 1.0, 1_000_000)

    assert call.premium_domestic > 0
    assert put.premium_domestic > 0
    assert call.vega > 0
    assert put.vega > 0


def test_fx_option_put_call_parity_gap_is_near_zero():
    spot = 5.0
    strike = 5.1
    rd = 0.10
    rf = 0.04
    vol = 0.15
    maturity = 1.0
    notional = 1_000_000

    call = garman_kohlhagen_price("call", spot, strike, rd, rf, vol, maturity, notional)
    put = garman_kohlhagen_price("put", spot, strike, rd, rf, vol, maturity, notional)

    gap = put_call_parity_gap(call.premium_domestic, put.premium_domestic, spot, strike, rd, rf, maturity, notional)
    assert abs(gap) < 1e-6


def test_fx_option_forward_rate_increases_with_domestic_rate():
    assert forward_rate(5.0, 0.12, 0.04, 1.0) > forward_rate(5.0, 0.08, 0.04, 1.0)


def test_spot_vol_surface_has_expected_grid():
    surface = spot_vol_surface(5.0, 5.1, 0.10, 0.04, 0.15, 1.0, 1_000_000)

    assert {-10.0, -5.0, 0.0, 5.0, 10.0}.issubset(set(surface["spot_shock_pct"]))
    assert {-0.05, 0.0, 0.05}.issubset(set(surface["vol_shock_abs"]))
    assert "put_call_parity_gap" in surface.columns

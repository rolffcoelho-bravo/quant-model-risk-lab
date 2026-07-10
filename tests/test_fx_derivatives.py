from __future__ import annotations

import pandas as pd

from qmrl.fx_derivatives import (
    fx_forward_rate,
    normalise_rate,
    price_fx_forward,
    spot_shock_table,
)


def test_rate_normalisation_accepts_percent_or_decimal():
    assert normalise_rate(13.25) == 0.1325
    assert normalise_rate(0.05) == 0.05


def test_fx_forward_rate_increases_when_domestic_rate_exceeds_foreign_rate():
    forward = fx_forward_rate(spot_rate=5.0, domestic_rate=0.10, foreign_rate=0.04, maturity_years=1.0)

    assert forward > 5.0


def test_fx_forward_long_value_sign_changes_with_contract_rate():
    low_contract = price_fx_forward(5.0, 0.10, 0.04, 1.0, 5.0, 1_000_000.0)
    high_contract = price_fx_forward(5.0, 0.10, 0.04, 1.0, 6.0, 1_000_000.0)

    assert low_contract.long_foreign_forward_value > high_contract.long_foreign_forward_value
    assert abs(low_contract.long_foreign_forward_value + low_contract.short_foreign_forward_value) < 1e-9


def test_fx_forward_shock_table_has_expected_shocks():
    table = spot_shock_table(5.0, 0.10, 0.04, 1.0, 5.1, 1_000_000.0)

    assert {-10.0, -5.0, 0.0, 5.0, 10.0}.issubset(set(table["spot_shock_pct"]))
    assert "long_foreign_forward_pnl" in table.columns

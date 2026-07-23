import math
import pytest

from qmrl.allocation import (
    ALLOCATION_BOUNDARY,
    AdjustmentVector,
    PortfolioAllocationState,
    SignedAdjustmentVector,
    TradeAllocationInput,
)
from tests.v1_4_gate5_helpers import additive_portfolio, trade


def test_adjustment_total_sign_identity():
    value = AdjustmentVector(cva=10, dva=2, fca=3, fba=1, mva=2, kva=4, wwr_uplift=1, stress_adjustment=-2)
    assert value.fva == 2
    assert value.total_adjustment == -19


def test_adjustment_rejects_negative_magnitude():
    with pytest.raises(ValueError):
        AdjustmentVector(cva=-1.0)


def test_signed_vector_allows_negative_changes():
    value = SignedAdjustmentVector(cva=-2.0, stress_adjustment=3.0)
    assert value.cva == -2.0
    assert value.total_adjustment == 5.0


def test_trade_currency_normalizes():
    item = trade("T1", currency="eur")
    assert item.currency == "EUR"


def test_portfolio_rejects_duplicate_trade_ids():
    item = trade("T1")
    with pytest.raises(ValueError):
        PortfolioAllocationState("P", (item, item))


def test_portfolio_insert_remove_replace():
    portfolio = additive_portfolio()
    inserted = trade("T4")
    changed = portfolio.with_trade(inserted)
    assert changed.trade("T4") == inserted
    reduced = changed.without("T4")
    assert reduced == portfolio
    replacement = trade("T1", scale=2.0)
    replaced = portfolio.replace("T1", replacement)
    assert replaced.trade("T1").scale == 2.0


def test_boundary_constant_is_explicit():
    assert ALLOCATION_BOUNDARY == "FULL_REVALUATION_PRIMARY_APPROXIMATION_DISCLOSED"

import pytest

from qmrl.allocation import insert_trade, leave_one_out, remove_trade, replace_trade
from tests.v1_4_gate5_helpers import additive_portfolio, evaluator, trade


def test_insert_trade_full_revaluation_reconciles():
    portfolio = additive_portfolio()
    result = insert_trade(portfolio, trade("T4"), evaluator())
    assert result.operation == "insert"
    assert result.full_revaluation is True
    assert result.increment == result.changed.subtract(result.base)


def test_remove_trade_full_revaluation_reconciles():
    portfolio = additive_portfolio()
    result = remove_trade(portfolio, "T1", evaluator())
    assert result.operation == "remove"
    assert result.increment.total_adjustment > 0.0


def test_replace_trade_full_revaluation_reconciles():
    portfolio = additive_portfolio()
    result = replace_trade(portfolio, "T1", trade("T1", scale=1.5), evaluator())
    assert result.operation == "replace"
    assert result.increment.total_adjustment < 0.0


def test_leave_one_out_covers_each_trade():
    portfolio = additive_portfolio()
    results = leave_one_out(portfolio, evaluator())
    assert set(results) == {"T1", "T2", "T3"}


def test_insert_duplicate_is_blocked():
    with pytest.raises(ValueError):
        insert_trade(additive_portfolio(), trade("T1"), evaluator())


def test_remove_unknown_is_blocked():
    with pytest.raises(KeyError):
        remove_trade(additive_portfolio(), "UNKNOWN", evaluator())


def test_removal_component_delta_matches():
    result = remove_trade(additive_portfolio(), "T2", evaluator())
    assert result.increment.cva == pytest.approx(-result.base.cva + result.changed.cva)
    assert result.increment.kva == pytest.approx(-result.base.kva + result.changed.kva)


def test_stress_increment_is_retained():
    result = insert_trade(
        additive_portfolio(),
        trade("T4", stress_multiplier=2.0),
        evaluator(),
    )
    assert result.increment.stress_adjustment < 0.0

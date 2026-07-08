import sys
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from qmrl.var_backtesting import count_var_exceptions, exception_rate, historical_var


def test_historical_var_is_positive_loss_number():
    returns = pd.Series([0.01, -0.02, 0.015, -0.03, 0.005])
    var_value = historical_var(returns, confidence_level=0.95)

    assert var_value > 0


def test_count_var_exceptions_returns_integer():
    returns = pd.Series([0.01, -0.02, 0.015, -0.05, 0.005])
    exceptions = count_var_exceptions(returns, var_value=0.03)

    assert isinstance(exceptions, int)
    assert exceptions == 1


def test_exception_rate_between_zero_and_one():
    returns = pd.Series([0.01, -0.02, 0.015, -0.05, 0.005])
    rate = exception_rate(returns, var_value=0.03)

    assert 0 <= rate <= 1

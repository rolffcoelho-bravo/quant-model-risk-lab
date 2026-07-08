"""Simple VaR backtesting utilities."""

from __future__ import annotations

import numpy as np
import pandas as pd


def historical_var(returns: pd.Series, confidence_level: float = 0.99) -> float:
    """Estimate historical Value-at-Risk as a positive loss number."""
    if returns.empty:
        raise ValueError("Returns cannot be empty.")
    if not 0 < confidence_level < 1:
        raise ValueError("confidence_level must be between 0 and 1.")

    clean_returns = returns.dropna()
    percentile = 100 * (1 - confidence_level)
    return float(-np.percentile(clean_returns, percentile))


def count_var_exceptions(returns: pd.Series, var_value: float) -> int:
    """Count observations where losses exceed VaR."""
    if var_value <= 0:
        raise ValueError("VaR must be a positive loss number.")
    clean_returns = returns.dropna()
    return int((clean_returns < -var_value).sum())


def exception_rate(returns: pd.Series, var_value: float) -> float:
    """Return the share of VaR exceptions in the sample."""
    clean_returns = returns.dropna()
    if clean_returns.empty:
        raise ValueError("Returns cannot be empty after dropping missing values.")
    return count_var_exceptions(clean_returns, var_value) / len(clean_returns)

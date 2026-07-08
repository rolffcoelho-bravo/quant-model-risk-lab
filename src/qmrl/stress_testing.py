"""Stress-testing utilities for simple portfolio-risk examples."""

from __future__ import annotations


def apply_return_shock(portfolio_value: float, shock_return: float) -> float:
    """Apply a return shock to a portfolio value."""
    if portfolio_value <= 0:
        raise ValueError("Portfolio value must be positive.")
    return portfolio_value * (1 + shock_return)


def stress_loss(portfolio_value: float, shock_return: float) -> float:
    """Return the loss produced by a negative return shock."""
    stressed_value = apply_return_shock(portfolio_value, shock_return)
    return portfolio_value - stressed_value

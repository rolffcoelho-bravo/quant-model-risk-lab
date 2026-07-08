"""Data-quality checks for financial model validation."""

from __future__ import annotations

import pandas as pd


def missing_value_report(data: pd.DataFrame) -> pd.DataFrame:
    """Return missing-value counts and percentages for each column."""
    if data.empty:
        raise ValueError("Input data cannot be empty.")

    report = pd.DataFrame({
        "missing_count": data.isna().sum(),
        "missing_percentage": data.isna().mean() * 100,
    })
    return report


def assert_required_columns(data: pd.DataFrame, required_columns: list[str]) -> None:
    """Raise an error if required columns are missing."""
    missing = [column for column in required_columns if column not in data.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")


def has_duplicate_index(data: pd.DataFrame) -> bool:
    """Return True if the DataFrame index has duplicate values."""
    return bool(data.index.duplicated().any())

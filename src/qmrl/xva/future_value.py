"""Pathwise trade and portfolio future-value simulation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np

from .scenario_paths import ScenarioCube


@dataclass(frozen=True)
class FXForwardTrade:
    """Foreign-currency notional settled in domestic currency."""

    trade_id: str
    notional_foreign: float
    strike: float
    maturity_time: float
    spot_factor: str
    domestic_rate_factor: str
    foreign_rate_factor: str

    def __post_init__(self) -> None:
        if not self.trade_id.strip():
            raise ValueError(
                "trade_id must not be empty."
            )

        if not np.isfinite(
            (
                self.notional_foreign,
                self.strike,
                self.maturity_time,
            )
        ).all():
            raise ValueError(
                "Trade parameters must be finite."
            )

        if self.strike <= 0.0:
            raise ValueError(
                "strike must be positive."
            )

        if self.maturity_time <= 0.0:
            raise ValueError(
                "maturity_time must be positive."
            )


@dataclass(frozen=True)
class ZeroCouponBondTrade:
    """Zero-coupon cash flow valued from a simulated short rate."""

    trade_id: str
    notional: float
    maturity_time: float
    rate_factor: str

    def __post_init__(self) -> None:
        if not self.trade_id.strip():
            raise ValueError(
                "trade_id must not be empty."
            )

        if not np.isfinite(
            (
                self.notional,
                self.maturity_time,
            )
        ).all():
            raise ValueError(
                "Trade parameters must be finite."
            )

        if self.maturity_time <= 0.0:
            raise ValueError(
                "maturity_time must be positive."
            )


TradeSpec = FXForwardTrade | ZeroCouponBondTrade


@dataclass(frozen=True)
class FutureValueCube:
    """Future values indexed by path, time, and trade."""

    times: np.ndarray
    trade_ids: tuple[str, ...]
    values: np.ndarray
    portfolio_values: np.ndarray

    def __post_init__(self) -> None:
        times = np.asarray(
            self.times,
            dtype=float,
        )
        values = np.asarray(
            self.values,
            dtype=float,
        )
        portfolio = np.asarray(
            self.portfolio_values,
            dtype=float,
        )

        if values.ndim != 3:
            raise ValueError(
                "values must have path, time, trade dimensions."
            )

        if values.shape[1] != times.size:
            raise ValueError(
                "Future-value time dimension mismatch."
            )

        if values.shape[2] != len(self.trade_ids):
            raise ValueError(
                "Future-value trade dimension mismatch."
            )

        if portfolio.shape != values.shape[:2]:
            raise ValueError(
                "portfolio_values shape mismatch."
            )

        if not np.isfinite(values).all():
            raise ValueError(
                "Future values must be finite."
            )

        if not np.allclose(
            portfolio,
            np.sum(values, axis=2),
        ):
            raise ValueError(
                "portfolio_values must equal trade aggregation."
            )

        immutable_times = times.copy()
        immutable_values = values.copy()
        immutable_portfolio = portfolio.copy()

        immutable_times.setflags(write=False)
        immutable_values.setflags(write=False)
        immutable_portfolio.setflags(write=False)

        object.__setattr__(
            self,
            "times",
            immutable_times,
        )
        object.__setattr__(
            self,
            "values",
            immutable_values,
        )
        object.__setattr__(
            self,
            "portfolio_values",
            immutable_portfolio,
        )


def _validate_maturity(
    cube: ScenarioCube,
    maturity_time: float,
) -> None:
    if maturity_time > cube.times[-1] + 1e-12:
        raise ValueError(
            "Trade maturity exceeds the scenario horizon."
        )


def value_fx_forward(
    cube: ScenarioCube,
    trade: FXForwardTrade,
) -> np.ndarray:
    """Value an FX forward across all scenario paths and times."""

    _validate_maturity(
        cube,
        trade.maturity_time,
    )

    spot = cube.factor_values(
        trade.spot_factor
    )
    domestic_rate = cube.factor_values(
        trade.domestic_rate_factor
    )
    foreign_rate = cube.factor_values(
        trade.foreign_rate_factor
    )

    remaining = np.maximum(
        trade.maturity_time
        - cube.times,
        0.0,
    )

    active = (
        cube.times
        <= trade.maturity_time + 1e-12
    )

    values = (
        trade.notional_foreign
        * (
            spot
            * np.exp(
                -foreign_rate
                * remaining[np.newaxis, :]
            )
            - trade.strike
            * np.exp(
                -domestic_rate
                * remaining[np.newaxis, :]
            )
        )
    )

    values[:, ~active] = 0.0
    return values


def value_zero_coupon_bond(
    cube: ScenarioCube,
    trade: ZeroCouponBondTrade,
) -> np.ndarray:
    """Value a zero-coupon cash flow using the simulated short rate."""

    _validate_maturity(
        cube,
        trade.maturity_time,
    )

    short_rate = cube.factor_values(
        trade.rate_factor
    )

    remaining = np.maximum(
        trade.maturity_time
        - cube.times,
        0.0,
    )

    active = (
        cube.times
        <= trade.maturity_time + 1e-12
    )

    values = (
        trade.notional
        * np.exp(
            -short_rate
            * remaining[np.newaxis, :]
        )
    )

    values[:, ~active] = 0.0
    return values


def value_portfolio(
    cube: ScenarioCube,
    trades: Iterable[TradeSpec],
) -> FutureValueCube:
    """Build the path, time, and trade future-value cube."""

    trade_list = list(trades)

    if not trade_list:
        raise ValueError(
            "At least one trade is required."
        )

    trade_ids = tuple(
        trade.trade_id
        for trade in trade_list
    )

    if len(trade_ids) != len(set(trade_ids)):
        raise ValueError(
            "trade_id values must be unique."
        )

    values = np.empty(
        (
            cube.num_paths,
            cube.num_times,
            len(trade_list),
        ),
        dtype=float,
    )

    for index, trade in enumerate(trade_list):
        if isinstance(trade, FXForwardTrade):
            values[:, :, index] = (
                value_fx_forward(
                    cube,
                    trade,
                )
            )
            continue

        if isinstance(
            trade,
            ZeroCouponBondTrade,
        ):
            values[:, :, index] = (
                value_zero_coupon_bond(
                    cube,
                    trade,
                )
            )
            continue

        raise TypeError(
            f"Unsupported trade type: {type(trade)!r}"
        )

    return FutureValueCube(
        times=cube.times,
        trade_ids=trade_ids,
        values=values,
        portfolio_values=np.sum(
            values,
            axis=2,
        ),
    )

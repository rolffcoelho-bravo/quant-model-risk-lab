"""Pathwise netting, collateral, and exposure integration for XVA Gate 3."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
import hashlib
import json
from typing import Mapping, Sequence

import numpy as np

from .collateral import (
    CollateralAgreement,
    simulate_collateral_path,
)
from .future_value import FutureValueCube
from .netting import NettingSet, validate_trade_membership


def _immutable_float_array(
    values: np.ndarray,
    *,
    name: str,
    ndim: int,
) -> np.ndarray:
    array = np.asarray(values, dtype=float)

    if array.ndim != ndim:
        raise ValueError(
            f"{name} must have {ndim} dimensions."
        )

    if not np.isfinite(array).all():
        raise ValueError(
            f"{name} must contain finite values."
        )

    result = array.copy()
    result.setflags(write=False)
    return result


def _immutable_bool_array(
    values: np.ndarray,
    *,
    name: str,
    ndim: int,
) -> np.ndarray:
    array = np.asarray(values, dtype=bool)

    if array.ndim != ndim:
        raise ValueError(
            f"{name} must have {ndim} dimensions."
        )

    result = array.copy()
    result.setflags(write=False)
    return result


def _validate_dates(
    dates: Sequence[date],
    expected_length: int,
) -> tuple[date, ...]:
    normalized = tuple(dates)

    if len(normalized) != expected_length:
        raise ValueError(
            "dates must match the future-value time dimension."
        )

    if normalized != tuple(sorted(normalized)):
        raise ValueError("dates must be sorted.")

    if len(normalized) != len(set(normalized)):
        raise ValueError("dates must be unique.")

    return normalized


@dataclass(frozen=True)
class PathwiseNettingCube:
    """Future clean values organized by legal netting set."""

    times: np.ndarray
    dates: tuple[date, ...]
    netting_set_ids: tuple[str, ...]
    counterparty_ids: tuple[str, ...]
    collateral_agreement_ids: tuple[str | None, ...]
    netting_eligible: np.ndarray
    trade_counts: np.ndarray
    clean_values: np.ndarray
    gross_positive_values: np.ndarray
    gross_negative_values: np.ndarray

    def __post_init__(self) -> None:
        times = _immutable_float_array(
            self.times,
            name="times",
            ndim=1,
        )

        if times.size == 0:
            raise ValueError(
                "times must not be empty."
            )

        if not np.isclose(times[0], 0.0):
            raise ValueError(
                "times must start at zero."
            )

        if times.size > 1 and np.any(
            np.diff(times) <= 0.0
        ):
            raise ValueError(
                "times must be strictly increasing."
            )

        dates = _validate_dates(
            self.dates,
            times.size,
        )

        num_sets = len(self.netting_set_ids)

        if num_sets == 0:
            raise ValueError(
                "At least one netting set is required."
            )

        if len(set(self.netting_set_ids)) != num_sets:
            raise ValueError(
                "netting_set_ids must be unique."
            )

        if len(self.counterparty_ids) != num_sets:
            raise ValueError(
                "counterparty_ids length mismatch."
            )

        if len(self.collateral_agreement_ids) != num_sets:
            raise ValueError(
                "collateral_agreement_ids length mismatch."
            )

        eligible = _immutable_bool_array(
            self.netting_eligible,
            name="netting_eligible",
            ndim=1,
        )

        counts = np.asarray(
            self.trade_counts,
            dtype=int,
        )

        if counts.ndim != 1:
            raise ValueError(
                "trade_counts must be one-dimensional."
            )

        if counts.size != num_sets:
            raise ValueError(
                "trade_counts length mismatch."
            )

        if np.any(counts <= 0):
            raise ValueError(
                "trade_counts must be positive."
            )

        immutable_counts = counts.copy()
        immutable_counts.setflags(write=False)

        clean = _immutable_float_array(
            self.clean_values,
            name="clean_values",
            ndim=3,
        )

        gross_positive = _immutable_float_array(
            self.gross_positive_values,
            name="gross_positive_values",
            ndim=3,
        )

        gross_negative = _immutable_float_array(
            self.gross_negative_values,
            name="gross_negative_values",
            ndim=3,
        )

        expected_shape = (
            clean.shape[0],
            times.size,
            num_sets,
        )

        for name, array in (
            ("clean_values", clean),
            (
                "gross_positive_values",
                gross_positive,
            ),
            (
                "gross_negative_values",
                gross_negative,
            ),
        ):
            if array.shape != expected_shape:
                raise ValueError(
                    f"{name} shape mismatch."
                )

        if np.any(gross_positive < 0.0):
            raise ValueError(
                "gross_positive_values must be non-negative."
            )

        if np.any(gross_negative < 0.0):
            raise ValueError(
                "gross_negative_values must be non-negative."
            )

        if not np.allclose(
            clean,
            gross_positive - gross_negative,
        ):
            raise ValueError(
                "Gross positive minus gross negative must "
                "reconcile to clean values."
            )

        object.__setattr__(self, "times", times)
        object.__setattr__(self, "dates", dates)
        object.__setattr__(
            self,
            "netting_eligible",
            eligible,
        )
        object.__setattr__(
            self,
            "trade_counts",
            immutable_counts,
        )
        object.__setattr__(
            self,
            "clean_values",
            clean,
        )
        object.__setattr__(
            self,
            "gross_positive_values",
            gross_positive,
        )
        object.__setattr__(
            self,
            "gross_negative_values",
            gross_negative,
        )

    @property
    def num_paths(self) -> int:
        return int(self.clean_values.shape[0])

    @property
    def num_times(self) -> int:
        return int(self.clean_values.shape[1])

    @property
    def num_netting_sets(self) -> int:
        return int(self.clean_values.shape[2])

    def netting_set_index(self, netting_set_id: str) -> int:
        try:
            return self.netting_set_ids.index(
                netting_set_id
            )
        except ValueError as exc:
            raise KeyError(
                f"Unknown netting set: {netting_set_id}"
            ) from exc


@dataclass(frozen=True)
class CollateralStateCube:
    """Collateral state by path, time, and netting set."""

    times: np.ndarray
    dates: tuple[date, ...]
    netting_set_ids: tuple[str, ...]
    face_balances: np.ndarray
    effective_balances: np.ndarray
    transfer_called: np.ndarray
    pending_face_balances: np.ndarray

    def __post_init__(self) -> None:
        times = _immutable_float_array(
            self.times,
            name="times",
            ndim=1,
        )

        dates = _validate_dates(
            self.dates,
            times.size,
        )

        arrays: dict[str, np.ndarray] = {}

        for name in (
            "face_balances",
            "effective_balances",
            "transfer_called",
            "pending_face_balances",
        ):
            arrays[name] = _immutable_float_array(
                getattr(self, name),
                name=name,
                ndim=3,
            )

        shape = arrays["effective_balances"].shape

        if shape[1] != times.size:
            raise ValueError(
                "Collateral time dimension mismatch."
            )

        if shape[2] != len(self.netting_set_ids):
            raise ValueError(
                "Collateral netting-set dimension mismatch."
            )

        for name, array in arrays.items():
            if array.shape != shape:
                raise ValueError(
                    f"{name} shape mismatch."
                )

        object.__setattr__(self, "times", times)
        object.__setattr__(self, "dates", dates)

        for name, array in arrays.items():
            object.__setattr__(self, name, array)


@dataclass(frozen=True)
class PathwiseExposureCube:
    """Integrated pathwise exposure before and after collateral."""

    times: np.ndarray
    dates: tuple[date, ...]
    netting_set_ids: tuple[str, ...]
    counterparty_ids: tuple[str, ...]
    clean_values: np.ndarray
    collateral_values: np.ndarray
    net_values: np.ndarray
    uncollateralized_positive: np.ndarray
    uncollateralized_negative: np.ndarray
    positive_exposure: np.ndarray
    negative_exposure: np.ndarray
    mpor_positive_exposure: np.ndarray
    mpor_negative_exposure: np.ndarray
    mpor_target_indices: np.ndarray

    def __post_init__(self) -> None:
        times = _immutable_float_array(
            self.times,
            name="times",
            ndim=1,
        )

        dates = _validate_dates(
            self.dates,
            times.size,
        )

        arrays: dict[str, np.ndarray] = {}

        for name in (
            "clean_values",
            "collateral_values",
            "net_values",
            "uncollateralized_positive",
            "uncollateralized_negative",
            "positive_exposure",
            "negative_exposure",
            "mpor_positive_exposure",
            "mpor_negative_exposure",
        ):
            arrays[name] = _immutable_float_array(
                getattr(self, name),
                name=name,
                ndim=3,
            )

        shape = arrays["clean_values"].shape

        if shape[1] != times.size:
            raise ValueError(
                "Exposure time dimension mismatch."
            )

        if shape[2] != len(self.netting_set_ids):
            raise ValueError(
                "Exposure netting-set dimension mismatch."
            )

        if len(self.counterparty_ids) != shape[2]:
            raise ValueError(
                "counterparty_ids length mismatch."
            )

        for name, array in arrays.items():
            if array.shape != shape:
                raise ValueError(
                    f"{name} shape mismatch."
                )

        if not np.allclose(
            arrays["net_values"],
            arrays["clean_values"]
            - arrays["collateral_values"],
        ):
            raise ValueError(
                "net_values must equal clean minus collateral."
            )

        if not np.allclose(
            arrays["net_values"],
            arrays["positive_exposure"]
            - arrays["negative_exposure"],
        ):
            raise ValueError(
                "Positive minus negative exposure must "
                "reconcile to net values."
            )

        target_indices = np.asarray(
            self.mpor_target_indices,
            dtype=int,
        )

        if target_indices.shape != (
            times.size,
            shape[2],
        ):
            raise ValueError(
                "mpor_target_indices shape mismatch."
            )

        if np.any(target_indices < 0):
            raise ValueError(
                "mpor_target_indices must be non-negative."
            )

        if np.any(target_indices >= times.size):
            raise ValueError(
                "mpor_target_indices exceed the time grid."
            )

        immutable_indices = target_indices.copy()
        immutable_indices.setflags(write=False)

        object.__setattr__(self, "times", times)
        object.__setattr__(self, "dates", dates)
        object.__setattr__(
            self,
            "mpor_target_indices",
            immutable_indices,
        )

        for name, array in arrays.items():
            object.__setattr__(self, name, array)


@dataclass(frozen=True)
class ExposureAggregation:
    """Netting-set, counterparty, and portfolio exposure profiles."""

    times: np.ndarray
    quantile: float
    netting_set_ids: tuple[str, ...]
    counterparty_ids: tuple[str, ...]
    expected_positive_by_netting_set: np.ndarray
    expected_negative_by_netting_set: np.ndarray
    pfe_by_netting_set: np.ndarray
    effective_epe_by_netting_set: np.ndarray
    mpor_expected_positive_by_netting_set: np.ndarray
    portfolio_expected_positive: np.ndarray
    portfolio_expected_negative: np.ndarray
    portfolio_pfe: np.ndarray
    portfolio_mpor_expected_positive: np.ndarray
    counterparty_expected_positive: np.ndarray
    counterparty_expected_negative: np.ndarray
    portfolio_epe: float
    portfolio_ene: float
    portfolio_peak_pfe: float

    def __post_init__(self) -> None:
        times = _immutable_float_array(
            self.times,
            name="times",
            ndim=1,
        )

        if not 0.0 < self.quantile < 1.0:
            raise ValueError(
                "quantile must be between zero and one."
            )

        expected_shape = (
            times.size,
            len(self.netting_set_ids),
        )

        for name in (
            "expected_positive_by_netting_set",
            "expected_negative_by_netting_set",
            "pfe_by_netting_set",
            "effective_epe_by_netting_set",
            "mpor_expected_positive_by_netting_set",
        ):
            array = _immutable_float_array(
                getattr(self, name),
                name=name,
                ndim=2,
            )

            if array.shape != expected_shape:
                raise ValueError(
                    f"{name} shape mismatch."
                )

            object.__setattr__(self, name, array)

        for name in (
            "portfolio_expected_positive",
            "portfolio_expected_negative",
            "portfolio_pfe",
            "portfolio_mpor_expected_positive",
        ):
            array = _immutable_float_array(
                getattr(self, name),
                name=name,
                ndim=1,
            )

            if array.size != times.size:
                raise ValueError(
                    f"{name} length mismatch."
                )

            object.__setattr__(self, name, array)

        cp_shape = (
            times.size,
            len(self.counterparty_ids),
        )

        for name in (
            "counterparty_expected_positive",
            "counterparty_expected_negative",
        ):
            array = _immutable_float_array(
                getattr(self, name),
                name=name,
                ndim=2,
            )

            if array.shape != cp_shape:
                raise ValueError(
                    f"{name} shape mismatch."
                )

            object.__setattr__(self, name, array)

        object.__setattr__(self, "times", times)


@dataclass(frozen=True)
class ExposureReconciliation:
    """Independent numerical reconciliation of Gate 3 integration."""

    trade_to_netting_max_abs_error: float
    clean_collateral_net_max_abs_error: float
    positive_negative_max_abs_error: float
    challenger_positive_max_abs_error: float
    challenger_negative_max_abs_error: float
    tolerance: float
    status: str


def allocate_future_values(
    future_values: FutureValueCube,
    netting_sets: Sequence[NettingSet],
    dates: Sequence[date],
) -> PathwiseNettingCube:
    """Allocate every future-value trade to exactly one netting set."""

    governed_sets = tuple(netting_sets)

    if not governed_sets:
        raise ValueError(
            "At least one netting set is required."
        )

    membership = validate_trade_membership(
        governed_sets
    )

    future_trade_ids = set(
        future_values.trade_ids
    )

    governed_trade_ids = set(membership)

    if future_trade_ids != governed_trade_ids:
        missing = sorted(
            future_trade_ids - governed_trade_ids
        )
        unexpected = sorted(
            governed_trade_ids - future_trade_ids
        )

        raise ValueError(
            "Trade allocation mismatch. "
            f"Unallocated={missing}; unknown={unexpected}."
        )

    normalized_dates = _validate_dates(
        dates,
        future_values.times.size,
    )

    trade_index = {
        trade_id: index
        for index, trade_id
        in enumerate(future_values.trade_ids)
    }

    shape = (
        future_values.values.shape[0],
        future_values.values.shape[1],
        len(governed_sets),
    )

    clean_values = np.zeros(
        shape,
        dtype=float,
    )

    gross_positive = np.zeros_like(
        clean_values
    )

    gross_negative = np.zeros_like(
        clean_values
    )

    for set_index, netting_set in enumerate(
        governed_sets
    ):
        indices = [
            trade_index[trade_id]
            for trade_id in netting_set.trade_ids
        ]

        trade_values = future_values.values[
            :,
            :,
            indices,
        ]

        clean_values[:, :, set_index] = np.sum(
            trade_values,
            axis=2,
        )

        gross_positive[:, :, set_index] = np.sum(
            np.maximum(trade_values, 0.0),
            axis=2,
        )

        gross_negative[:, :, set_index] = np.sum(
            np.maximum(-trade_values, 0.0),
            axis=2,
        )

    return PathwiseNettingCube(
        times=future_values.times,
        dates=normalized_dates,
        netting_set_ids=tuple(
            netting_set.netting_set_id
            for netting_set in governed_sets
        ),
        counterparty_ids=tuple(
            netting_set.counterparty_id
            for netting_set in governed_sets
        ),
        collateral_agreement_ids=tuple(
            netting_set.collateral_agreement_id
            for netting_set in governed_sets
        ),
        netting_eligible=np.asarray(
            [
                netting_set.netting_eligible
                for netting_set in governed_sets
            ],
            dtype=bool,
        ),
        trade_counts=np.asarray(
            [
                len(netting_set.trade_ids)
                for netting_set in governed_sets
            ],
            dtype=int,
        ),
        clean_values=clean_values,
        gross_positive_values=gross_positive,
        gross_negative_values=gross_negative,
    )


def simulate_pathwise_collateral(
    netting_cube: PathwiseNettingCube,
    agreements: Mapping[
        str,
        CollateralAgreement,
    ],
) -> CollateralStateCube:
    """Run the Gate 1 collateral state process on every path and set."""

    shape = netting_cube.clean_values.shape

    face = np.zeros(
        shape,
        dtype=float,
    )

    effective = np.zeros_like(face)
    called = np.zeros_like(face)
    pending = np.zeros_like(face)

    for set_index, agreement_id in enumerate(
        netting_cube.collateral_agreement_ids
    ):
        if agreement_id is None:
            continue

        if agreement_id not in agreements:
            raise KeyError(
                "Missing collateral agreement: "
                f"{agreement_id}"
            )

        if (
            not netting_cube.netting_eligible[
                set_index
            ]
            and netting_cube.trade_counts[
                set_index
            ]
            > 1
        ):
            raise ValueError(
                "Gate 3 does not collateralize a "
                "multi-trade noneligible set. Represent "
                "each trade as a separate exposure set."
            )

        agreement = agreements[
            agreement_id
        ]

        for path_index in range(
            netting_cube.num_paths
        ):
            points = simulate_collateral_path(
                netting_cube.dates,
                netting_cube.clean_values[
                    path_index,
                    :,
                    set_index,
                ],
                agreement,
            )

            face[
                path_index,
                :,
                set_index,
            ] = [
                point.face_balance
                for point in points
            ]

            effective[
                path_index,
                :,
                set_index,
            ] = [
                point.effective_balance
                for point in points
            ]

            called[
                path_index,
                :,
                set_index,
            ] = [
                point.transfer_called
                for point in points
            ]

            pending[
                path_index,
                :,
                set_index,
            ] = [
                point.pending_face_balance
                for point in points
            ]

    return CollateralStateCube(
        times=netting_cube.times,
        dates=netting_cube.dates,
        netting_set_ids=(
            netting_cube.netting_set_ids
        ),
        face_balances=face,
        effective_balances=effective,
        transfer_called=called,
        pending_face_balances=pending,
    )


def _mpor_target_indices(
    dates: tuple[date, ...],
    mpor_days: int,
) -> np.ndarray:
    targets = np.empty(
        len(dates),
        dtype=int,
    )

    for index, current_date in enumerate(dates):
        target_date = (
            current_date
            + timedelta(days=mpor_days)
        )

        target_index = len(dates) - 1

        for candidate_index in range(
            index,
            len(dates),
        ):
            if dates[candidate_index] >= target_date:
                target_index = candidate_index
                break

        targets[index] = target_index

    return targets


def build_pathwise_exposure_cube(
    netting_cube: PathwiseNettingCube,
    collateral_cube: CollateralStateCube,
    agreements: Mapping[
        str,
        CollateralAgreement,
    ],
) -> PathwiseExposureCube:
    """Integrate legal netting, collateral state, and pathwise exposure."""

    if (
        collateral_cube.netting_set_ids
        != netting_cube.netting_set_ids
    ):
        raise ValueError(
            "Netting-set order must match collateral."
        )

    if collateral_cube.dates != netting_cube.dates:
        raise ValueError(
            "Netting and collateral dates must match."
        )

    clean = np.asarray(
        netting_cube.clean_values,
        dtype=float,
    )

    collateral = np.asarray(
        collateral_cube.effective_balances,
        dtype=float,
    )

    net = clean - collateral

    uncollateralized_positive = np.where(
        netting_cube.netting_eligible[
            np.newaxis,
            np.newaxis,
            :,
        ],
        np.maximum(clean, 0.0),
        netting_cube.gross_positive_values,
    )

    uncollateralized_negative = np.where(
        netting_cube.netting_eligible[
            np.newaxis,
            np.newaxis,
            :,
        ],
        np.maximum(-clean, 0.0),
        netting_cube.gross_negative_values,
    )

    positive = np.empty_like(clean)
    negative = np.empty_like(clean)

    for set_index in range(
        netting_cube.num_netting_sets
    ):
        eligible = bool(
            netting_cube.netting_eligible[
                set_index
            ]
        )

        if (
            eligible
            or netting_cube.trade_counts[
                set_index
            ]
            == 1
        ):
            positive[:, :, set_index] = np.maximum(
                net[:, :, set_index],
                0.0,
            )

            negative[:, :, set_index] = np.maximum(
                -net[:, :, set_index],
                0.0,
            )
        else:
            if np.any(
                np.abs(
                    collateral[:, :, set_index]
                )
                > 1e-12
            ):
                raise ValueError(
                    "Collateral cannot be applied to a "
                    "multi-trade noneligible set."
                )

            positive[:, :, set_index] = (
                netting_cube.gross_positive_values[
                    :,
                    :,
                    set_index,
                ]
            )

            negative[:, :, set_index] = (
                netting_cube.gross_negative_values[
                    :,
                    :,
                    set_index,
                ]
            )

    target_indices = np.empty(
        (
            netting_cube.num_times,
            netting_cube.num_netting_sets,
        ),
        dtype=int,
    )

    mpor_positive = np.empty_like(clean)
    mpor_negative = np.empty_like(clean)

    for set_index, agreement_id in enumerate(
        netting_cube.collateral_agreement_ids
    ):
        if agreement_id is None:
            mpor_days = 0
        else:
            if agreement_id not in agreements:
                raise KeyError(
                    "Missing collateral agreement: "
                    f"{agreement_id}"
                )

            mpor_days = agreements[
                agreement_id
            ].margin_period_of_risk_days

        indices = _mpor_target_indices(
            netting_cube.dates,
            mpor_days,
        )

        target_indices[:, set_index] = indices

        if (
            netting_cube.netting_eligible[
                set_index
            ]
            or netting_cube.trade_counts[
                set_index
            ]
            == 1
        ):
            future_clean = clean[
                :,
                indices,
                set_index,
            ]

            mpor_net = (
                future_clean
                - collateral[
                    :,
                    :,
                    set_index,
                ]
            )

            mpor_positive[
                :,
                :,
                set_index,
            ] = np.maximum(
                mpor_net,
                0.0,
            )

            mpor_negative[
                :,
                :,
                set_index,
            ] = np.maximum(
                -mpor_net,
                0.0,
            )
        else:
            mpor_positive[
                :,
                :,
                set_index,
            ] = (
                netting_cube.gross_positive_values[
                    :,
                    indices,
                    set_index,
                ]
            )

            mpor_negative[
                :,
                :,
                set_index,
            ] = (
                netting_cube.gross_negative_values[
                    :,
                    indices,
                    set_index,
                ]
            )

    return PathwiseExposureCube(
        times=netting_cube.times,
        dates=netting_cube.dates,
        netting_set_ids=(
            netting_cube.netting_set_ids
        ),
        counterparty_ids=(
            netting_cube.counterparty_ids
        ),
        clean_values=clean,
        collateral_values=collateral,
        net_values=net,
        uncollateralized_positive=(
            uncollateralized_positive
        ),
        uncollateralized_negative=(
            uncollateralized_negative
        ),
        positive_exposure=positive,
        negative_exposure=negative,
        mpor_positive_exposure=mpor_positive,
        mpor_negative_exposure=mpor_negative,
        mpor_target_indices=target_indices,
    )


def _time_average(
    profile: np.ndarray,
    times: np.ndarray,
) -> float:
    if profile.size == 1:
        return float(profile[0])

    horizon = float(
        times[-1] - times[0]
    )

    if horizon <= 0.0:
        raise ValueError(
            "times must be strictly increasing."
        )

    return float(
        np.trapezoid(
            profile,
            times,
        )
        / horizon
    )


def aggregate_pathwise_exposure(
    exposure_cube: PathwiseExposureCube,
    *,
    quantile: float = 0.95,
) -> ExposureAggregation:
    """Aggregate pathwise exposure without cross-netting legal sets."""

    if not 0.0 < quantile < 1.0:
        raise ValueError(
            "quantile must be between zero and one."
        )

    positive = exposure_cube.positive_exposure
    negative = exposure_cube.negative_exposure
    mpor_positive = (
        exposure_cube.mpor_positive_exposure
    )

    expected_positive = np.mean(
        positive,
        axis=0,
    )

    expected_negative = np.mean(
        negative,
        axis=0,
    )

    pfe = np.quantile(
        positive,
        quantile,
        axis=0,
    )

    effective_epe = np.maximum.accumulate(
        expected_positive,
        axis=0,
    )

    mpor_expected_positive = np.mean(
        mpor_positive,
        axis=0,
    )

    portfolio_path_positive = np.sum(
        positive,
        axis=2,
    )

    portfolio_path_negative = np.sum(
        negative,
        axis=2,
    )

    portfolio_mpor_path_positive = np.sum(
        mpor_positive,
        axis=2,
    )

    portfolio_expected_positive = np.mean(
        portfolio_path_positive,
        axis=0,
    )

    portfolio_expected_negative = np.mean(
        portfolio_path_negative,
        axis=0,
    )

    portfolio_pfe = np.quantile(
        portfolio_path_positive,
        quantile,
        axis=0,
    )

    portfolio_mpor_expected_positive = np.mean(
        portfolio_mpor_path_positive,
        axis=0,
    )

    unique_counterparties = tuple(
        dict.fromkeys(
            exposure_cube.counterparty_ids
        )
    )

    cp_positive = np.zeros(
        (
            exposure_cube.times.size,
            len(unique_counterparties),
        ),
        dtype=float,
    )

    cp_negative = np.zeros_like(
        cp_positive
    )

    for cp_index, counterparty_id in enumerate(
        unique_counterparties
    ):
        set_indices = [
            index
            for index, value
            in enumerate(
                exposure_cube.counterparty_ids
            )
            if value == counterparty_id
        ]

        cp_positive[:, cp_index] = np.mean(
            np.sum(
                positive[
                    :,
                    :,
                    set_indices,
                ],
                axis=2,
            ),
            axis=0,
        )

        cp_negative[:, cp_index] = np.mean(
            np.sum(
                negative[
                    :,
                    :,
                    set_indices,
                ],
                axis=2,
            ),
            axis=0,
        )

    return ExposureAggregation(
        times=exposure_cube.times,
        quantile=float(quantile),
        netting_set_ids=(
            exposure_cube.netting_set_ids
        ),
        counterparty_ids=unique_counterparties,
        expected_positive_by_netting_set=(
            expected_positive
        ),
        expected_negative_by_netting_set=(
            expected_negative
        ),
        pfe_by_netting_set=pfe,
        effective_epe_by_netting_set=(
            effective_epe
        ),
        mpor_expected_positive_by_netting_set=(
            mpor_expected_positive
        ),
        portfolio_expected_positive=(
            portfolio_expected_positive
        ),
        portfolio_expected_negative=(
            portfolio_expected_negative
        ),
        portfolio_pfe=portfolio_pfe,
        portfolio_mpor_expected_positive=(
            portfolio_mpor_expected_positive
        ),
        counterparty_expected_positive=(
            cp_positive
        ),
        counterparty_expected_negative=(
            cp_negative
        ),
        portfolio_epe=_time_average(
            portfolio_expected_positive,
            exposure_cube.times,
        ),
        portfolio_ene=_time_average(
            portfolio_expected_negative,
            exposure_cube.times,
        ),
        portfolio_peak_pfe=float(
            np.max(portfolio_pfe)
        ),
    )


def reconcile_pathwise_exposure(
    future_values: FutureValueCube,
    netting_cube: PathwiseNettingCube,
    collateral_cube: CollateralStateCube,
    exposure_cube: PathwiseExposureCube,
    *,
    tolerance: float = 1e-10,
) -> ExposureReconciliation:
    """Reconcile trade, netting, collateral, and exposure layers."""

    if tolerance < 0.0:
        raise ValueError(
            "tolerance must be non-negative."
        )

    trade_sum = np.sum(
        future_values.values,
        axis=2,
    )

    netting_sum = np.sum(
        netting_cube.clean_values,
        axis=2,
    )

    trade_to_netting_error = float(
        np.max(
            np.abs(
                trade_sum - netting_sum
            )
        )
    )

    clean_collateral_net_error = float(
        np.max(
            np.abs(
                exposure_cube.net_values
                - (
                    netting_cube.clean_values
                    - collateral_cube.effective_balances
                )
            )
        )
    )

    positive_negative_error = float(
        np.max(
            np.abs(
                exposure_cube.net_values
                - (
                    exposure_cube.positive_exposure
                    - exposure_cube.negative_exposure
                )
            )
        )
    )

    challenger_positive = np.empty_like(
        exposure_cube.positive_exposure
    )

    challenger_negative = np.empty_like(
        exposure_cube.negative_exposure
    )

    for path_index in range(
        netting_cube.num_paths
    ):
        for time_index in range(
            netting_cube.num_times
        ):
            for set_index in range(
                netting_cube.num_netting_sets
            ):
                if (
                    netting_cube.netting_eligible[
                        set_index
                    ]
                    or netting_cube.trade_counts[
                        set_index
                    ]
                    == 1
                ):
                    value = (
                        netting_cube.clean_values[
                            path_index,
                            time_index,
                            set_index,
                        ]
                        - collateral_cube.effective_balances[
                            path_index,
                            time_index,
                            set_index,
                        ]
                    )

                    challenger_positive[
                        path_index,
                        time_index,
                        set_index,
                    ] = max(value, 0.0)

                    challenger_negative[
                        path_index,
                        time_index,
                        set_index,
                    ] = max(-value, 0.0)
                else:
                    challenger_positive[
                        path_index,
                        time_index,
                        set_index,
                    ] = (
                        netting_cube.gross_positive_values[
                            path_index,
                            time_index,
                            set_index,
                        ]
                    )

                    challenger_negative[
                        path_index,
                        time_index,
                        set_index,
                    ] = (
                        netting_cube.gross_negative_values[
                            path_index,
                            time_index,
                            set_index,
                        ]
                    )

    challenger_positive_error = float(
        np.max(
            np.abs(
                challenger_positive
                - exposure_cube.positive_exposure
            )
        )
    )

    challenger_negative_error = float(
        np.max(
            np.abs(
                challenger_negative
                - exposure_cube.negative_exposure
            )
        )
    )

    errors = (
        trade_to_netting_error,
        clean_collateral_net_error,
        positive_negative_error,
        challenger_positive_error,
        challenger_negative_error,
    )

    return ExposureReconciliation(
        trade_to_netting_max_abs_error=(
            trade_to_netting_error
        ),
        clean_collateral_net_max_abs_error=(
            clean_collateral_net_error
        ),
        positive_negative_max_abs_error=(
            positive_negative_error
        ),
        challenger_positive_max_abs_error=(
            challenger_positive_error
        ),
        challenger_negative_max_abs_error=(
            challenger_negative_error
        ),
        tolerance=float(tolerance),
        status=(
            "PASS"
            if max(errors) <= tolerance
            else "FAIL"
        ),
    )


def exposure_manifest(
    netting_cube: PathwiseNettingCube,
    collateral_cube: CollateralStateCube,
    exposure_cube: PathwiseExposureCube,
    aggregation: ExposureAggregation,
) -> dict[str, object]:
    """Create machine-readable, content-addressed Gate 3 evidence."""

    digest = hashlib.sha256()

    for array in (
        netting_cube.times,
        netting_cube.clean_values,
        collateral_cube.effective_balances,
        exposure_cube.positive_exposure,
        exposure_cube.negative_exposure,
        exposure_cube.mpor_positive_exposure,
        aggregation.portfolio_expected_positive,
        aggregation.portfolio_pfe,
    ):
        digest.update(
            np.ascontiguousarray(
                array,
                dtype=np.float64,
            ).tobytes()
        )

    metadata = {
        "netting_set_ids": (
            netting_cube.netting_set_ids
        ),
        "counterparty_ids": (
            netting_cube.counterparty_ids
        ),
        "dates": [
            value.isoformat()
            for value in netting_cube.dates
        ],
        "quantile": aggregation.quantile,
    }

    digest.update(
        json.dumps(
            metadata,
            sort_keys=True,
        ).encode("utf-8")
    )

    return {
        "schema_version": "1.0",
        "gate": "XVA_EXPOSURE_GATE_3",
        "num_paths": netting_cube.num_paths,
        "num_times": netting_cube.num_times,
        "num_netting_sets": (
            netting_cube.num_netting_sets
        ),
        "netting_set_ids": list(
            netting_cube.netting_set_ids
        ),
        "counterparty_ids": list(
            netting_cube.counterparty_ids
        ),
        "quantile": aggregation.quantile,
        "portfolio_epe": (
            aggregation.portfolio_epe
        ),
        "portfolio_ene": (
            aggregation.portfolio_ene
        ),
        "portfolio_peak_pfe": (
            aggregation.portfolio_peak_pfe
        ),
        "exposure_sha256": digest.hexdigest(),
    }

"""Correlated market-factor path simulation and reproducibility evidence."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any

import numpy as np

from .random_control import (
    RandomControl,
    generate_standard_normal,
)
from .risk_factors import (
    RiskFactorSet,
)


@dataclass(frozen=True)
class ScenarioCube:
    """Market-factor values indexed by path, time, and factor."""

    times: np.ndarray
    factor_names: tuple[str, ...]
    values: np.ndarray
    seed: int
    antithetic: bool
    model_version: str = "xva-scenario-gate2-v1"

    def __post_init__(self) -> None:
        times = np.asarray(
            self.times,
            dtype=float,
        )
        values = np.asarray(
            self.values,
            dtype=float,
        )

        if times.ndim != 1 or times.size < 2:
            raise ValueError(
                "times must contain at least two points."
            )

        if not np.isfinite(times).all():
            raise ValueError("times must be finite.")

        if not np.isclose(times[0], 0.0):
            raise ValueError(
                "The scenario time grid must start at zero."
            )

        if np.any(np.diff(times) <= 0.0):
            raise ValueError(
                "times must be strictly increasing."
            )

        if values.ndim != 3:
            raise ValueError(
                "values must have path, time, factor dimensions."
            )

        if values.shape[1] != times.size:
            raise ValueError(
                "Scenario time dimension does not match times."
            )

        if values.shape[2] != len(self.factor_names):
            raise ValueError(
                "Scenario factor dimension does not match names."
            )

        if values.shape[0] <= 0:
            raise ValueError(
                "Scenario cube requires at least one path."
            )

        if not np.isfinite(values).all():
            raise ValueError(
                "Scenario values must be finite."
            )

        if len(self.factor_names) != len(
            set(self.factor_names)
        ):
            raise ValueError(
                "factor_names must be unique."
            )

        immutable_times = times.copy()
        immutable_values = values.copy()
        immutable_times.setflags(write=False)
        immutable_values.setflags(write=False)

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

    @property
    def num_paths(self) -> int:
        return int(self.values.shape[0])

    @property
    def num_times(self) -> int:
        return int(self.values.shape[1])

    @property
    def num_factors(self) -> int:
        return int(self.values.shape[2])

    def factor_index(self, name: str) -> int:
        try:
            return self.factor_names.index(name)
        except ValueError as exc:
            raise KeyError(
                f"Unknown risk factor: {name}"
            ) from exc

    def factor_values(self, name: str) -> np.ndarray:
        return self.values[
            :,
            :,
            self.factor_index(name),
        ]


def _correlation_square_root(
    correlation: np.ndarray,
) -> np.ndarray:
    eigenvalues, eigenvectors = np.linalg.eigh(
        correlation
    )

    clipped = np.clip(
        eigenvalues,
        0.0,
        None,
    )

    return (
        eigenvectors
        @ np.diag(np.sqrt(clipped))
        @ eigenvectors.T
    )


def generate_scenario_cube(
    factor_set: RiskFactorSet,
    times: np.ndarray,
    *,
    num_paths: int,
    random_control: RandomControl,
) -> ScenarioCube:
    """Simulate correlated GBM, Vasicek, and deterministic factors."""

    time_array = np.asarray(
        times,
        dtype=float,
    )

    if time_array.ndim != 1 or time_array.size < 2:
        raise ValueError(
            "times must contain at least two points."
        )

    if not np.isfinite(time_array).all():
        raise ValueError("times must be finite.")

    if not np.isclose(time_array[0], 0.0):
        raise ValueError(
            "The scenario time grid must start at zero."
        )

    increments = np.diff(time_array)

    if np.any(increments <= 0.0):
        raise ValueError(
            "times must be strictly increasing."
        )

    num_factors = len(factor_set.factors)

    independent = generate_standard_normal(
        random_control,
        num_paths=num_paths,
        num_steps=increments.size,
        num_factors=num_factors,
    )

    square_root = _correlation_square_root(
        factor_set.correlation
    )

    shocks = np.einsum(
        "ptf,fg->ptg",
        independent,
        square_root,
    )

    values = np.empty(
        (
            num_paths,
            time_array.size,
            num_factors,
        ),
        dtype=float,
    )

    for factor_index, factor in enumerate(
        factor_set.factors
    ):
        values[
            :,
            0,
            factor_index,
        ] = factor.initial_value

    for step_index, delta_time in enumerate(
        increments,
        start=1,
    ):
        previous = values[
            :,
            step_index - 1,
            :,
        ]

        step_shocks = shocks[
            :,
            step_index - 1,
            :,
        ]

        for factor_index, factor in enumerate(
            factor_set.factors
        ):
            previous_value = previous[
                :,
                factor_index,
            ]
            z_value = step_shocks[
                :,
                factor_index,
            ]

            if factor.model == "gbm_fx":
                values[
                    :,
                    step_index,
                    factor_index,
                ] = previous_value * np.exp(
                    (
                        factor.drift
                        - 0.5
                        * factor.volatility
                        * factor.volatility
                    )
                    * delta_time
                    + factor.volatility
                    * np.sqrt(delta_time)
                    * z_value
                )
                continue

            if factor.model == "vasicek_rate":
                kappa = factor.mean_reversion

                if kappa > 1e-14:
                    decay = np.exp(
                        -kappa * delta_time
                    )
                    conditional_mean = (
                        factor.long_run_mean
                        + (
                            previous_value
                            - factor.long_run_mean
                        )
                        * decay
                    )
                    conditional_std = (
                        factor.volatility
                        * np.sqrt(
                            (
                                1.0
                                - np.exp(
                                    -2.0
                                    * kappa
                                    * delta_time
                                )
                            )
                            / (2.0 * kappa)
                        )
                    )
                else:
                    conditional_mean = (
                        previous_value
                        + factor.drift
                        * delta_time
                    )
                    conditional_std = (
                        factor.volatility
                        * np.sqrt(delta_time)
                    )

                values[
                    :,
                    step_index,
                    factor_index,
                ] = (
                    conditional_mean
                    + conditional_std
                    * z_value
                )
                continue

            if factor.model == "deterministic":
                values[
                    :,
                    step_index,
                    factor_index,
                ] = (
                    previous_value
                    + factor.drift
                    * delta_time
                )
                continue

            raise RuntimeError(
                f"Unsupported model: {factor.model}"
            )

    return ScenarioCube(
        times=time_array,
        factor_names=factor_set.names,
        values=values,
        seed=random_control.seed,
        antithetic=random_control.antithetic,
    )


def scenario_manifest(
    cube: ScenarioCube,
    factor_set: RiskFactorSet,
) -> dict[str, Any]:
    """Return deterministic metadata and a content hash."""

    digest = hashlib.sha256()

    digest.update(
        np.ascontiguousarray(
            cube.times,
            dtype=np.float64,
        ).tobytes()
    )

    digest.update(
        np.ascontiguousarray(
            cube.values,
            dtype=np.float64,
        ).tobytes()
    )

    digest.update(
        json.dumps(
            {
                "factor_names": cube.factor_names,
                "seed": cube.seed,
                "antithetic": cube.antithetic,
                "model_version": cube.model_version,
                "calibration_source": (
                    factor_set.calibration_source
                ),
                "calibration_as_of": (
                    factor_set.calibration_as_of
                ),
            },
            sort_keys=True,
        ).encode("utf-8")
    )

    return {
        "schema_version": "1.0",
        "model_version": cube.model_version,
        "seed": cube.seed,
        "antithetic": cube.antithetic,
        "num_paths": cube.num_paths,
        "num_times": cube.num_times,
        "factor_names": list(
            cube.factor_names
        ),
        "calibration_source": (
            factor_set.calibration_source
        ),
        "calibration_as_of": (
            factor_set.calibration_as_of
        ),
        "scenario_sha256": digest.hexdigest(),
    }

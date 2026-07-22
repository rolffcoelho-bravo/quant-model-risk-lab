"""Deterministic random-number controls for XVA scenario simulation."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class RandomControl:
    """Governed pseudo-random-number settings."""

    seed: int = 20260722
    antithetic: bool = True
    bit_generator: str = "PCG64"
    dtype: str = "float64"

    def __post_init__(self) -> None:
        if self.seed < 0:
            raise ValueError("seed must be non-negative.")

        if self.bit_generator != "PCG64":
            raise ValueError(
                "Gate 2 currently supports only PCG64."
            )

        if self.dtype != "float64":
            raise ValueError(
                "Gate 2 currently supports only float64."
            )


def generate_standard_normal(
    control: RandomControl,
    *,
    num_paths: int,
    num_steps: int,
    num_factors: int,
) -> np.ndarray:
    """Generate reproducible standard-normal draws."""

    for name, value in (
        ("num_paths", num_paths),
        ("num_steps", num_steps),
        ("num_factors", num_factors),
    ):
        if value <= 0:
            raise ValueError(f"{name} must be positive.")

    if control.antithetic and num_paths % 2 != 0:
        raise ValueError(
            "Antithetic simulation requires an even num_paths."
        )

    generator = np.random.Generator(
        np.random.PCG64(control.seed)
    )

    if control.antithetic:
        half = num_paths // 2
        base = generator.standard_normal(
            size=(half, num_steps, num_factors)
        )
        draws = np.concatenate(
            (base, -base),
            axis=0,
        )
    else:
        draws = generator.standard_normal(
            size=(num_paths, num_steps, num_factors)
        )

    return np.asarray(draws, dtype=np.float64)

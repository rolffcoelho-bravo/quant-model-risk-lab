from __future__ import annotations

import numpy as np
import pytest

from qmrl.xva import (
    RandomControl,
    generate_standard_normal,
)


def test_seeded_draws_are_reproducible() -> None:
    control = RandomControl(
        seed=123,
        antithetic=False,
    )

    first = generate_standard_normal(
        control,
        num_paths=10,
        num_steps=3,
        num_factors=2,
    )

    second = generate_standard_normal(
        control,
        num_paths=10,
        num_steps=3,
        num_factors=2,
    )

    assert np.array_equal(first, second)


def test_antithetic_draws_have_exact_zero_cross_path_mean() -> None:
    draws = generate_standard_normal(
        RandomControl(
            seed=17,
            antithetic=True,
        ),
        num_paths=20,
        num_steps=4,
        num_factors=3,
    )

    assert np.max(
        np.abs(
            np.mean(
                draws,
                axis=0,
            )
        )
    ) <= 1e-15


def test_antithetic_control_requires_even_paths() -> None:
    with pytest.raises(ValueError):
        generate_standard_normal(
            RandomControl(
                seed=1,
                antithetic=True,
            ),
            num_paths=5,
            num_steps=1,
            num_factors=1,
        )


def test_random_control_rejects_unsupported_generator() -> None:
    with pytest.raises(ValueError):
        RandomControl(
            bit_generator="MT19937"
        )

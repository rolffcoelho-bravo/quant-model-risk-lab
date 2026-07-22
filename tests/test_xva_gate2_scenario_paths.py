from __future__ import annotations

import numpy as np

from qmrl.xva import (
    RandomControl,
    RiskFactorSet,
    RiskFactorSpec,
    generate_scenario_cube,
    scenario_manifest,
)


def test_deterministic_factor_follows_locked_path() -> None:
    factor_set = RiskFactorSet(
        factors=(
            RiskFactorSpec(
                name="DET",
                factor_type="generic",
                model="deterministic",
                initial_value=1.0,
                drift=0.1,
            ),
        ),
        correlation=np.eye(1),
    )

    cube = generate_scenario_cube(
        factor_set,
        np.array(
            [0.0, 0.5, 1.0]
        ),
        num_paths=2,
        random_control=RandomControl(
            seed=1,
            antithetic=True,
        ),
    )

    assert cube.values.shape == (
        2,
        3,
        1,
    )

    assert cube.factor_values(
        "DET"
    )[0].tolist() == [
        1.0,
        1.05,
        1.10,
    ]


def test_correlated_factor_innovations_recover_target_sign() -> None:
    factor_set = RiskFactorSet(
        factors=(
            RiskFactorSpec(
                name="F1",
                factor_type="generic",
                model="vasicek_rate",
                initial_value=0.0,
                volatility=1.0,
            ),
            RiskFactorSpec(
                name="F2",
                factor_type="generic",
                model="vasicek_rate",
                initial_value=0.0,
                volatility=1.0,
            ),
        ),
        correlation=np.array(
            [
                [1.0, -0.6],
                [-0.6, 1.0],
            ]
        ),
    )

    cube = generate_scenario_cube(
        factor_set,
        np.array(
            [0.0, 1.0]
        ),
        num_paths=20000,
        random_control=RandomControl(
            seed=5,
            antithetic=True,
        ),
    )

    terminal = cube.values[
        :,
        -1,
        :,
    ]

    recovered = np.corrcoef(
        terminal.T
    )[0, 1]

    assert recovered < -0.57
    assert recovered > -0.63


def test_same_seed_produces_same_manifest_hash() -> None:
    factor_set = RiskFactorSet(
        factors=(
            RiskFactorSpec(
                name="FX",
                factor_type="fx_spot",
                model="gbm_fx",
                initial_value=1.2,
                drift=0.02,
                volatility=0.15,
            ),
        ),
        correlation=np.eye(1),
        calibration_as_of="2026-07-22",
    )

    control = RandomControl(
        seed=11,
        antithetic=True,
    )

    first = generate_scenario_cube(
        factor_set,
        np.array(
            [0.0, 0.5, 1.0]
        ),
        num_paths=100,
        random_control=control,
    )

    second = generate_scenario_cube(
        factor_set,
        np.array(
            [0.0, 0.5, 1.0]
        ),
        num_paths=100,
        random_control=control,
    )

    assert scenario_manifest(
        first,
        factor_set,
    )["scenario_sha256"] == scenario_manifest(
        second,
        factor_set,
    )["scenario_sha256"]


def test_scenario_cube_is_immutable() -> None:
    factor_set = RiskFactorSet(
        factors=(
            RiskFactorSpec(
                name="DET",
                factor_type="generic",
                model="deterministic",
                initial_value=1.0,
            ),
        ),
        correlation=np.eye(1),
    )

    cube = generate_scenario_cube(
        factor_set,
        np.array(
            [0.0, 1.0]
        ),
        num_paths=2,
        random_control=RandomControl(),
    )

    assert not cube.values.flags.writeable
    assert not cube.times.flags.writeable

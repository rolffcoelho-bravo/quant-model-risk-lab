from __future__ import annotations

import numpy as np

from qmrl.xva import (
    RandomControl,
    RiskFactorSet,
    RiskFactorSpec,
    compare_terminal_moments,
    convergence_diagnostics,
    gbm_moments,
    generate_scenario_cube,
    vasicek_moments,
)


def test_gbm_analytical_moments_are_positive() -> None:
    mean, variance = gbm_moments(
        initial_value=1.2,
        drift=0.03,
        volatility=0.2,
        horizon=1.0,
    )

    assert mean > 1.2
    assert variance > 0.0


def test_vasicek_mean_reverts_toward_long_run_level() -> None:
    mean, variance = vasicek_moments(
        initial_value=0.05,
        mean_reversion=0.5,
        long_run_mean=0.03,
        volatility=0.01,
        horizon=1.0,
    )

    assert 0.03 < mean < 0.05
    assert variance > 0.0


def test_simulated_gbm_mean_matches_analytical_challenger() -> None:
    factor_set = RiskFactorSet(
        factors=(
            RiskFactorSpec(
                name="FX",
                factor_type="fx_spot",
                model="gbm_fx",
                initial_value=1.2,
                drift=0.03,
                volatility=0.2,
            ),
        ),
        correlation=np.eye(1),
    )

    cube = generate_scenario_cube(
        factor_set,
        np.linspace(
            0.0,
            1.0,
            5,
        ),
        num_paths=40000,
        random_control=RandomControl(
            seed=37,
            antithetic=True,
        ),
    )

    check = compare_terminal_moments(
        cube,
        factor_set,
        "FX",
    )

    assert check.mean_relative_error < 0.0015
    assert check.variance_relative_error < 0.03


def test_convergence_diagnostics_identify_tight_zero_variance_estimator() -> None:
    diagnostics = convergence_diagnostics(
        np.ones(1000),
        sample_sizes=[
            10,
            100,
            1000,
        ],
        relative_tolerance=0.001,
    )

    assert diagnostics.stable
    assert diagnostics.final_estimate == 1.0
    assert diagnostics.final_standard_error == 0.0

from __future__ import annotations

import numpy as np
import pytest

from qmrl.xva import (
    RiskFactorSet,
    RiskFactorSpec,
    validate_correlation_matrix,
)


def _factor(name: str) -> RiskFactorSpec:
    return RiskFactorSpec(
        name=name,
        factor_type="short_rate",
        model="vasicek_rate",
        initial_value=0.03,
        volatility=0.01,
        mean_reversion=0.5,
        long_run_mean=0.025,
        currency="USD",
    )


def test_factor_set_preserves_order_and_correlation() -> None:
    factor_set = RiskFactorSet(
        factors=(
            _factor("R1"),
            _factor("R2"),
        ),
        correlation=np.array(
            [
                [1.0, 0.4],
                [0.4, 1.0],
            ]
        ),
    )

    assert factor_set.names == (
        "R1",
        "R2",
    )
    assert factor_set.correlation[0, 1] == 0.4
    assert not factor_set.correlation.flags.writeable


def test_non_psd_correlation_is_rejected() -> None:
    with pytest.raises(ValueError):
        validate_correlation_matrix(
            np.array(
                [
                    [1.0, 1.2],
                    [1.2, 1.0],
                ]
            )
        )


def test_duplicate_factor_names_are_rejected() -> None:
    with pytest.raises(ValueError):
        RiskFactorSet(
            factors=(
                _factor("R"),
                _factor("R"),
            ),
            correlation=np.eye(2),
        )


def test_gbm_requires_positive_initial_value() -> None:
    with pytest.raises(ValueError):
        RiskFactorSpec(
            name="FX",
            factor_type="fx_spot",
            model="gbm_fx",
            initial_value=0.0,
        )

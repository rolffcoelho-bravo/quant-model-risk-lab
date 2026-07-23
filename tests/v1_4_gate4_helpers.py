from __future__ import annotations

import numpy as np

from qmrl.capital import (
    BpsCurve,
    CapitalExposureInput,
    CapitalMarketState,
    CapitalPolicy,
    IntegrationRule,
)


def sample_input() -> CapitalExposureInput:
    return CapitalExposureInput(
        times=np.array([0.0, 1.0, 2.0, 3.0]),
        expected_exposure=np.array(
            [
                [0.0, 100.0, 80.0, 20.0],
                [0.0, 50.0, 40.0, 10.0],
            ]
        ),
        counterparty_ids=("CP_A", "CP_B"),
        netting_set_ids=("NS_A", "NS_B"),
        currencies=("USD", "EUR"),
        risk_weights=np.array([0.50, 0.75]),
        trade_ids=("T1", "T2", "T3"),
        trade_netting_set_indices=(0, 0, 1),
        trade_weights=np.array([0.60, 0.40, 1.00]),
    )


def sample_policy(**overrides: object) -> CapitalPolicy:
    values = dict(
        ead_multiplier=1.4,
        risk_weight=0.5,
        capital_ratio=0.08,
        maturity_multiplier=1.0,
        stress_multiplier=1.0,
        integration_rule=IntegrationRule.TRAPEZOID,
    )
    values.update(overrides)
    return CapitalPolicy(**values)


def sample_market() -> CapitalMarketState:
    return CapitalMarketState(
        times=np.array([0.0, 1.0, 2.0, 3.0]),
        discount_factors=np.array([1.0, 0.98, 0.95, 0.92]),
        counterparty_survival=np.array([1.0, 0.97, 0.93, 0.88]),
    )


def sample_hurdle(level: float = 1000.0) -> BpsCurve:
    return BpsCurve(
        np.array([0.0, 3.0]),
        np.array([level, level]),
    )

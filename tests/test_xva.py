from __future__ import annotations

import numpy as np

from qmrl.xva import (
    XVAAssumptions,
    compute_xva_from_clean_values,
    cumulative_default_probability,
    scenario_exposures,
)


def test_scenario_exposures_are_non_negative():
    values = np.array([-10.0, 0.0, 20.0])
    positive, negative = scenario_exposures(values)

    assert positive.tolist() == [0.0, 0.0, 20.0]
    assert negative.tolist() == [10.0, 0.0, 0.0]


def test_cumulative_default_probability_increases_with_spread():
    low = cumulative_default_probability(50.0, 0.40, 5.0)
    high = cumulative_default_probability(150.0, 0.40, 5.0)

    assert 0.0 < low < high < 1.0


def test_xva_components_are_transparent_and_finite():
    values = np.array([-100.0, -50.0, 0.0, 50.0, 100.0])
    result = compute_xva_from_clean_values(values, clean_value_at_base=0.0, discount_rate=0.04, assumptions=XVAAssumptions())

    assert result["expected_exposure"] >= 0.0
    assert result["expected_negative_exposure"] >= 0.0
    assert result["pfe_95"] >= result["expected_exposure"]
    assert result["cva"] >= 0.0
    assert result["dva"] >= 0.0
    assert result["fva"] >= 0.0
    assert result["xva_adjusted_value"] == result["xva_adjusted_value"]

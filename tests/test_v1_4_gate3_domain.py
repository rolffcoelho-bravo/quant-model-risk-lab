import pytest

from qmrl.margin import (
    InitialMarginProfile,
    MarginPolicy,
    ParametricMarginInput,
    PathwiseMarginInput,
    PROXY_LABEL,
    SurvivalProfile,
)


def test_margin_policy_accepts_approved_historical_proxy():
    policy = MarginPolicy(method="historical_simulation")
    assert policy.proxy_label == PROXY_LABEL


def test_margin_policy_rejects_certification_label_override():
    with pytest.raises(ValueError):
        MarginPolicy(method="parametric", proxy_label="SIMM_CERTIFIED")


def test_margin_policy_requires_segregated_posted_margin():
    with pytest.raises(ValueError):
        MarginPolicy(method="historical_simulation", posted_margin_segregated=False)


def test_pathwise_margin_input_rejects_dimension_mismatch():
    with pytest.raises(ValueError):
        PathwiseMarginInput("NS", "USD", (0.0, 1.0), ((1.0,),))


def test_parametric_input_rejects_asymmetric_covariance():
    with pytest.raises(ValueError):
        ParametricMarginInput(
            "NS", "USD", (0.0, 1.0), ((1.0, 2.0), (1.0, 2.0)),
            ((1.0, 0.2), (0.1, 1.0)),
        )


def test_initial_margin_profile_rejects_negative_margin():
    with pytest.raises(ValueError):
        InitialMarginProfile(
            "NS", "USD", (0.0, 1.0), (-1.0, 0.0), (0.0, 0.0),
            "historical_simulation", "hash", False,
        )


def test_survival_profile_requires_non_increasing_probabilities():
    with pytest.raises(ValueError):
        SurvivalProfile((0.0, 1.0), (0.9, 1.0), (1.0, 0.9))

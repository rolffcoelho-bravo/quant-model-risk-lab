import pytest

from qmrl.allocation import AllocationStatus, finite_difference_marginal
from tests.v1_4_gate5_helpers import additive_portfolio, evaluator, nonlinear_portfolio


def test_marginal_derivative_for_additive_trade():
    result = finite_difference_marginal(additive_portfolio(), "T1", evaluator())
    assert result.derivative.cva == pytest.approx(6.0, rel=1e-8)


def test_marginal_reports_refined_bump():
    result = finite_difference_marginal(
        additive_portfolio(), "T1", evaluator(), bump_fraction=1e-3
    )
    assert result.bump_fraction == pytest.approx(5e-4)


def test_marginal_convergence_is_small_for_additive_portfolio():
    result = finite_difference_marginal(additive_portfolio(), "T2", evaluator())
    assert result.convergence_error < 1e-8


def test_marginal_full_revaluation_reference_is_present():
    result = finite_difference_marginal(additive_portfolio(), "T3", evaluator())
    assert result.full_revaluation_reference is not None
    assert result.approximation_error is not None


def test_marginal_can_skip_full_revaluation_comparison():
    result = finite_difference_marginal(
        additive_portfolio(),
        "T1",
        evaluator(),
        compare_full_revaluation=False,
    )
    assert result.full_revaluation_reference is None
    assert result.approximation_error is None


def test_invalid_bump_is_rejected():
    with pytest.raises(ValueError):
        finite_difference_marginal(additive_portfolio(), "T1", evaluator(), bump_fraction=0.6)


def test_nonlinear_marginal_discloses_status_and_error():
    result = finite_difference_marginal(
        nonlinear_portfolio(),
        "T1",
        evaluator(),
        approximation_tolerance=1e-12,
    )
    assert result.status in {AllocationStatus.REMEDIATE, AllocationStatus.PASS_WITH_MONITORING}
    assert result.approximation_error is not None

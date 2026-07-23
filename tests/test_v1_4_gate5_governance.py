import pytest

from qmrl.allocation import (
    ALLOCATION_BOUNDARY,
    AllocationStatus,
    euler_allocation,
    finite_difference_marginal,
)
from tests.v1_4_gate5_helpers import additive_portfolio, evaluator, nonlinear_portfolio


def test_approximation_boundary_is_retained():
    result = finite_difference_marginal(additive_portfolio(), "T1", evaluator())
    assert result.boundary == ALLOCATION_BOUNDARY


def test_nonlinear_euler_cannot_pass():
    result = euler_allocation(nonlinear_portfolio(), evaluator())
    assert result.status == AllocationStatus.INVALID


def test_full_revaluation_reference_is_required_by_default():
    result = finite_difference_marginal(additive_portfolio(), "T2", evaluator())
    assert result.full_revaluation_reference is not None

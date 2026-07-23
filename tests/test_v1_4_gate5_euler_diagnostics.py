import pytest

from qmrl.allocation import (
    AllocationStatus,
    concentration_hhi,
    detect_nonlinearity,
    euler_allocation,
    leave_one_out_allocation,
)
from tests.v1_4_gate5_helpers import additive_portfolio, evaluator, nonlinear_portfolio


def test_additive_portfolio_is_euler_valid():
    report = detect_nonlinearity(additive_portfolio(), evaluator())
    assert report.euler_valid is True
    assert report.reasons == ()


def test_nonlinear_portfolio_is_euler_invalid():
    report = detect_nonlinearity(nonlinear_portfolio(), evaluator())
    assert report.euler_valid is False
    assert "threshold" in report.reasons
    assert "minimum_transfer_amount" in report.reasons
    assert "concentration_addon" in report.reasons
    assert "collateral_regime_switch" in report.reasons


def test_euler_allocation_reconciles_with_residual():
    result = euler_allocation(additive_portfolio(), evaluator())
    assert result.status == AllocationStatus.PASS
    assert abs(result.residual.total_adjustment) < 1e-7


def test_euler_is_invalid_for_nonlinear_portfolio():
    result = euler_allocation(nonlinear_portfolio(), evaluator())
    assert result.status == AllocationStatus.INVALID


def test_leave_one_out_reports_residual_explicitly():
    result = leave_one_out_allocation(nonlinear_portfolio(), evaluator())
    assert result.method == "leave_one_out"
    assert result.residual is not None


def test_concentration_hhi_bounds():
    assert concentration_hhi({"A": 1.0, "B": 1.0}) == pytest.approx(0.5)
    assert concentration_hhi({"A": 2.0}) == pytest.approx(1.0)
    assert concentration_hhi({}) == 0.0


def test_force_monitoring_status():
    result = euler_allocation(additive_portfolio(), evaluator(), force_monitoring=True)
    assert result.status == AllocationStatus.PASS_WITH_MONITORING

"""Tests for quantitative FX-option monitoring and revalidation."""

from __future__ import annotations

from qmrl.fx_option_governance import (
    load_fx_option_governance_contract,
)
from qmrl.fx_option_monitoring import (
    FXOptionMonitoringSnapshot,
    evaluate_fx_option_monitoring,
)


def baseline() -> FXOptionMonitoringSnapshot:
    return FXOptionMonitoringSnapshot(
        spot_rate=5.0,
        realised_volatility=0.15,
        domestic_rate=0.14,
        foreign_rate=0.04,
        parity_relative_gap=0.0,
        call_delta=500_000.0,
        vega=1_900_000.0,
    )


def test_unchanged_snapshot_passes() -> None:
    contract = load_fx_option_governance_contract()

    result = evaluate_fx_option_monitoring(
        current=baseline(),
        baseline=baseline(),
        policy=contract.monitoring,
    )

    assert result.monitoring_status == "PASS"
    assert not result.revalidation_required
    assert result.alerts == ()


def test_spot_breach_requires_revalidation() -> None:
    contract = load_fx_option_governance_contract()
    reference = baseline()

    current = FXOptionMonitoringSnapshot(
        **{
            **reference.__dict__,
            "spot_rate": 5.30,
        }
    )

    result = evaluate_fx_option_monitoring(
        current=current,
        baseline=reference,
        policy=contract.monitoring,
    )

    assert result.revalidation_required

    assert (
        "SPOT_MOVE_THRESHOLD_BREACH"
        in result.alerts
    )


def test_volatility_and_rate_breaches_are_detected() -> None:
    contract = load_fx_option_governance_contract()
    reference = baseline()

    current = FXOptionMonitoringSnapshot(
        **{
            **reference.__dict__,
            "realised_volatility": 0.21,
            "domestic_rate": 0.16,
            "foreign_rate": 0.06,
        }
    )

    result = evaluate_fx_option_monitoring(
        current=current,
        baseline=reference,
        policy=contract.monitoring,
    )

    assert (
        "REALISED_VOLATILITY_THRESHOLD_BREACH"
        in result.alerts
    )

    assert (
        "DOMESTIC_RATE_THRESHOLD_BREACH"
        in result.alerts
    )

    assert (
        "FOREIGN_RATE_THRESHOLD_BREACH"
        in result.alerts
    )


def test_parity_and_sign_changes_are_detected() -> None:
    contract = load_fx_option_governance_contract()
    reference = baseline()

    current = FXOptionMonitoringSnapshot(
        **{
            **reference.__dict__,
            "parity_relative_gap": 0.000002,
            "call_delta": -500_000.0,
            "vega": -1_900_000.0,
        }
    )

    result = evaluate_fx_option_monitoring(
        current=current,
        baseline=reference,
        policy=contract.monitoring,
    )

    assert (
        "PARITY_RELATIVE_GAP_THRESHOLD_BREACH"
        in result.alerts
    )

    assert "CALL_DELTA_SIGN_CHANGE" in result.alerts
    assert "VEGA_SIGN_CHANGE" in result.alerts


def test_public_contract_cannot_grant_production_approval() -> None:
    contract = load_fx_option_governance_contract()

    assert not (
        contract.model_boundaries.production_approval
    )

    assert (
        contract.model_boundaries.market_quote_benchmark
        == "OPEN_NO_PUBLIC_QUOTE_DATA"
    )
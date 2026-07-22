from __future__ import annotations

from datetime import date
import numpy as np
import pytest

from qmrl.xva.credit_curve import CreditCurve
from qmrl.xva.pathwise_exposure import PathwiseExposureCube
from qmrl.xva.wrong_way_risk import WWRDependenceSpec, calculate_wwr_cva, pathwise_exposure_scores
from qmrl.xva.xva_integration import DiscountCurve


def _curve() -> CreditCurve:
    return CreditCurve(
        curve_id="CP1",
        obligor_id="CP1",
        role="counterparty",
        probability_measure="risk_neutral",
        currency="USD",
        as_of_date=date(2026, 1, 2),
        recovery_rate=0.4,
        node_times=np.array([0.5, 1.0, 2.0]),
        hazard_rates=np.array([0.2, 0.2, 0.2]),
        source_quote_spreads_bps=np.array([1200.0, 1200.0, 1200.0]),
        source_quote_types=("cds", "cds", "cds"),
    )


def _discount() -> DiscountCurve:
    return DiscountCurve(
        curve_id="USD",
        currency="USD",
        as_of_date=date(2026, 1, 2),
        times=np.array([0.0, 0.5, 1.0, 2.0]),
        discount_factors=np.exp(-0.02 * np.array([0.0, 0.5, 1.0, 2.0])),
    )


def _cube() -> PathwiseExposureCube:
    paths = 400
    times = np.array([0.0, 0.5, 1.0, 2.0])
    path_scale = np.linspace(0.1, 2.5, paths)[:, None]
    values = (path_scale * np.array([0.0, 30.0, 70.0, 100.0])[None, :])[:, :, None]
    zeros = np.zeros_like(values)
    return PathwiseExposureCube(
        times=times,
        dates=(date(2026, 1, 2), date(2026, 7, 2), date(2027, 1, 2), date(2028, 1, 2)),
        netting_set_ids=("NS1",),
        counterparty_ids=("CP1",),
        clean_values=values,
        collateral_values=zeros,
        net_values=values,
        uncollateralized_positive=values,
        uncollateralized_negative=zeros,
        positive_exposure=values,
        negative_exposure=zeros,
        mpor_positive_exposure=values,
        mpor_negative_exposure=zeros,
        mpor_target_indices=np.arange(times.size)[:, None],
    )


def _spec(rho: float, classification: str) -> WWRDependenceSpec:
    return WWRDependenceSpec(
        dependence_id="D1",
        netting_set_id="NS1",
        counterparty_id="CP1",
        market_factor_id="FX",
        classification=classification,
        channel="fx",
        correlation=rho,
        as_of_date=date(2026, 1, 2),
        calibration_source="TEST",
        rationale="Unit-test dependence.",
        approved=True,
    )


def test_exposure_scores_are_centered() -> None:
    scores = pathwise_exposure_scores(_cube())
    assert scores.shape == (400, 1)
    assert float(np.mean(scores)) == pytest.approx(0.0, abs=1e-12)


def test_independence_has_zero_uplift() -> None:
    result = calculate_wwr_cva(
        _cube(),
        counterparty_curves={"CP1": _curve()},
        discount_curve=_discount(),
        dependence_specs={"NS1": _spec(0.0, "independent")},
    )
    assert result.uplift == pytest.approx(0.0, abs=1e-10)


def test_positive_dependence_increases_cva() -> None:
    result = calculate_wwr_cva(
        _cube(),
        counterparty_curves={"CP1": _curve()},
        discount_curve=_discount(),
        dependence_specs={"NS1": _spec(0.65, "general_wrong_way")},
    )
    assert result.dependent_cva > result.independent_cva
    assert result.uplift_ratio > 0.0


def test_right_way_dependence_reduces_cva() -> None:
    result = calculate_wwr_cva(
        _cube(),
        counterparty_curves={"CP1": _curve()},
        discount_curve=_discount(),
        dependence_specs={"NS1": _spec(-0.65, "right_way")},
    )
    assert result.dependent_cva < result.independent_cva


def test_boundary_correlation_remains_finite() -> None:
    result = calculate_wwr_cva(
        _cube(),
        counterparty_curves={"CP1": _curve()},
        discount_curve=_discount(),
        dependence_specs={"NS1": _spec(0.99, "specific_wrong_way")},
    )
    assert np.isfinite(result.dependent_cva)
    assert 0.0 <= result.concentration_hhi <= 1.0

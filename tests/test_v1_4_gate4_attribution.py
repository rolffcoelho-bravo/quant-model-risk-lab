from __future__ import annotations

import numpy as np

from qmrl.capital import build_capital_attribution, build_capital_profile, calculate_kva, capital_concentration
from v1_4_gate4_helpers import sample_hurdle, sample_input, sample_market, sample_policy


def _results():
    profile = build_capital_profile(sample_input(), sample_policy())
    kva = calculate_kva(profile, sample_market(), sample_hurdle())
    return profile, kva, build_capital_attribution(profile, kva)


def test_netting_set_attribution_reconciles() -> None:
    _, kva, attribution = _results()
    assert np.isclose(sum(row["kva"] for row in attribution.netting_set), kva.total_kva)


def test_counterparty_attribution_reconciles() -> None:
    _, kva, attribution = _results()
    assert np.isclose(sum(row["kva"] for row in attribution.counterparty), kva.total_kva)


def test_currency_attribution_reconciles() -> None:
    _, kva, attribution = _results()
    assert np.isclose(sum(row["kva"] for row in attribution.currency), kva.total_kva)


def test_trade_attribution_reconciles() -> None:
    _, kva, attribution = _results()
    assert np.isclose(sum(row["kva"] for row in attribution.trade), kva.total_kva)


def test_time_bucket_attribution_reconciles() -> None:
    _, kva, attribution = _results()
    assert np.isclose(sum(row["kva"] for row in attribution.time_bucket), kva.total_kva)


def test_attribution_residual_is_zero() -> None:
    _, _, attribution = _results()
    assert abs(attribution.reconciliation_residual) <= 1e-12


def test_concentration_metrics_are_bounded() -> None:
    profile, kva, _ = _results()
    metrics = capital_concentration(profile, kva)
    assert 0.0 < metrics["hhi"] <= 1.0
    assert 0.0 < metrics["maximum_share"] <= 1.0

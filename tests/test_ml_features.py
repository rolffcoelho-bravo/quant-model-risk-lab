import numpy as np
import pandas as pd

from src.qmrl.ml_features import (
    build_model_risk_feature_panel,
    build_model_risk_signals,
    deterministic_kmeans,
    mahalanobis_distances,
    pca_reconstruction_errors,
    percentile_rank,
    shrinkage_covariance,
)


def test_percentile_rank_is_bounded():
    value = percentile_rank(pd.Series([1, 2, 3, 4]), 3)

    assert 0 <= value <= 100


def test_build_model_risk_feature_panel_creates_expected_columns():
    dates = pd.date_range("2024-01-01", periods=70, freq="D")
    curve = pd.DataFrame(
        {
            "date": dates,
            "DGS2": np.linspace(4.0, 4.2, 70),
            "DGS5": np.linspace(4.1, 4.3, 70),
            "DGS10": np.linspace(4.3, 4.5, 70),
            "DGS30": np.linspace(4.7, 4.9, 70),
        }
    )
    inflation = pd.DataFrame({"date": dates, "T10YIE": np.linspace(2.1, 2.3, 70)})

    panel = build_model_risk_feature_panel(curve=curve, inflation=inflation)

    assert "slope_2s10" in panel.columns
    assert "real_rate_proxy" in panel.columns
    assert "d_bei_bp" in panel.columns


def test_shrinkage_covariance_has_correct_shape():
    matrix = np.array([[0.0, 1.0], [1.0, 0.0], [0.5, 0.5], [1.5, -0.5]])
    cov = shrinkage_covariance(matrix)

    assert cov.shape == (2, 2)


def test_mahalanobis_distances_are_non_negative():
    matrix = np.array([[0.0, 1.0], [1.0, 0.0], [0.5, 0.5], [1.5, -0.5]])
    distances = mahalanobis_distances(matrix)

    assert (distances >= 0).all()


def test_pca_reconstruction_errors_are_non_negative():
    matrix = np.array([[0.0, 1.0, 2.0], [1.0, 0.0, 1.8], [0.5, 0.5, 1.9], [1.5, -0.5, 2.2]])
    errors = pca_reconstruction_errors(matrix)

    assert (errors >= 0).all()


def test_deterministic_kmeans_returns_labels():
    matrix = np.array([[0.0, 0.0], [0.1, 0.1], [3.0, 3.0], [3.1, 3.1], [-2.0, -2.0], [-2.1, -2.1]])
    labels, centers = deterministic_kmeans(matrix, n_clusters=3)

    assert len(labels) == len(matrix)
    assert centers.shape == (3, 2)


def test_build_model_risk_signals_returns_decision_state():
    dates = pd.date_range("2024-01-01", periods=180, freq="D")
    curve = pd.DataFrame(
        {
            "date": dates,
            "DGS2": np.linspace(4.0, 4.2, 180),
            "DGS5": np.linspace(4.1, 4.3, 180),
            "DGS10": np.linspace(4.3, 4.5, 180),
            "DGS30": np.linspace(4.7, 4.9, 180),
        }
    )
    inflation = pd.DataFrame({"date": dates, "T10YIE": np.linspace(2.1, 2.3, 180)})

    panel = build_model_risk_feature_panel(curve=curve, inflation=inflation)
    signals, score_table, selected_features = build_model_risk_signals(panel, lookback=120)

    assert not signals.empty
    assert not score_table.empty
    assert len(selected_features) >= 3
    assert "decision_state" in signals.columns

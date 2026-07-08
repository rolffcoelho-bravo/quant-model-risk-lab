"""ML feature construction for model-risk monitoring.

This module builds rates, FX and inflation monitoring features from the
repository official-data layer. The goal is model-risk monitoring, not market
forecasting.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


RATE_COLUMNS = ["DGS1", "DGS2", "DGS5", "DGS10", "DGS30"]


def percentile_rank(values: pd.Series, value: float) -> float:
    clean = values.dropna()
    if clean.empty:
        return float("nan")
    return float((clean <= value).mean() * 100.0)


def _read_date_csv(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    if "date" not in frame.columns:
        raise ValueError(f"{path} must contain a date column.")
    frame["date"] = pd.to_datetime(frame["date"])
    return frame.sort_values("date")


def load_official_feature_inputs(processed_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame | None]:
    curve_path = processed_dir / "usd_treasury_curve_nodes.csv"
    inflation_path = processed_dir / "breakeven_inflation_panel.csv"
    fx_path = processed_dir / "fx_daily_returns.csv"

    if not curve_path.exists():
        raise FileNotFoundError(curve_path)

    if not inflation_path.exists():
        raise FileNotFoundError(inflation_path)

    curve = _read_date_csv(curve_path)
    inflation = _read_date_csv(inflation_path)

    fx_returns = None
    if fx_path.exists():
        fx_returns = _read_date_csv(fx_path)

    return curve, inflation, fx_returns


def build_model_risk_feature_panel(
    curve: pd.DataFrame,
    inflation: pd.DataFrame,
    fx_returns: pd.DataFrame | None = None,
) -> pd.DataFrame:
    missing_curve = [col for col in ["date", "DGS2", "DGS5", "DGS10", "DGS30"] if col not in curve.columns]
    if missing_curve:
        raise ValueError(f"Curve panel missing required columns: {missing_curve}")

    if "T10YIE" not in inflation.columns:
        raise ValueError("Inflation panel must contain T10YIE.")

    panel = curve.merge(inflation[["date", "T10YIE"]], on="date", how="inner")
    panel = panel.sort_values("date").copy()

    panel["slope_2s10"] = panel["DGS10"] - panel["DGS2"]
    panel["slope_5s30"] = panel["DGS30"] - panel["DGS5"]
    panel["real_rate_proxy"] = panel["DGS10"] - panel["T10YIE"]

    panel["d_dgs10_bp"] = panel["DGS10"].diff() * 100.0
    panel["d_slope_2s10_bp"] = panel["slope_2s10"].diff() * 100.0
    panel["d_slope_5s30_bp"] = panel["slope_5s30"].diff() * 100.0
    panel["d_bei_bp"] = panel["T10YIE"].diff() * 100.0
    panel["d_real_rate_proxy_bp"] = panel["real_rate_proxy"].diff() * 100.0

    if fx_returns is not None and not fx_returns.empty:
        fx_numeric = fx_returns.select_dtypes(include=["number"]).copy()
        if not fx_numeric.empty:
            fx = fx_returns[["date"]].copy()
            fx["fx_mean_abs_return"] = fx_numeric.abs().mean(axis=1)
            fx["fx_max_abs_return"] = fx_numeric.abs().max(axis=1)
            panel = panel.merge(fx, on="date", how="left")

    return panel


def build_feature_panel_from_processed(processed_dir: Path) -> pd.DataFrame:
    curve, inflation, fx_returns = load_official_feature_inputs(processed_dir)
    return build_model_risk_feature_panel(curve=curve, inflation=inflation, fx_returns=fx_returns)


def select_monitoring_features(panel: pd.DataFrame, min_non_null: int = 120) -> list[str]:
    candidates = [
        "d_dgs10_bp",
        "d_slope_2s10_bp",
        "d_slope_5s30_bp",
        "d_bei_bp",
        "d_real_rate_proxy_bp",
        "real_rate_proxy",
        "fx_mean_abs_return",
        "fx_max_abs_return",
    ]

    selected = []
    for column in candidates:
        if column in panel.columns and panel[column].notna().sum() >= min_non_null:
            selected.append(column)

    if len(selected) < 3:
        fallback = [
            column
            for column in [
                "d_dgs10_bp",
                "d_slope_2s10_bp",
                "d_bei_bp",
                "real_rate_proxy",
            ]
            if column in panel.columns and panel[column].notna().sum() >= 60
        ]
        selected = fallback

    if len(selected) < 3:
        raise ValueError("Insufficient monitoring features available.")

    return selected


def standardize_matrix(frame: pd.DataFrame) -> tuple[np.ndarray, pd.Series, pd.Series]:
    mean = frame.mean(axis=0)
    std = frame.std(axis=0).replace(0.0, np.nan)
    std = std.fillna(1.0)

    matrix = ((frame - mean) / std).to_numpy(dtype=float)
    return matrix, mean, std


def rolling_zscore(frame: pd.DataFrame, window: int = 126) -> pd.DataFrame:
    mean = frame.rolling(window=window, min_periods=max(30, window // 3)).mean()
    std = frame.rolling(window=window, min_periods=max(30, window // 3)).std().replace(0.0, np.nan)
    return (frame - mean) / std


def shrinkage_covariance(matrix: np.ndarray, shrinkage: float = 0.20) -> np.ndarray:
    cov = np.cov(matrix, rowvar=False)
    if cov.ndim == 0:
        cov = np.array([[float(cov)]])

    target = np.diag(np.diag(cov))
    shrunk = (1.0 - shrinkage) * cov + shrinkage * target
    shrunk = shrunk + np.eye(shrunk.shape[0]) * 1e-6
    return shrunk


def mahalanobis_distances(matrix: np.ndarray, shrinkage: float = 0.20) -> np.ndarray:
    center = matrix.mean(axis=0)
    cov = shrinkage_covariance(matrix, shrinkage=shrinkage)
    inv_cov = np.linalg.pinv(cov)

    distances = []
    for row in matrix:
        diff = row - center
        distance = float(np.sqrt(max(diff @ inv_cov @ diff.T, 0.0)))
        distances.append(distance)

    return np.array(distances)


def pca_reconstruction_errors(matrix: np.ndarray, n_components: int = 2) -> np.ndarray:
    if matrix.shape[1] <= 1:
        return np.zeros(matrix.shape[0])

    components = max(1, min(n_components, matrix.shape[1] - 1))
    center = matrix.mean(axis=0)
    centered = matrix - center

    _, _, vt = np.linalg.svd(centered, full_matrices=False)
    loading = vt[:components].T
    reconstructed = centered @ loading @ loading.T
    residual = centered - reconstructed

    return np.sqrt(np.mean(residual**2, axis=1))


def deterministic_kmeans(matrix: np.ndarray, n_clusters: int = 3, max_iter: int = 60) -> tuple[np.ndarray, np.ndarray]:
    if matrix.shape[0] < n_clusters:
        labels = np.zeros(matrix.shape[0], dtype=int)
        centers = matrix.mean(axis=0, keepdims=True)
        return labels, centers

    norms = np.linalg.norm(matrix, axis=1)
    quantiles = np.linspace(0.15, 0.85, n_clusters)
    initial_indices = [
        int(np.argmin(np.abs(norms - np.quantile(norms, q))))
        for q in quantiles
    ]
    centers = matrix[initial_indices].copy()

    labels = np.zeros(matrix.shape[0], dtype=int)

    for _ in range(max_iter):
        distances = np.linalg.norm(matrix[:, None, :] - centers[None, :, :], axis=2)
        new_labels = np.argmin(distances, axis=1)

        new_centers = centers.copy()
        for cluster in range(n_clusters):
            mask = new_labels == cluster
            if mask.any():
                new_centers[cluster] = matrix[mask].mean(axis=0)

        if np.array_equal(new_labels, labels):
            centers = new_centers
            labels = new_labels
            break

        centers = new_centers
        labels = new_labels

    return labels, centers


def rank_regime_labels(labels: np.ndarray, centers: np.ndarray) -> dict[int, str]:
    center_norms = np.linalg.norm(centers, axis=1)
    order = np.argsort(center_norms)

    names = ["Normal input regime", "Watch input regime", "Stress input regime"]
    mapping = {}
    for rank, cluster in enumerate(order):
        mapping[int(cluster)] = names[min(rank, len(names) - 1)]

    return mapping


def build_model_risk_signals(
    feature_panel: pd.DataFrame,
    lookback: int = 252,
) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    selected_features = select_monitoring_features(feature_panel)
    clean = feature_panel[["date"] + selected_features].dropna().sort_values("date").copy()

    if len(clean) < 60:
        raise ValueError("Need at least 60 complete observations for ML monitoring.")

    window = clean.tail(min(lookback, len(clean))).copy()
    feature_frame = window[selected_features]

    zscores = rolling_zscore(clean[selected_features]).loc[window.index]
    latest_z = zscores.tail(1).iloc[0]
    latest_abs_z = latest_z.abs()
    max_abs_z_feature = str(latest_abs_z.idxmax())
    max_abs_z = float(latest_abs_z.max())

    matrix, _, _ = standardize_matrix(feature_frame)
    mahala = mahalanobis_distances(matrix)
    pca_error = pca_reconstruction_errors(matrix, n_components=2)

    labels, centers = deterministic_kmeans(matrix, n_clusters=3)
    regime_mapping = rank_regime_labels(labels, centers)
    regime_names = [regime_mapping[int(label)] for label in labels]

    latest_mahala = float(mahala[-1])
    latest_pca_error = float(pca_error[-1])
    latest_regime = regime_names[-1]

    mahala_percentile = percentile_rank(pd.Series(mahala), latest_mahala)
    pca_percentile = percentile_rank(pd.Series(pca_error), latest_pca_error)

    feature_percentiles = {
        f"{feature}_percentile": percentile_rank(feature_frame[feature], float(feature_frame[feature].iloc[-1]))
        for feature in selected_features
    }

    pressure_score = (
        0.45 * mahala_percentile
        + 0.35 * min(100.0, max_abs_z / 3.0 * 100.0)
        + 0.20 * pca_percentile
    )
    pressure_score = float(round(min(max(pressure_score, 0.0), 100.0), 1))

    flags = []
    if max_abs_z >= 3.0:
        flags.append(f"univariate z-score breach in {max_abs_z_feature}")

    if mahala_percentile >= 95.0:
        flags.append("multivariate Mahalanobis distance above 95th percentile")

    if pca_percentile >= 90.0:
        flags.append("PCA reconstruction error above 90th percentile")

    if "Stress" in latest_regime:
        flags.append("latest observation assigned to stress input regime")

    if pressure_score >= 70.0 or len(flags) >= 2:
        decision_state = "Enhanced model-risk review"
    elif pressure_score >= 45.0 or flags:
        decision_state = "ML monitoring watch"
    else:
        decision_state = "Standard monitoring"

    if not flags:
        flags = ["no major ML monitoring threshold breach"]

    score_table = window[["date"]].copy()
    score_table["mahalanobis_distance"] = mahala
    score_table["pca_reconstruction_error"] = pca_error
    score_table["kmeans_regime"] = regime_names
    score_table["max_abs_rolling_zscore"] = zscores.abs().max(axis=1).to_numpy()

    latest = {
        "date": window["date"].iloc[-1].date().isoformat(),
        "decision_state": decision_state,
        "ml_pressure_score": pressure_score,
        "selected_features": "; ".join(selected_features),
        "max_abs_zscore": max_abs_z,
        "max_abs_zscore_feature": max_abs_z_feature,
        "mahalanobis_distance": latest_mahala,
        "mahalanobis_percentile": mahala_percentile,
        "pca_reconstruction_error": latest_pca_error,
        "pca_error_percentile": pca_percentile,
        "kmeans_regime": latest_regime,
        "decision_flags": "; ".join(flags),
    }

    latest.update(feature_percentiles)

    signals = pd.DataFrame([latest])
    return signals, score_table, selected_features

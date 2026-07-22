"""Wrong-way-risk dependence and pathwise CVA controls for XVA Gate 6."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import hashlib
import json
import math
from typing import Mapping, Sequence

import numpy as np

from .credit_curve import CreditCurve
from .pathwise_exposure import PathwiseExposureCube
from .xva_integration import DiscountCurve


_CLASSIFICATIONS = {
    "independent",
    "general_wrong_way",
    "specific_wrong_way",
    "right_way",
}
_CHANNELS = {
    "systemic",
    "sector",
    "sovereign",
    "commodity",
    "fx",
    "rates",
    "idiosyncratic",
}


def _finite(value: float, name: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{name} must be finite.")
    return number


def _immutable(values: Sequence[float] | np.ndarray, *, name: str, ndim: int) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    if array.ndim != ndim:
        raise ValueError(f"{name} must have {ndim} dimensions.")
    if not np.isfinite(array).all():
        raise ValueError(f"{name} must contain finite values.")
    result = array.copy()
    result.setflags(write=False)
    return result


def _normal_cdf(values: np.ndarray) -> np.ndarray:
    vectorized = np.vectorize(
        lambda x: 0.5 * (1.0 + math.erf(float(x) / math.sqrt(2.0))),
        otypes=[float],
    )
    return vectorized(values)


def normal_ppf(probability: float) -> float:
    """Acklam inverse-normal approximation without a SciPy dependency."""

    p = _finite(probability, "probability")
    if not 0.0 < p < 1.0:
        raise ValueError("probability must be strictly between zero and one.")

    a = (
        -3.969683028665376e01,
        2.209460984245205e02,
        -2.759285104469687e02,
        1.383577518672690e02,
        -3.066479806614716e01,
        2.506628277459239e00,
    )
    b = (
        -5.447609879822406e01,
        1.615858368580409e02,
        -1.556989798598866e02,
        6.680131188771972e01,
        -1.328068155288572e01,
    )
    c = (
        -7.784894002430293e-03,
        -3.223964580411365e-01,
        -2.400758277161838e00,
        -2.549732539343734e00,
        4.374664141464968e00,
        2.938163982698783e00,
    )
    d = (
        7.784695709041462e-03,
        3.224671290700398e-01,
        2.445134137142996e00,
        3.754408661907416e00,
    )
    lower = 0.02425
    upper = 1.0 - lower

    if p < lower:
        q = math.sqrt(-2.0 * math.log(p))
        numerator = (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5])
        denominator = ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1.0)
        return numerator / denominator

    if p > upper:
        q = math.sqrt(-2.0 * math.log(1.0 - p))
        numerator = (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5])
        denominator = ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1.0)
        return -(numerator / denominator)

    q = p - 0.5
    r = q * q
    numerator = (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q
    denominator = (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1.0)
    return numerator / denominator


@dataclass(frozen=True)
class WWRDependenceSpec:
    """Governed market-credit dependence assumption."""

    dependence_id: str
    netting_set_id: str
    counterparty_id: str
    market_factor_id: str
    classification: str
    channel: str
    correlation: float
    as_of_date: date
    calibration_source: str
    rationale: str
    review_date: date | None = None
    human_review_required: bool = True
    approved: bool = False

    def __post_init__(self) -> None:
        for name in (
            "dependence_id",
            "netting_set_id",
            "counterparty_id",
            "market_factor_id",
            "calibration_source",
            "rationale",
        ):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} must not be empty.")

        if self.classification not in _CLASSIFICATIONS:
            raise ValueError("Unsupported WWR classification.")
        if self.channel not in _CHANNELS:
            raise ValueError("Unsupported stress channel.")

        rho = _finite(self.correlation, "correlation")
        if not -0.99 <= rho <= 0.99:
            raise ValueError("correlation must be within [-0.99, 0.99].")

        if self.classification == "independent" and not math.isclose(rho, 0.0, abs_tol=1e-14):
            raise ValueError("Independent classification requires zero correlation.")
        if self.classification in {"general_wrong_way", "specific_wrong_way"} and rho < 0.0:
            raise ValueError("Wrong-way-risk classification requires non-negative correlation.")
        if self.classification == "right_way" and rho > 0.0:
            raise ValueError("Right-way-risk classification requires non-positive correlation.")
        if self.classification == "specific_wrong_way" and not self.human_review_required:
            raise ValueError("Specific wrong-way risk requires human review.")
        if self.review_date is not None and self.review_date < self.as_of_date:
            raise ValueError("review_date must not precede as_of_date.")

        object.__setattr__(self, "correlation", rho)


@dataclass(frozen=True)
class WWRResult:
    """Independent and dependence-adjusted pathwise CVA attribution."""

    netting_set_ids: tuple[str, ...]
    counterparty_ids: tuple[str, ...]
    correlations: np.ndarray
    independent_cva_by_netting_set: np.ndarray
    dependent_cva_by_netting_set: np.ndarray
    uplift_by_netting_set: np.ndarray
    conditional_pd_mean_by_netting_set: np.ndarray
    tail_exposure_share_by_netting_set: np.ndarray
    independent_cva: float
    dependent_cva: float
    uplift: float
    uplift_ratio: float
    concentration_hhi: float

    def __post_init__(self) -> None:
        count = len(self.netting_set_ids)
        if count == 0 or len(self.counterparty_ids) != count:
            raise ValueError("WWR identifiers are inconsistent.")
        if len(set(self.netting_set_ids)) != count:
            raise ValueError("netting_set_ids must be unique.")

        for name in (
            "correlations",
            "independent_cva_by_netting_set",
            "dependent_cva_by_netting_set",
            "uplift_by_netting_set",
            "conditional_pd_mean_by_netting_set",
            "tail_exposure_share_by_netting_set",
        ):
            array = _immutable(getattr(self, name), name=name, ndim=1)
            if array.size != count:
                raise ValueError(f"{name} length mismatch.")
            object.__setattr__(self, name, array)

        for name in (
            "independent_cva",
            "dependent_cva",
            "uplift",
            "uplift_ratio",
            "concentration_hhi",
        ):
            _finite(getattr(self, name), name)


def pathwise_exposure_scores(
    exposure_cube: PathwiseExposureCube,
    *,
    use_mpor: bool = True,
) -> np.ndarray:
    """Standardize path-average positive exposure for each legal netting set."""

    source = (
        exposure_cube.mpor_positive_exposure
        if use_mpor
        else exposure_cube.positive_exposure
    )
    path_average = np.mean(source[:, 1:, :], axis=1)
    mean = np.mean(path_average, axis=0, keepdims=True)
    standard_deviation = np.std(path_average, axis=0, keepdims=True)
    safe = np.where(standard_deviation > 1e-14, standard_deviation, 1.0)
    scores = (path_average - mean) / safe
    scores[:, np.ravel(standard_deviation <= 1e-14)] = 0.0
    return scores


def gaussian_copula_conditional_cumulative_pd(
    cumulative_pd: Sequence[float] | np.ndarray,
    exposure_scores: Sequence[float] | np.ndarray,
    *,
    correlation: float,
) -> np.ndarray:
    """Return conditional cumulative PD under a one-factor Gaussian copula."""

    probabilities = np.asarray(cumulative_pd, dtype=float)
    scores = np.asarray(exposure_scores, dtype=float)
    rho = _finite(correlation, "correlation")

    if probabilities.ndim != 1 or scores.ndim != 1:
        raise ValueError("cumulative_pd and exposure_scores must be one-dimensional.")
    if np.any(probabilities < 0.0) or np.any(probabilities > 1.0):
        raise ValueError("cumulative_pd must remain within [0, 1].")
    if np.any(np.diff(probabilities) < -1e-14):
        raise ValueError("cumulative_pd must be non-decreasing.")
    if not np.isfinite(scores).all():
        raise ValueError("exposure_scores must be finite.")
    if not -0.99 <= rho <= 0.99:
        raise ValueError("correlation must be within [-0.99, 0.99].")

    if math.isclose(rho, 0.0, abs_tol=1e-15):
        return np.tile(probabilities[None, :], (scores.size, 1))

    clipped = np.clip(probabilities, 1e-12, 1.0 - 1e-12)
    thresholds = np.asarray([normal_ppf(float(value)) for value in clipped])
    denominator = math.sqrt(max(1.0 - rho * rho, 1e-12))
    arguments = (thresholds[None, :] + rho * scores[:, None]) / denominator
    conditional = _normal_cdf(arguments)
    conditional[:, probabilities <= 0.0] = 0.0
    conditional[:, probabilities >= 1.0] = 1.0
    return np.clip(conditional, 0.0, 1.0)


def gaussian_copula_default_uniforms(
    exposure_scores: Sequence[float] | np.ndarray,
    independent_normals: Sequence[float] | np.ndarray,
    *,
    correlation: float,
) -> np.ndarray:
    """Generate default uniforms coupled to exposure through a Gaussian copula."""

    scores = np.asarray(exposure_scores, dtype=float)
    independent = np.asarray(independent_normals, dtype=float)
    if scores.shape != independent.shape:
        raise ValueError("exposure_scores and independent_normals must have equal shape.")
    if scores.ndim not in {1, 2} or not np.isfinite(scores).all() or not np.isfinite(independent).all():
        raise ValueError("Gaussian-copula inputs must be finite one- or two-dimensional arrays.")
    rho = _finite(correlation, "correlation")
    if not -0.99 <= rho <= 0.99:
        raise ValueError("correlation must be within [-0.99, 0.99].")
    latent = rho * scores + math.sqrt(1.0 - rho * rho) * independent
    return 1.0 - _normal_cdf(latent)


def _tail_share(values: np.ndarray, tail_fraction: float = 0.05) -> float:
    positive = np.maximum(np.asarray(values, dtype=float), 0.0)
    total = float(np.sum(positive))
    if total <= 0.0:
        return 0.0
    count = max(1, int(math.ceil(positive.size * tail_fraction)))
    tail = np.partition(positive, positive.size - count)[-count:]
    return float(np.sum(tail) / total)


def calculate_wwr_cva(
    exposure_cube: PathwiseExposureCube,
    *,
    counterparty_curves: Mapping[str, CreditCurve],
    discount_curve: DiscountCurve,
    dependence_specs: Mapping[str, WWRDependenceSpec],
    own_curve: CreditCurve | None = None,
    use_mpor: bool = True,
) -> WWRResult:
    """Calculate independent and Gaussian-copula dependence-adjusted CVA."""

    times = np.asarray(exposure_cube.times, dtype=float)
    if times.size < 2:
        raise ValueError("At least two exposure times are required.")

    source = (
        exposure_cube.mpor_positive_exposure
        if use_mpor
        else exposure_cube.positive_exposure
    )
    scores = pathwise_exposure_scores(exposure_cube, use_mpor=use_mpor)
    ends = times[1:]
    discount = discount_curve.values(ends)
    own_survival = (
        own_curve.survival_probabilities(ends)
        if own_curve is not None
        else np.ones_like(ends)
    )

    number_of_sets = len(exposure_cube.netting_set_ids)
    independent = np.zeros(number_of_sets, dtype=float)
    dependent = np.zeros(number_of_sets, dtype=float)
    correlations = np.zeros(number_of_sets, dtype=float)
    conditional_pd_means = np.zeros(number_of_sets, dtype=float)
    tail_shares = np.zeros(number_of_sets, dtype=float)

    for set_index, (set_id, counterparty_id) in enumerate(
        zip(
            exposure_cube.netting_set_ids,
            exposure_cube.counterparty_ids,
            strict=True,
        )
    ):
        if set_id not in dependence_specs:
            raise ValueError(f"Missing dependence specification for {set_id}.")
        spec = dependence_specs[set_id]
        if spec.netting_set_id != set_id or spec.counterparty_id != counterparty_id:
            raise ValueError("Dependence specification identifier mismatch.")
        if counterparty_id not in counterparty_curves:
            raise ValueError(f"Missing credit curve for {counterparty_id}.")

        curve = counterparty_curves[counterparty_id]
        cumulative = np.asarray(
            [curve.cumulative_default_probability(float(value)) for value in ends],
            dtype=float,
        )
        base_marginal = np.diff(np.concatenate(([0.0], cumulative)))
        conditional_cumulative = gaussian_copula_conditional_cumulative_pd(
            cumulative,
            scores[:, set_index],
            correlation=spec.correlation,
        )
        conditional_marginal = np.diff(
            np.concatenate(
                (
                    np.zeros((conditional_cumulative.shape[0], 1)),
                    conditional_cumulative,
                ),
                axis=1,
            ),
            axis=1,
        )
        conditional_marginal = np.maximum(conditional_marginal, 0.0)
        path_exposure = source[:, 1:, set_index]

        independent[set_index] = float(
            np.sum(
                discount
                * np.mean(path_exposure, axis=0)
                * curve.loss_given_default
                * base_marginal
                * own_survival
            )
        )
        dependent[set_index] = float(
            np.sum(
                discount
                * np.mean(path_exposure * conditional_marginal, axis=0)
                * curve.loss_given_default
                * own_survival
            )
        )
        correlations[set_index] = spec.correlation
        conditional_pd_means[set_index] = float(np.mean(conditional_cumulative[:, -1]))
        tail_shares[set_index] = _tail_share(np.mean(path_exposure, axis=1))

    uplift_by_set = dependent - independent
    independent_total = float(np.sum(independent))
    dependent_total = float(np.sum(dependent))
    uplift = dependent_total - independent_total
    uplift_ratio = uplift / independent_total if independent_total > 0.0 else 0.0
    total_contribution = float(np.sum(dependent))
    if total_contribution > 0.0:
        shares = dependent / total_contribution
        concentration_hhi = float(np.sum(shares * shares))
    else:
        concentration_hhi = 0.0

    return WWRResult(
        netting_set_ids=exposure_cube.netting_set_ids,
        counterparty_ids=exposure_cube.counterparty_ids,
        correlations=correlations,
        independent_cva_by_netting_set=independent,
        dependent_cva_by_netting_set=dependent,
        uplift_by_netting_set=uplift_by_set,
        conditional_pd_mean_by_netting_set=conditional_pd_means,
        tail_exposure_share_by_netting_set=tail_shares,
        independent_cva=independent_total,
        dependent_cva=dependent_total,
        uplift=uplift,
        uplift_ratio=uplift_ratio,
        concentration_hhi=concentration_hhi,
    )


def wwr_manifest(
    exposure_cube: PathwiseExposureCube,
    result: WWRResult,
    dependence_specs: Mapping[str, WWRDependenceSpec],
) -> dict[str, object]:
    """Create deterministic content-addressed Gate 6 WWR evidence."""

    digest = hashlib.sha256()
    for values in (
        exposure_cube.times,
        exposure_cube.positive_exposure,
        exposure_cube.mpor_positive_exposure,
        result.correlations,
        result.independent_cva_by_netting_set,
        result.dependent_cva_by_netting_set,
    ):
        digest.update(np.ascontiguousarray(values, dtype=np.float64).tobytes())

    metadata = {
        set_id: {
            "classification": dependence_specs[set_id].classification,
            "channel": dependence_specs[set_id].channel,
            "correlation": dependence_specs[set_id].correlation,
            "source": dependence_specs[set_id].calibration_source,
            "approved": dependence_specs[set_id].approved,
        }
        for set_id in sorted(dependence_specs)
    }
    digest.update(json.dumps(metadata, sort_keys=True).encode("utf-8"))

    return {
        "schema_version": "1.0",
        "gate": "XVA_EXPOSURE_GATE_6",
        "model": "GAUSSIAN_COPULA_WWR",
        "num_paths": int(exposure_cube.positive_exposure.shape[0]),
        "num_netting_sets": len(result.netting_set_ids),
        "independent_cva": result.independent_cva,
        "dependent_cva": result.dependent_cva,
        "uplift": result.uplift,
        "uplift_ratio": result.uplift_ratio,
        "concentration_hhi": result.concentration_hhi,
        "sha256": digest.hexdigest(),
        "production_approval": False,
    }

"""Seed, path, grid, perturbation, and sensitivity-ranking stability diagnostics."""

from __future__ import annotations

import math
from statistics import mean
from typing import Mapping, Sequence

from .domain import GovernanceStatus, StabilityObservation


def classify_deviation(
    deviation: float,
    warning_threshold: float,
    block_threshold: float,
) -> GovernanceStatus:
    if warning_threshold < 0.0 or block_threshold < warning_threshold:
        raise ValueError("Invalid stability thresholds.")
    if deviation <= warning_threshold:
        return GovernanceStatus.PASS
    if deviation <= block_threshold:
        return GovernanceStatus.PASS_WITH_MONITORING
    return GovernanceStatus.BLOCK


def _relative(first: float, second: float) -> float:
    return abs(float(first) - float(second)) / max(abs(float(first)), abs(float(second)), 1.0e-15)


def seed_stability(
    estimates: Mapping[int, float],
    warning_threshold: float = 0.01,
    block_threshold: float = 0.05,
) -> StabilityObservation:
    if len(estimates) < 2:
        raise ValueError("Seed stability requires at least two estimates.")
    values = tuple(float(estimates[key]) for key in sorted(estimates))
    if any(not math.isfinite(value) for value in values):
        raise ValueError("Seed estimates must be finite.")
    baseline = mean(values)
    deviation = max(_relative(value, baseline) for value in values)
    return StabilityObservation(
        dimension="seed",
        baseline_value=baseline,
        challenged_value=max(values, key=lambda value: abs(value - baseline)),
        deviation=deviation,
        warning_threshold=warning_threshold,
        block_threshold=block_threshold,
        status=classify_deviation(deviation, warning_threshold, block_threshold),
        detail=f"{len(values)} deterministic seeds evaluated",
    )


def path_count_stability(
    estimates: Mapping[int, float],
    warning_threshold: float = 0.02,
    block_threshold: float = 0.10,
) -> StabilityObservation:
    if len(estimates) < 2 or any(int(key) <= 0 for key in estimates):
        raise ValueError("Path-count stability requires at least two positive path counts.")
    counts = sorted(estimates)
    baseline = float(estimates[counts[-1]])
    deviations = [_relative(float(estimates[count]), baseline) for count in counts[:-1]]
    deviation = max(deviations)
    challenged = float(estimates[counts[deviations.index(deviation)]])
    return StabilityObservation(
        dimension="path_count",
        baseline_value=baseline,
        challenged_value=challenged,
        deviation=deviation,
        warning_threshold=warning_threshold,
        block_threshold=block_threshold,
        status=classify_deviation(deviation, warning_threshold, block_threshold),
        detail=f"reference_paths={counts[-1]}",
    )


def time_grid_stability(
    estimates: Mapping[str, float],
    reference_grid: str,
    warning_threshold: float = 0.01,
    block_threshold: float = 0.05,
) -> StabilityObservation:
    if reference_grid not in estimates or len(estimates) < 2:
        raise ValueError("A named reference grid and at least one challenger grid are required.")
    baseline = float(estimates[reference_grid])
    challengers = [(name, float(value)) for name, value in estimates.items() if name != reference_grid]
    name, challenged = max(challengers, key=lambda item: _relative(item[1], baseline))
    deviation = _relative(challenged, baseline)
    return StabilityObservation(
        dimension="time_grid",
        baseline_value=baseline,
        challenged_value=challenged,
        deviation=deviation,
        warning_threshold=warning_threshold,
        block_threshold=block_threshold,
        status=classify_deviation(deviation, warning_threshold, block_threshold),
        detail=f"reference={reference_grid};worst={name}",
    )


def input_perturbation_stability(
    *,
    label: str,
    baseline: float,
    perturbed: float,
    expected_direction: str = "either",
    warning_threshold: float = 0.10,
    block_threshold: float = 0.30,
) -> StabilityObservation:
    if expected_direction not in {"increase", "decrease", "either"}:
        raise ValueError("Unsupported perturbation direction.")
    direction_failed = (
        expected_direction == "increase" and perturbed < baseline
    ) or (
        expected_direction == "decrease" and perturbed > baseline
    )
    deviation = _relative(perturbed, baseline)
    status = GovernanceStatus.BLOCK if direction_failed else classify_deviation(
        deviation, warning_threshold, block_threshold
    )
    return StabilityObservation(
        dimension=f"perturbation:{label}",
        baseline_value=baseline,
        challenged_value=perturbed,
        deviation=deviation,
        warning_threshold=warning_threshold,
        block_threshold=block_threshold,
        status=status,
        detail=f"expected_direction={expected_direction}",
    )


def _ranks(values: Mapping[str, float]) -> dict[str, float]:
    ordered = sorted(values.items(), key=lambda item: (-abs(float(item[1])), item[0]))
    return {name: float(index + 1) for index, (name, _) in enumerate(ordered)}


def sensitivity_ranking_stability(
    baseline: Mapping[str, float],
    challenged: Mapping[str, float],
    warning_threshold: float = 0.10,
    block_threshold: float = 0.35,
) -> StabilityObservation:
    if set(baseline) != set(challenged) or len(baseline) < 2:
        raise ValueError("Sensitivity rankings require matching keys and at least two factors.")
    first = _ranks(baseline)
    second = _ranks(challenged)
    n = len(first)
    squared = sum((first[key] - second[key]) ** 2 for key in first)
    correlation = 1.0 - 6.0 * squared / (n * (n * n - 1.0))
    correlation = max(-1.0, min(1.0, correlation))
    deviation = (1.0 - correlation) / 2.0
    return StabilityObservation(
        dimension="sensitivity_ranking",
        baseline_value=1.0,
        challenged_value=correlation,
        deviation=deviation,
        warning_threshold=warning_threshold,
        block_threshold=block_threshold,
        status=classify_deviation(deviation, warning_threshold, block_threshold),
        detail=f"factor_count={n}",
    )

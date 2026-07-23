"""Independent reconciliation for full, partial, cached, and parallel results."""

from __future__ import annotations

from dataclasses import fields, is_dataclass
import math
from typing import Any, Mapping

from .domain import ReconciliationReport


def _flatten(value: Any, prefix: str = "root") -> dict[str, Any]:
    if is_dataclass(value):
        result: dict[str, Any] = {}
        for field in fields(value):
            result.update(_flatten(getattr(value, field.name), f"{prefix}.{field.name}"))
        return result
    if isinstance(value, Mapping):
        result = {}
        for key in sorted(value, key=str):
            result.update(_flatten(value[key], f"{prefix}.{key}"))
        return result
    if isinstance(value, (tuple, list)):
        result = {}
        for index, item in enumerate(value):
            result.update(_flatten(item, f"{prefix}[{index}]"))
        return result
    return {prefix: value}


def reconcile_outputs(
    primary: Any,
    challenger: Any,
    *,
    tolerance: float = 1.0e-10,
) -> ReconciliationReport:
    if not math.isfinite(tolerance) or tolerance < 0.0:
        raise ValueError("tolerance must be finite and non-negative.")
    left = _flatten(primary)
    right = _flatten(challenger)
    paths = sorted(set(left) | set(right))
    mismatches: list[str] = []
    max_abs = 0.0
    max_rel = 0.0
    compared = 0
    for path in paths:
        if path not in left or path not in right:
            mismatches.append(path)
            continue
        a = left[path]
        b = right[path]
        if isinstance(a, bool) or isinstance(b, bool):
            if a != b:
                mismatches.append(path)
            continue
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            a_float = float(a)
            b_float = float(b)
            if not math.isfinite(a_float) or not math.isfinite(b_float):
                mismatches.append(path)
                continue
            absolute = abs(a_float - b_float)
            relative = absolute / max(abs(a_float), abs(b_float), 1.0)
            max_abs = max(max_abs, absolute)
            max_rel = max(max_rel, relative)
            compared += 1
            if absolute > tolerance and relative > tolerance:
                mismatches.append(path)
        elif a != b:
            mismatches.append(path)
    return ReconciliationReport(
        status="PASS" if not mismatches else "REMEDIATE",
        compared_values=compared,
        max_absolute_difference=max_abs,
        max_relative_difference=max_rel,
        tolerance=tolerance,
        mismatches=tuple(mismatches),
    )


def reconcile_output_hashes(
    primary: Mapping[str, str],
    challenger: Mapping[str, str],
) -> ReconciliationReport:
    return reconcile_outputs(dict(primary), dict(challenger), tolerance=0.0)

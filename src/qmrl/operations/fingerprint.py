"""Canonical fingerprints and deterministic cache keys."""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from enum import Enum
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping


def canonical_data(value: Any) -> Any:
    if is_dataclass(value):
        return {
            field.name: canonical_data(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, Enum):
        return canonical_data(value.value)
    if isinstance(value, Mapping):
        return {
            str(key): canonical_data(value[key])
            for key in sorted(value, key=lambda item: str(item))
        }
    if isinstance(value, (tuple, list)):
        return [canonical_data(item) for item in value]
    if isinstance(value, (set, frozenset)):
        normalized = [canonical_data(item) for item in value]
        return sorted(normalized, key=lambda item: json.dumps(item, sort_keys=True))
    if isinstance(value, Path):
        return value.as_posix()
    if hasattr(value, "tolist") and not isinstance(value, (str, bytes, bytearray)):
        return canonical_data(value.tolist())
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("Canonical fingerprints reject non-finite floats.")
        return 0.0 if value == 0.0 else value
    if isinstance(value, (str, int, bool)) or value is None:
        return value
    if isinstance(value, bytes):
        return value.hex()
    raise TypeError(f"Unsupported canonical value: {type(value).__name__}.")


def canonical_json(value: Any) -> str:
    return json.dumps(
        canonical_data(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def content_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def normalized_text_hash(content: str | bytes) -> str:
    data = content.encode("utf-8") if isinstance(content, str) else bytes(content)
    data = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(data).hexdigest()


def deterministic_cache_key(
    *,
    node_id: str,
    dependency_hashes: Mapping[str, str],
    external_input: Any,
    policy_hash: str,
    engine_version: str,
    seed: int,
    scope: str = "portfolio",
) -> str:
    return content_hash(
        {
            "node_id": node_id,
            "dependency_hashes": dependency_hashes,
            "external_input": external_input,
            "policy_hash": policy_hash,
            "engine_version": engine_version,
            "seed": int(seed),
            "scope": scope,
        }
    )


def deterministic_run_id(plan_hash: str, engine_version: str, seed: int) -> str:
    return f"run-{content_hash({'plan_hash': plan_hash, 'engine_version': engine_version, 'seed': int(seed)})[:20]}"

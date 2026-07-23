"""Content-addressed file cache with stale and corruption detection."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import Any, Mapping

from .fingerprint import canonical_data, canonical_json, content_hash


@dataclass(frozen=True)
class CacheLookup:
    status: str
    value: Any | None
    output_hash: str
    reason: str

    def __post_init__(self) -> None:
        if self.status not in {"HIT", "MISS", "STALE", "CORRUPT"}:
            raise ValueError("Unsupported cache lookup status.")


class FileCache:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        if len(key) != 64 or any(char not in "0123456789abcdef" for char in key):
            raise ValueError("Cache key must be a SHA-256 digest.")
        return self.root / key[:2] / f"{key}.json"

    def put(self, key: str, value: Any, metadata: Mapping[str, Any]) -> str:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        normalized_value = canonical_data(value)
        normalized_metadata = canonical_data(metadata)
        envelope = {
            "key": key,
            "value": normalized_value,
            "output_hash": content_hash(normalized_value),
            "metadata": normalized_metadata,
            "metadata_hash": content_hash(normalized_metadata),
        }
        temporary = path.with_suffix(".tmp")
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(canonical_json(envelope))
            handle.write("\n")
        os.replace(temporary, path)
        return envelope["output_hash"]

    def get(
        self,
        key: str,
        *,
        expected_metadata: Mapping[str, Any] | None = None,
    ) -> CacheLookup:
        path = self._path(key)
        if not path.exists():
            return CacheLookup("MISS", None, "", "entry_not_found")
        try:
            envelope = json.loads(path.read_text(encoding="utf-8"))
            if envelope.get("key") != key:
                return CacheLookup("CORRUPT", None, "", "key_mismatch")
            value = envelope["value"]
            metadata = envelope["metadata"]
            output_hash = content_hash(value)
            if output_hash != envelope.get("output_hash"):
                return CacheLookup("CORRUPT", None, "", "output_hash_mismatch")
            if content_hash(metadata) != envelope.get("metadata_hash"):
                return CacheLookup("CORRUPT", None, "", "metadata_hash_mismatch")
            if expected_metadata is not None:
                expected = canonical_data(expected_metadata)
                if metadata != expected:
                    return CacheLookup("STALE", None, output_hash, "metadata_mismatch")
            return CacheLookup("HIT", value, output_hash, "validated")
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
            return CacheLookup("CORRUPT", None, "", "unreadable_entry")

    def invalidate(self, keys: list[str] | tuple[str, ...]) -> int:
        removed = 0
        for key in keys:
            path = self._path(key)
            if path.exists():
                path.unlink()
                removed += 1
        return removed

    def keys(self) -> tuple[str, ...]:
        values = [
            path.stem
            for path in self.root.rglob("*.json")
            if len(path.stem) == 64
        ]
        return tuple(sorted(values))

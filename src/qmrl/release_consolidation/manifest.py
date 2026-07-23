"""Deterministic release-manifest helpers."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Iterable

from .domain import ReleaseArtifact


def normalized_bytes(path: str | Path) -> bytes:
    return Path(path).read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def normalized_sha256(path: str | Path) -> str:
    return hashlib.sha256(normalized_bytes(path)).hexdigest()


def artifact_category(path: str) -> str:
    if path.startswith("configs/"):
        return "contract"
    if path.startswith("docs/") or path.startswith("reports/") or path == "README.md":
        return "documentation"
    if path.startswith("data/"):
        return "evidence"
    if path.startswith("src/"):
        return "implementation"
    if path.startswith("tests/"):
        return "validation"
    return "metadata"


def build_artifacts(root: str | Path, paths: Iterable[str]) -> tuple[ReleaseArtifact, ...]:
    base = Path(root)
    values = tuple(sorted(set(paths)))
    if not values:
        raise ValueError("Release manifest requires at least one artifact.")
    artifacts = []
    for path in values:
        full = base / path
        if not full.is_file():
            raise FileNotFoundError(path)
        artifacts.append(ReleaseArtifact(path, normalized_sha256(full), artifact_category(path)))
    return tuple(artifacts)


def verify_artifacts(root: str | Path, artifacts: Iterable[ReleaseArtifact]) -> tuple[str, ...]:
    base = Path(root)
    failures = []
    for item in artifacts:
        full = base / item.path
        if not full.is_file() or normalized_sha256(full) != item.sha256:
            failures.append(item.path)
    return tuple(sorted(failures))

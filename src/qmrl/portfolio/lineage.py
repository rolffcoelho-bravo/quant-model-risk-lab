"""Deterministic portfolio and calculation lineage."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Mapping

from .domain import PortfolioSnapshot


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def canonical_mapping_hash(value: Mapping[str, Any]) -> str:
    return sha256_bytes(canonical_json_bytes(value))


def canonical_portfolio_hash(snapshot: PortfolioSnapshot) -> str:
    from .ingestion import portfolio_to_mapping

    return canonical_mapping_hash(portfolio_to_mapping(snapshot))


def deterministic_run_id(
    *,
    snapshot_hash: str,
    configuration_hash: str,
    model_version: str,
    valuation_date: str,
    random_seed: int,
) -> str:
    payload = {
        "snapshot_hash": snapshot_hash,
        "configuration_hash": configuration_hash,
        "model_version": model_version,
        "valuation_date": valuation_date,
        "random_seed": random_seed,
    }
    return "run_" + canonical_mapping_hash(payload)[:24]


@dataclass(frozen=True)
class CalculationRun:
    run_id: str
    valuation_date: str
    portfolio_snapshot_id: str
    model_version: str
    configuration_hash: str
    input_hash: str
    source_hash: str
    random_seed: int
    created_at_utc: str


@dataclass(frozen=True)
class PortfolioLineageManifest:
    schema_version: str
    run: CalculationRun
    counts: dict[str, int]
    hash_policy: dict[str, str]
    validation_status: str
    downstream_calculation_permitted: bool

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "run": {
                "run_id": self.run.run_id,
                "valuation_date": self.run.valuation_date,
                "portfolio_snapshot_id": self.run.portfolio_snapshot_id,
                "model_version": self.run.model_version,
                "configuration_hash": self.run.configuration_hash,
                "input_hash": self.run.input_hash,
                "source_hash": self.run.source_hash,
                "random_seed": self.run.random_seed,
                "created_at_utc": self.run.created_at_utc,
            },
            "counts": dict(sorted(self.counts.items())),
            "hash_policy": dict(sorted(self.hash_policy.items())),
            "validation_status": self.validation_status,
            "downstream_calculation_permitted": (
                self.downstream_calculation_permitted
            ),
        }


def build_lineage_manifest(
    snapshot: PortfolioSnapshot,
    *,
    configuration: Mapping[str, Any],
    model_version: str,
    random_seed: int,
    created_at_utc: str,
    source_hash: str = "",
    validation_status: str = "PASS",
) -> PortfolioLineageManifest:
    input_hash = canonical_portfolio_hash(snapshot)
    configuration_hash = canonical_mapping_hash(configuration)
    permitted = validation_status == "PASS"
    run = CalculationRun(
        run_id=deterministic_run_id(
            snapshot_hash=input_hash,
            configuration_hash=configuration_hash,
            model_version=model_version,
            valuation_date=snapshot.valuation_date,
            random_seed=random_seed,
        ),
        valuation_date=snapshot.valuation_date,
        portfolio_snapshot_id=snapshot.snapshot_id,
        model_version=model_version,
        configuration_hash=configuration_hash,
        input_hash=input_hash,
        source_hash=source_hash,
        random_seed=random_seed,
        created_at_utc=created_at_utc,
    )
    return PortfolioLineageManifest(
        schema_version="1.0",
        run=run,
        counts=snapshot.counts(),
        hash_policy={
            "algorithm": "sha256",
            "canonical_encoding": "UTF-8",
            "object_key_order": "lexicographic",
            "collection_order": "canonical identifier order",
        },
        validation_status=validation_status,
        downstream_calculation_permitted=permitted,
    )


def compare_lineage_manifests(
    left: PortfolioLineageManifest,
    right: PortfolioLineageManifest,
) -> dict[str, object]:
    fields = {
        "input_hash": (
            left.run.input_hash,
            right.run.input_hash,
        ),
        "configuration_hash": (
            left.run.configuration_hash,
            right.run.configuration_hash,
        ),
        "model_version": (
            left.run.model_version,
            right.run.model_version,
        ),
        "valuation_date": (
            left.run.valuation_date,
            right.run.valuation_date,
        ),
        "random_seed": (
            left.run.random_seed,
            right.run.random_seed,
        ),
    }
    differences = {
        key: {"left": values[0], "right": values[1]}
        for key, values in fields.items()
        if values[0] != values[1]
    }
    return {
        "identical_calculation_identity": not differences,
        "differences": differences,
    }

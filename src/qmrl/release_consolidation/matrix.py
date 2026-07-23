"""Gate-matrix construction and reconciliation."""

from __future__ import annotations

import hashlib
import json
from typing import Mapping

from .domain import GateEvidence

GATE_TARGETS = {
    0: "ARCHITECTURE_FROZEN",
    1: "PORTFOLIO_CONTRACTS_VALIDATED",
    2: "MULTI_CURRENCY_VALIDATED",
    3: "MVA_VALIDATED",
    4: "KVA_VALIDATED",
    5: "INCREMENTAL_ANALYTICS_VALIDATED",
    6: "OPERATIONAL_SCALE_VALIDATED",
    7: "RELEASE_CANDIDATE_VALIDATED",
    8: "RELEASED_WITH_MONITORING",
}


def build_gate_matrix(statuses: Mapping[int, str]) -> tuple[GateEvidence, ...]:
    if set(statuses) != set(GATE_TARGETS):
        raise ValueError("Release matrix must contain Gates 0 through 8 exactly once.")
    matrix = []
    for gate in range(9):
        status = str(statuses[gate])
        if status != GATE_TARGETS[gate]:
            raise ValueError(f"Gate {gate} status does not match the frozen target.")
        matrix.append(GateEvidence(gate, status, (f"gate-{gate}-manifest",)))
    return tuple(matrix)


def matrix_hash(matrix: tuple[GateEvidence, ...]) -> str:
    payload = [
        {"gate": item.gate, "status": item.status, "evidence_ids": item.evidence_ids}
        for item in matrix
    ]
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def matrix_summary(matrix: tuple[GateEvidence, ...]) -> dict[str, object]:
    if tuple(item.gate for item in matrix) != tuple(range(9)):
        raise ValueError("Gate matrix must be ordered from Gate 0 through Gate 8.")
    return {
        "gate_count": len(matrix),
        "all_targets_met": all(item.status == GATE_TARGETS[item.gate] for item in matrix),
        "release_candidate_validated": matrix[7].status == GATE_TARGETS[7],
        "release_status": matrix[8].status,
        "matrix_hash": matrix_hash(matrix),
    }

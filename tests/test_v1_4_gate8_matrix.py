from __future__ import annotations
import pytest
from qmrl.release_consolidation import GATE_TARGETS, build_gate_matrix, matrix_hash, matrix_summary

def test_gate_matrix_contains_nine_ordered_gates():
    matrix = build_gate_matrix(GATE_TARGETS)
    assert tuple(item.gate for item in matrix) == tuple(range(9))

def test_gate_matrix_rejects_missing_gate():
    values = dict(GATE_TARGETS); values.pop(8)
    with pytest.raises(ValueError, match="Gates 0 through 8"):
        build_gate_matrix(values)

def test_gate_matrix_rejects_wrong_status():
    values = dict(GATE_TARGETS); values[4] = "WRONG"
    with pytest.raises(ValueError, match="Gate 4"):
        build_gate_matrix(values)

def test_matrix_hash_is_deterministic():
    matrix = build_gate_matrix(GATE_TARGETS)
    assert matrix_hash(matrix) == matrix_hash(matrix)

def test_matrix_summary_confirms_release_candidate():
    summary = matrix_summary(build_gate_matrix(GATE_TARGETS))
    assert summary["release_candidate_validated"] is True

def test_matrix_summary_reports_release_status():
    summary = matrix_summary(build_gate_matrix(GATE_TARGETS))
    assert summary["release_status"] == "RELEASED_WITH_MONITORING"

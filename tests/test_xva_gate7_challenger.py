from __future__ import annotations

import pytest

from qmrl.xva import (
    ToleranceBand,
    challenger_evidence_hash,
    compare_component,
    independent_cva_challenger,
    independent_dva_challenger,
    independent_funding_challenger,
)


BAND = ToleranceBand(absolute=0.01, relative=0.001, hard_multiplier=5.0, materiality=1.0)


def test_challenger_soft_reconciliation_passes() -> None:
    result = compare_component("CVA", 100.0, 100.005, BAND)
    assert result.status == "PASS"


def test_material_hard_boundary_breach_blocks() -> None:
    result = compare_component("CVA", 100.0, 101.0, BAND)
    assert result.status == "BLOCK"
    assert result.material


def test_independent_cva_and_dva_challengers() -> None:
    cva = independent_cva_challenger([10.0, 20.0], [1.0, 0.9], [0.01, 0.02], 0.4)
    dva = independent_dva_challenger([5.0, 8.0], [1.0, 0.9], [0.02, 0.03], 0.4)
    assert cva == pytest.approx((10.0 * 0.01 + 20.0 * 0.9 * 0.02) * 0.6)
    assert dva == pytest.approx((5.0 * 0.02 + 8.0 * 0.9 * 0.03) * 0.6)


def test_independent_funding_challenger_reconciles_signs() -> None:
    fca, fba, fva = independent_funding_challenger(
        [0.0, 100.0, 80.0], [0.0, 20.0, 10.0], [1.0, 0.98, 0.95], [0.0, 0.5, 1.0], [0.0, 0.02, 0.02], [0.0, 0.01, 0.01]
    )
    assert fca > 0.0
    assert fba > 0.0
    assert fva == pytest.approx(fca - fba)


def test_challenger_evidence_hash_is_deterministic() -> None:
    result = compare_component("FVA", 5.0, 5.0, BAND)
    first = challenger_evidence_hash([result], {"seed": 7})
    second = challenger_evidence_hash([result], {"seed": 7})
    assert first == second
    assert len(first) == 64

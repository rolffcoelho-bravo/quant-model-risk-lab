from pathlib import Path

from qmrl.multicurrency import calculate_multicurrency_exposure
from qmrl.portfolio import validate_portfolio_snapshot
from v1_4_gate2_helpers import (
    curves,
    fx_market,
    policy,
    reference_snapshot,
    trade_values,
)


def test_gate1_snapshot_remains_valid():
    validation = validate_portfolio_snapshot(reference_snapshot())
    assert validation.is_valid


def test_gate2_consumes_canonical_gate1_snapshot():
    results = calculate_multicurrency_exposure(
        reference_snapshot(),
        trade_values(),
        {},
        fx_market(),
        curves(),
        policy(),
    )
    assert len(results) == 1
    assert results[0].netting_set_id == "NS-1"


def test_gate2_does_not_introduce_mva_or_kva():
    root = Path(__file__).resolve().parents[1]
    source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (root / "src" / "qmrl" / "multicurrency").glob("*.py")
    ).lower()
    assert "margin valuation adjustment" not in source
    assert "capital valuation adjustment" not in source

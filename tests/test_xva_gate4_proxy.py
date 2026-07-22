from __future__ import annotations

from datetime import date, timedelta

import pytest

from qmrl.xva import (
    CreditProxyCandidate,
    proxy_selection_to_quote,
    select_credit_proxy,
)


AS_OF = date(2026, 1, 2)


def candidate(
    candidate_id: str,
    level: str,
    spread: float,
    *,
    age_days: int = 0,
    basis: float = 0.0,
) -> CreditProxyCandidate:
    return CreditProxyCandidate(
        candidate_id=candidate_id,
        obligor_id="CP1",
        proxy_obligor_id=f"PROXY-{candidate_id}",
        level=level,
        tenor_years=5.0,
        spread_bps=spread,
        basis_adjustment_bps=basis,
        as_of_date=AS_OF - timedelta(days=age_days),
        source_id="PROXY-SOURCE",
    )


def select(candidates: list[CreditProxyCandidate]):
    return select_credit_proxy(
        candidates,
        as_of_date=AS_OF,
        max_age_days=5,
        required_tenor=5.0,
        expected_measure="risk_neutral",
        expected_currency="USD",
        expected_seniority="senior_unsecured",
    )


def test_direct_quote_has_priority_over_proxy_levels() -> None:
    result = select(
        [
            candidate("SECTOR", "sector", 140.0),
            candidate("DIRECT", "direct", 100.0),
            candidate("PARENT", "parent", 110.0),
        ]
    )

    assert result.selected_candidate_id == "DIRECT"
    assert result.human_review_required is False


def test_parent_selected_when_direct_quote_is_stale() -> None:
    result = select(
        [
            candidate("DIRECT", "direct", 100.0, age_days=10),
            candidate("PARENT", "parent", 100.0, basis=5.0),
            candidate("SECTOR", "sector", 140.0),
        ]
    )

    assert result.selected_candidate_id == "PARENT"
    assert result.adjusted_spread_bps == 105.0
    assert result.human_review_required is True
    assert any("DIRECT:stale" in item for item in result.rejected_candidates)


def test_no_eligible_proxy_fails_closed() -> None:
    with pytest.raises(ValueError, match="No eligible"):
        select([candidate("STALE", "sector", 140.0, age_days=10)])


def test_proxy_selection_converts_to_governed_quote() -> None:
    result = select([candidate("PARENT", "parent", 100.0, basis=5.0)])
    quote = proxy_selection_to_quote(
        result,
        quote_id="CP1-5Y-PROXY",
        obligor_id="CP1",
        tenor_years=5.0,
        as_of_date=AS_OF,
        source_id="APPROVED-PROXY",
        probability_measure="risk_neutral",
        currency="USD",
        seniority="senior_unsecured",
    )

    assert quote.quote_type == "proxy"
    assert quote.spread_bps == 105.0

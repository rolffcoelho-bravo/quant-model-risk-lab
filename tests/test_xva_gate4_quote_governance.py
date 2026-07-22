from __future__ import annotations

from datetime import date, timedelta

import pytest

from qmrl.xva import (
    CreditQuote,
    RecoveryAssumption,
    validate_credit_quotes,
    validate_recovery_assumption,
)


AS_OF = date(2026, 1, 2)


def quote(
    tenor: float,
    *,
    age_days: int = 0,
    quote_type: str = "cds",
    measure: str = "risk_neutral",
) -> CreditQuote:
    return CreditQuote(
        quote_id=f"Q-{tenor}-{age_days}-{quote_type}-{measure}",
        obligor_id="CP1",
        tenor_years=tenor,
        spread_bps=100.0,
        as_of_date=AS_OF - timedelta(days=age_days),
        source_id="SOURCE",
        quote_type=quote_type,
        probability_measure=measure,
    )


def test_stale_quote_is_rejected() -> None:
    with pytest.raises(ValueError, match="Stale"):
        validate_credit_quotes(
            [quote(5.0, age_days=10)],
            as_of_date=AS_OF,
            max_age_days=5,
        )


def test_missing_required_tenor_is_rejected() -> None:
    with pytest.raises(ValueError, match="Missing"):
        validate_credit_quotes(
            [quote(1.0), quote(5.0)],
            as_of_date=AS_OF,
            max_age_days=5,
            required_tenors=[1.0, 3.0, 5.0],
        )


def test_risk_neutral_and_historical_quotes_cannot_be_mixed() -> None:
    with pytest.raises(ValueError, match="probability measure"):
        validate_credit_quotes(
            [quote(1.0), quote(3.0, measure="historical")],
            as_of_date=AS_OF,
            max_age_days=5,
        )


def test_bond_spread_requires_explicit_proxy_approval() -> None:
    with pytest.raises(ValueError, match="Bond spreads"):
        validate_credit_quotes(
            [quote(5.0, quote_type="bond")],
            as_of_date=AS_OF,
            max_age_days=5,
        )

    approved = validate_credit_quotes(
        [quote(5.0, quote_type="bond")],
        as_of_date=AS_OF,
        max_age_days=5,
        allow_bond_spread_proxy=True,
    )

    assert approved[0].quote_type == "bond"


def test_stale_recovery_is_rejected() -> None:
    recovery = RecoveryAssumption(
        obligor_id="CP1",
        recovery_rate=0.40,
        as_of_date=AS_OF - timedelta(days=400),
        source_id="POLICY",
    )

    with pytest.raises(ValueError, match="stale"):
        validate_recovery_assumption(
            recovery,
            as_of_date=AS_OF,
            max_age_days=365,
            expected_obligor_id="CP1",
            expected_seniority="senior_unsecured",
        )

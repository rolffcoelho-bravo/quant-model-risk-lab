from __future__ import annotations

from datetime import date

from qmrl.xva import (
    CreditQuote,
    RecoveryAssumption,
    credit_curve_manifest,
    credit_curve_sensitivity,
    calibrate_piecewise_credit_curve,
)


AS_OF = date(2026, 1, 2)


def quotes() -> tuple[CreditQuote, ...]:
    return tuple(
        CreditQuote(
            quote_id=f"Q-{tenor}",
            obligor_id="CP1",
            tenor_years=tenor,
            spread_bps=spread,
            as_of_date=AS_OF,
            source_id="SOURCE",
        )
        for tenor, spread in ((1.0, 80.0), (3.0, 100.0), (5.0, 120.0))
    )


def recovery() -> RecoveryAssumption:
    return RecoveryAssumption(
        obligor_id="CP1",
        recovery_rate=0.40,
        as_of_date=AS_OF,
        source_id="POLICY",
    )


def test_parallel_spread_bump_increases_terminal_pd() -> None:
    result = credit_curve_sensitivity(
        quotes(),
        recovery(),
        curve_id="SENS",
        role="counterparty",
        as_of_date=AS_OF,
        parallel_spread_bump_bps=1.0,
    )

    assert result.parallel_spread_pd_delta > 0.0
    assert result.max_quote_repricing_error_bps <= 1e-7


def test_higher_recovery_increases_implied_pd_for_fixed_spreads() -> None:
    result = credit_curve_sensitivity(
        quotes(),
        recovery(),
        curve_id="SENS",
        role="counterparty",
        as_of_date=AS_OF,
        recovery_bump=0.01,
    )

    assert result.recovery_pd_delta > 0.0


def test_manifest_hash_is_deterministic() -> None:
    curve = calibrate_piecewise_credit_curve(
        quotes(),
        recovery(),
        curve_id="MANIFEST",
        role="counterparty",
        as_of_date=AS_OF,
    )

    first = credit_curve_manifest(curve)
    second = credit_curve_manifest(curve)

    assert first == second
    assert len(first["credit_curve_sha256"]) == 64

from __future__ import annotations

from datetime import date

import numpy as np
import pytest

from qmrl.xva import (
    CreditQuote,
    RecoveryAssumption,
    calibrate_piecewise_credit_curve,
    par_spread_bps,
    reprice_credit_quotes,
)


AS_OF = date(2026, 1, 2)


def quotes() -> tuple[CreditQuote, ...]:
    return tuple(
        CreditQuote(
            quote_id=f"CP1-{tenor}Y",
            obligor_id="CP1",
            tenor_years=tenor,
            spread_bps=spread,
            as_of_date=AS_OF,
            source_id="LOCKED-CDS",
        )
        for tenor, spread in (
            (1.0, 80.0),
            (3.0, 100.0),
            (5.0, 120.0),
        )
    )


def recovery() -> RecoveryAssumption:
    return RecoveryAssumption(
        obligor_id="CP1",
        recovery_rate=0.40,
        as_of_date=AS_OF,
        source_id="RECOVERY-POLICY",
    )


def test_piecewise_curve_reprices_all_quotes() -> None:
    curve = calibrate_piecewise_credit_curve(
        quotes(),
        recovery(),
        curve_id="CP1-CDS",
        role="counterparty",
        as_of_date=AS_OF,
        required_tenors=[1.0, 3.0, 5.0],
    )

    report = reprice_credit_quotes(curve, quotes())

    assert report.max_abs_error_bps <= 1e-7
    assert np.all(curve.hazard_rates >= 0.0)


def test_survival_is_monotone_and_probability_bounded() -> None:
    curve = calibrate_piecewise_credit_curve(
        quotes(),
        recovery(),
        curve_id="CP1-CDS",
        role="counterparty",
        as_of_date=AS_OF,
    )

    times = np.linspace(0.0, 5.0, 101)
    survival = curve.survival_probabilities(times)

    assert np.all((survival >= 0.0) & (survival <= 1.0))
    assert np.all(np.diff(survival) <= 1e-12)


def test_counterparty_and_own_curves_are_separate_roles() -> None:
    counterparty = calibrate_piecewise_credit_curve(
        quotes(),
        recovery(),
        curve_id="CP1-COUNTERPARTY",
        role="counterparty",
        as_of_date=AS_OF,
    )

    own_quotes = tuple(
        CreditQuote(
            quote_id=quote.quote_id.replace("CP1", "OWN"),
            obligor_id="OWN",
            tenor_years=quote.tenor_years,
            spread_bps=quote.spread_bps - 20.0,
            as_of_date=AS_OF,
            source_id="LOCKED-CDS",
        )
        for quote in quotes()
    )
    own_recovery = RecoveryAssumption(
        obligor_id="OWN",
        recovery_rate=0.40,
        as_of_date=AS_OF,
        source_id="RECOVERY-POLICY",
    )
    own = calibrate_piecewise_credit_curve(
        own_quotes,
        own_recovery,
        curve_id="OWN-CREDIT",
        role="own",
        as_of_date=AS_OF,
    )

    assert counterparty.role == "counterparty"
    assert own.role == "own"
    assert own.obligor_id != counterparty.obligor_id


def test_curve_par_spread_is_positive() -> None:
    curve = calibrate_piecewise_credit_curve(
        quotes(),
        recovery(),
        curve_id="CP1-CDS",
        role="counterparty",
        as_of_date=AS_OF,
    )

    assert par_spread_bps(curve, 5.0) == pytest.approx(120.0, abs=1e-7)


def test_inconsistent_downward_curve_fails_if_negative_hazard_required() -> None:
    inconsistent = (
        CreditQuote(
            quote_id="1Y",
            obligor_id="CP1",
            tenor_years=1.0,
            spread_bps=300.0,
            as_of_date=AS_OF,
            source_id="TEST",
        ),
        CreditQuote(
            quote_id="5Y",
            obligor_id="CP1",
            tenor_years=5.0,
            spread_bps=10.0,
            as_of_date=AS_OF,
            source_id="TEST",
        ),
    )

    with pytest.raises(ValueError):
        calibrate_piecewise_credit_curve(
            inconsistent,
            recovery(),
            curve_id="INVALID",
            role="counterparty",
            as_of_date=AS_OF,
        )

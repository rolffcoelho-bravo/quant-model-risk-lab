from __future__ import annotations

from qmrl.margin import InitialMarginProfile, MarginPolicy, PathwiseMarginInput, SurvivalProfile
from qmrl.multicurrency import CurrencyCurveSet, TermCurve


TIMES = (0.0, 0.5, 1.0)


def historical_input() -> PathwiseMarginInput:
    return PathwiseMarginInput(
        netting_set_id="NS-MVA",
        currency="USD",
        times=TIMES,
        values=(
            (100.0, 70.0, 20.0),
            (100.0, 80.0, 30.0),
            (100.0, 110.0, 40.0),
            (100.0, 60.0, 10.0),
        ),
    )


def historical_policy(**overrides) -> MarginPolicy:
    values = {
        "method": "historical_simulation",
        "confidence_level": 0.75,
        "margin_period_days": 180,
        "base_margin_days": 10,
        "addon_rate": 0.0,
        "minimum_margin": 0.0,
        "received_margin_reusable": False,
        "posted_margin_segregated": True,
        "integration_rule": "trapezoid",
        "survival_treatment": "none",
    }
    values.update(overrides)
    return MarginPolicy(**values)


def margin_profile(*, reusable=False, posted=(100.0, 80.0, 0.0), received=(20.0, 10.0, 0.0)):
    return InitialMarginProfile(
        netting_set_id="NS-MVA",
        currency="USD",
        times=TIMES,
        posted_margin=posted,
        received_margin=received,
        method="historical_simulation",
        policy_hash="gate3-policy",
        received_margin_reusable=reusable,
    )


def curves(*, funding=(0.02, 0.02, 0.02), remuneration=(0.005, 0.005, 0.005)):
    return CurrencyCurveSet(
        (
            TermCurve("USD-DISC", "USD", "discount", TIMES, (1.0, 0.98, 0.95)),
            TermCurve("USD-FUND", "USD", "funding", TIMES, funding),
            TermCurve("USD-COLL", "USD", "collateral_remuneration", TIMES, remuneration),
        )
    )


def survival():
    return SurvivalProfile(
        times=TIMES,
        own_survival=(1.0, 0.98, 0.95),
        counterparty_survival=(1.0, 0.97, 0.93),
    )

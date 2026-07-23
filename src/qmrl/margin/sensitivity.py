"""Standard Gate 3 MVA sensitivities."""

from __future__ import annotations

from qmrl.multicurrency import CurrencyCurveSet

from .domain import InitialMarginProfile, MarginPolicy, MVAResult, SurvivalProfile
from .mva import calculate_mva


def build_standard_mva_sensitivities(
    profile: InitialMarginProfile,
    curve_set: CurrencyCurveSet,
    policy: MarginPolicy,
    *,
    survival: SurvivalProfile | None = None,
) -> dict[str, MVAResult]:
    return {
        "base": calculate_mva(profile, curve_set, policy, survival=survival),
        "funding_up_10bps": calculate_mva(
            profile,
            curve_set,
            policy,
            survival=survival,
            funding_spread_shift_bps=10.0,
        ),
        "remuneration_up_10bps": calculate_mva(
            profile,
            curve_set,
            policy,
            survival=survival,
            remuneration_shift_bps=10.0,
        ),
        "margin_up_10pct": calculate_mva(
            profile,
            curve_set,
            policy,
            survival=survival,
            margin_scale=1.10,
        ),
    }

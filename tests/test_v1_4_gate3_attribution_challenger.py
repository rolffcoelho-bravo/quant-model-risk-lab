import math

from qmrl.margin import (
    InitialMarginProfile,
    aggregate_mva,
    build_standard_mva_sensitivities,
    calculate_mva,
    challenge_mva,
    independent_mva,
)

from v1_4_gate3_helpers import curves, historical_policy, margin_profile


def test_independent_challenger_reconciles():
    primary = calculate_mva(margin_profile(), curves(), historical_policy())
    challenger = independent_mva(margin_profile(), curves(), historical_policy())
    assert math.isclose(primary.net_mva, challenger, rel_tol=1e-14)


def test_challenge_report_passes_with_tight_tolerance():
    primary = calculate_mva(margin_profile(), curves(), historical_policy())
    report = challenge_mva(
        primary.net_mva, margin_profile(), curves(), historical_policy(), tolerance=1e-12
    )
    assert report.status == "PASS"


def test_challenge_report_flags_material_difference():
    report = challenge_mva(
        999.0, margin_profile(), curves(), historical_policy(), tolerance=1e-12
    )
    assert report.status == "REMEDIATE"


def test_aggregate_mva_reconciles_components():
    one = calculate_mva(margin_profile(), curves(), historical_policy())
    second_profile = InitialMarginProfile(
        "NS-2", "EUR", margin_profile().times,
        margin_profile().posted_margin, margin_profile().received_margin,
        "historical_simulation", "policy-2", False,
    )
    eur_curves = type(curves())((
        __import__('qmrl.multicurrency', fromlist=['TermCurve']).TermCurve("EUR-D", "EUR", "discount", margin_profile().times, (1.0, 0.98, 0.95)),
        __import__('qmrl.multicurrency', fromlist=['TermCurve']).TermCurve("EUR-F", "EUR", "funding", margin_profile().times, (0.02, 0.02, 0.02)),
        __import__('qmrl.multicurrency', fromlist=['TermCurve']).TermCurve("EUR-C", "EUR", "collateral_remuneration", margin_profile().times, (0.005, 0.005, 0.005)),
    ))
    two = calculate_mva(second_profile, eur_curves, historical_policy())
    aggregate = aggregate_mva((one, two))
    assert math.isclose(aggregate.net_mva, one.net_mva + two.net_mva)
    assert set(aggregate.by_currency) == {"EUR", "USD"}


def test_concentration_metrics_are_bounded():
    one = calculate_mva(margin_profile(), curves(), historical_policy())
    aggregate = aggregate_mva((one, one))
    assert math.isclose(aggregate.concentration_hhi, 0.5)
    assert math.isclose(aggregate.maximum_share, 0.5)


def test_standard_sensitivities_have_expected_direction():
    results = build_standard_mva_sensitivities(
        margin_profile(), curves(), historical_policy()
    )
    assert results["funding_up_10bps"].net_mva > results["base"].net_mva
    assert results["remuneration_up_10bps"].net_mva < results["base"].net_mva
    assert results["margin_up_10pct"].net_mva > results["base"].net_mva

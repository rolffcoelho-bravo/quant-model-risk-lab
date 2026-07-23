import pytest

from qmrl.multicurrency import FXQuote, FXScenarioMarket, PathwiseSeries


def test_pathwise_series_normalizes_currency():
    series = PathwiseSeries("eur", (0, 1), ((1, 2),))
    assert series.currency == "EUR"
    assert series.path_count == 1


def test_pathwise_series_rejects_non_increasing_grid():
    with pytest.raises(ValueError):
        PathwiseSeries("USD", (0, 0), ((1, 2),))


def test_fx_quote_rejects_non_positive_rates():
    with pytest.raises(ValueError):
        FXQuote("EUR", "USD", (0,), ((0.0,),))


def test_identity_rate_is_one():
    assert FXScenarioMarket().rate("USD", "USD", 0, 0) == 1.0


def test_direct_rate():
    market = FXScenarioMarket(
        (FXQuote("EUR", "USD", (0,), ((1.1,),)),)
    )
    assert market.rate("EUR", "USD", 0, 0) == pytest.approx(1.1)


def test_inverse_rate():
    market = FXScenarioMarket(
        (FXQuote("EUR", "USD", (0,), ((1.25,),)),)
    )
    assert market.rate("USD", "EUR", 0, 0) == pytest.approx(0.8)


def test_triangular_rate():
    market = FXScenarioMarket(
        (
            FXQuote("GBP", "EUR", (0,), ((1.2,),)),
            FXQuote("EUR", "USD", (0,), ((1.1,),)),
        ),
        triangulation_currency="EUR",
    )
    assert market.rate("GBP", "USD", 0, 0) == pytest.approx(1.32)


def test_missing_governed_path_is_blocked():
    with pytest.raises(KeyError):
        FXScenarioMarket().rate("EUR", "USD", 0, 0)


def test_duplicate_quote_is_blocked():
    quote = FXQuote("EUR", "USD", (0,), ((1.1,),))
    with pytest.raises(ValueError):
        FXScenarioMarket((quote, quote))


def test_triangulation_report_passes_for_consistent_quotes():
    market = FXScenarioMarket(
        (
            FXQuote("GBP", "USD", (0,), ((1.32,),)),
            FXQuote("GBP", "EUR", (0,), ((1.2,),)),
            FXQuote("EUR", "USD", (0,), ((1.1,),)),
        )
    )
    report = market.triangulation_report("GBP", "USD", "EUR")
    assert report.passed
    assert report.maximum_absolute_error == pytest.approx(0.0)

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from qmrl.black_scholes import OptionInputs, black_scholes_price, vega


def test_black_scholes_call_price_positive():
    inputs = OptionInputs(spot=100, strike=100, rate=0.05, volatility=0.2, maturity=1, option_type="call")
    price = black_scholes_price(inputs)

    assert price > 0


def test_higher_volatility_increases_call_value():
    low_vol = OptionInputs(spot=100, strike=100, rate=0.05, volatility=0.1, maturity=1, option_type="call")
    high_vol = OptionInputs(spot=100, strike=100, rate=0.05, volatility=0.3, maturity=1, option_type="call")

    assert black_scholes_price(high_vol) > black_scholes_price(low_vol)


def test_vega_positive_for_standard_option():
    inputs = OptionInputs(spot=100, strike=100, rate=0.05, volatility=0.2, maturity=1, option_type="call")

    assert vega(inputs) > 0

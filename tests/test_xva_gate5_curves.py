from datetime import date
import numpy as np
import pytest

from qmrl.xva import DiscountCurve, FundingCurve

AS_OF = date(2026, 1, 2)

def test_discount_curve_log_linear_interpolation() -> None:
    curve = DiscountCurve("OIS", "USD", AS_OF, np.array([0.0, 1.0]), np.array([1.0, np.exp(-0.02)]))
    assert curve.discount_factor(0.5) == pytest.approx(np.exp(-0.01))

def test_discount_curve_rejects_increasing_factors() -> None:
    with pytest.raises(ValueError):
        DiscountCurve("BAD", "USD", AS_OF, [0.0, 1.0], [1.0, 1.01])

def test_forbidden_discount_extrapolation() -> None:
    curve = DiscountCurve("OIS", "USD", AS_OF, [0.0, 1.0], [1.0, 0.98], "forbidden")
    with pytest.raises(ValueError):
        curve.discount_factor(2.0)

def test_funding_curve_interpolates_borrow_and_lend() -> None:
    curve = FundingCurve("FUND", "USD", AS_OF, [0.0, 1.0], [100.0, 200.0], [50.0, 100.0])
    assert curve.spreads_bps(0.5) == pytest.approx((150.0, 75.0))

def test_funding_curve_rejects_lending_above_borrowing() -> None:
    with pytest.raises(ValueError):
        FundingCurve("BAD", "USD", AS_OF, [0.0, 1.0], [50.0, 50.0], [60.0, 60.0])

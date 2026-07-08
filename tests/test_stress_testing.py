import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from qmrl.stress_testing import apply_return_shock, stress_loss


def test_apply_return_shock_reduces_value_for_negative_shock():
    stressed_value = apply_return_shock(portfolio_value=1000, shock_return=-0.10)

    assert stressed_value == 900


def test_stress_loss_positive_for_negative_shock():
    loss = stress_loss(portfolio_value=1000, shock_return=-0.10)

    assert loss == 100

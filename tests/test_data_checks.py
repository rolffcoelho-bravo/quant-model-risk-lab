import sys
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from qmrl.data_checks import assert_required_columns, missing_value_report


def test_missing_value_report_counts_missing_values():
    data = pd.DataFrame({"price": [1.0, None, 3.0], "return": [0.1, 0.2, None]})
    report = missing_value_report(data)

    assert report.loc["price", "missing_count"] == 1
    assert report.loc["return", "missing_count"] == 1


def test_required_columns_passes_when_columns_exist():
    data = pd.DataFrame({"date": [], "price": []})
    assert_required_columns(data, ["date", "price"])

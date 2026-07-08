import sys
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from qmrl.reporting import dataframe_to_markdown, validation_decision


def test_dataframe_to_markdown_contains_headers():
    data = pd.DataFrame({"model_id": ["MRM001"], "status": ["Pass"]})
    markdown = dataframe_to_markdown(data)

    assert "model_id" in markdown
    assert "MRM001" in markdown


def test_validation_decision_passes_below_threshold():
    assert validation_decision(exception_rate=0.05, threshold=0.10) == "Pass"


def test_validation_decision_requires_review_above_threshold():
    assert validation_decision(exception_rate=0.15, threshold=0.10) == "Review required"

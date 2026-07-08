import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from qmrl.monitoring import threshold_monitor


def test_threshold_monitor_passes_when_metric_below_threshold():
    result = threshold_monitor(
        model_id="MRM002",
        metric_name="Exception rate",
        metric_value=0.04,
        threshold=0.10,
    )

    assert result.status == "pass"


def test_threshold_monitor_flags_review_when_metric_above_threshold():
    result = threshold_monitor(
        model_id="MRM002",
        metric_name="Exception rate",
        metric_value=0.15,
        threshold=0.10,
    )

    assert result.status == "review"

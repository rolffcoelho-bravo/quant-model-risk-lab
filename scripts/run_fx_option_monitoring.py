"""Create governed FX-option monitoring and revalidation evidence."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from qmrl.fx_option_governance import (
    load_fx_option_governance_contract,
)
from qmrl.fx_option_monitoring import (
    FXOptionMonitoringSnapshot,
    evaluate_fx_option_monitoring,
)


SUMMARY_PATH = (
    ROOT
    / "data"
    / "official"
    / "processed"
    / "fx_option_validation_summary.csv"
)

PARITY_PATH = (
    ROOT
    / "data"
    / "official"
    / "processed"
    / "fx_option_put_call_parity_table.csv"
)

BASELINE_PATH = (
    ROOT
    / "data"
    / "official"
    / "processed"
    / "fx_option_monitoring_baseline.csv"
)

STATUS_PATH = (
    ROOT
    / "data"
    / "official"
    / "processed"
    / "fx_option_monitoring_status.csv"
)

REPORT_PATH = (
    ROOT
    / "reports"
    / "fx_option_monitoring_report.md"
)


def normalise_name(value: str) -> str:
    return re.sub(
        r"[^a-z0-9]+",
        "",
        value.lower(),
    )


def first_numeric(
    row: pd.Series,
    candidates: Iterable[str],
) -> float:
    by_normalised_name = {
        normalise_name(str(column)): column
        for column in row.index
    }

    for candidate in candidates:
        key = normalise_name(candidate)

        if key in by_normalised_name:
            value = pd.to_numeric(
                row[
                    by_normalised_name[key]
                ],
                errors="coerce",
            )

            if pd.notna(value):
                return float(value)

    raise KeyError(
        "None of the required columns were found: "
        + ", ".join(candidates)
    )


def current_snapshot() -> FXOptionMonitoringSnapshot:
    if not SUMMARY_PATH.exists():
        raise FileNotFoundError(
            "The FX-option validation summary is missing."
        )

    if not PARITY_PATH.exists():
        raise FileNotFoundError(
            "The put-call parity evidence is missing."
        )

    summary = pd.read_csv(
        SUMMARY_PATH
    ).iloc[0]

    parity = pd.read_csv(
        PARITY_PATH
    ).iloc[0]

    spot = first_numeric(
        summary,
        [
            "spot_rate_brl_per_usd",
            "spot_rate",
            "spot",
        ],
    )

    realised_volatility = first_numeric(
        summary,
        [
            "realised_volatility_input",
            "realized_volatility_input",
            "volatility",
        ],
    )

    domestic_rate = first_numeric(
        summary,
        [
            "domestic_rate_brl",
            "domestic_rate",
        ],
    )

    foreign_rate = first_numeric(
        summary,
        [
            "foreign_rate_usd",
            "foreign_rate",
        ],
    )

    call_delta = first_numeric(
        summary,
        [
            "call_delta",
            "delta_call",
            "delta",
        ],
    )

    vega = first_numeric(
        summary,
        [
            "call_vega",
            "vega",
        ],
    )

    parity_gap = abs(
        first_numeric(
            parity,
            [
                "parity_gap",
                "put_call_parity_gap",
            ],
        )
    )

    call_premium = abs(
        first_numeric(
            summary,
            [
                "call_value_brl",
                "call_premium_brl",
                "call_premium_domestic",
                "call_value",
            ],
        )
    )

    parity_relative_gap = (
        parity_gap
        / max(
            call_premium,
            1.0,
        )
    )

    return FXOptionMonitoringSnapshot(
        spot_rate=spot,
        realised_volatility=realised_volatility,
        domestic_rate=domestic_rate,
        foreign_rate=foreign_rate,
        parity_relative_gap=parity_relative_gap,
        call_delta=call_delta,
        vega=vega,
    )


def snapshot_record(
    snapshot: FXOptionMonitoringSnapshot,
) -> dict[str, object]:
    return {
        "created_at_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "spot_rate": snapshot.spot_rate,
        "realised_volatility": (
            snapshot.realised_volatility
        ),
        "domestic_rate": snapshot.domestic_rate,
        "foreign_rate": snapshot.foreign_rate,
        "parity_relative_gap": (
            snapshot.parity_relative_gap
        ),
        "call_delta": snapshot.call_delta,
        "vega": snapshot.vega,
    }


def load_baseline() -> FXOptionMonitoringSnapshot:
    if not BASELINE_PATH.exists():
        raise FileNotFoundError(
            "The monitoring baseline has not been initialized."
        )

    row = pd.read_csv(
        BASELINE_PATH
    ).iloc[0]

    return FXOptionMonitoringSnapshot(
        spot_rate=float(row["spot_rate"]),
        realised_volatility=float(
            row["realised_volatility"]
        ),
        domestic_rate=float(
            row["domestic_rate"]
        ),
        foreign_rate=float(
            row["foreign_rate"]
        ),
        parity_relative_gap=float(
            row["parity_relative_gap"]
        ),
        call_delta=float(row["call_delta"]),
        vega=float(row["vega"]),
    )


def write_baseline(
    snapshot: FXOptionMonitoringSnapshot,
) -> None:
    BASELINE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    pd.DataFrame(
        [snapshot_record(snapshot)]
    ).to_csv(
        BASELINE_PATH,
        index=False,
    )


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--initialize-baseline",
        action="store_true",
    )

    args = parser.parse_args()

    contract = load_fx_option_governance_contract()
    current = current_snapshot()

    if (
        args.initialize_baseline
        or not BASELINE_PATH.exists()
    ):
        write_baseline(current)

        print(
            f"Wrote {BASELINE_PATH.relative_to(ROOT)}"
        )
        print("Monitoring baseline: INITIALIZED")

    baseline = load_baseline()

    result = evaluate_fx_option_monitoring(
        current=current,
        baseline=baseline,
        policy=contract.monitoring,
    )

    alerts_json = json.dumps(
        list(result.alerts),
        ensure_ascii=False,
    )

    status_record = {
        "created_at_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "contract_id": contract.contract_id,
        "monitoring_status": (
            result.monitoring_status
        ),
        "revalidation_required": (
            result.revalidation_required
        ),
        "alerts_json": alerts_json,
        "spot_move_relative": (
            result.spot_move_relative
        ),
        "spot_move_relative_threshold": (
            contract.monitoring
            .spot_move_relative_threshold
        ),
        "realised_volatility_change_absolute": (
            result
            .realised_volatility_change_absolute
        ),
        "realised_volatility_change_absolute_threshold": (
            contract.monitoring
            .realised_volatility_change_absolute_threshold
        ),
        "domestic_rate_change_absolute": (
            result.domestic_rate_change_absolute
        ),
        "domestic_rate_change_absolute_threshold": (
            contract.monitoring
            .domestic_rate_change_absolute_threshold
        ),
        "foreign_rate_change_absolute": (
            result.foreign_rate_change_absolute
        ),
        "foreign_rate_change_absolute_threshold": (
            contract.monitoring
            .foreign_rate_change_absolute_threshold
        ),
        "parity_relative_gap": (
            result.parity_relative_gap
        ),
        "parity_relative_gap_threshold": (
            contract.monitoring
            .parity_relative_gap_threshold
        ),
        "delta_sign_change": (
            result.delta_sign_change
        ),
        "vega_sign_change": (
            result.vega_sign_change
        ),
        "model_owner": (
            contract.monitoring.model_owner
        ),
        "validation_owner": (
            contract.monitoring.validation_owner
        ),
        "escalation_owner": (
            contract.monitoring.escalation_owner
        ),
        "review_frequency": (
            contract.monitoring.review_frequency
        ),
        "market_quote_benchmark": (
            contract.model_boundaries
            .market_quote_benchmark
        ),
        "production_approval": (
            contract.model_boundaries
            .production_approval
        ),
    }

    STATUS_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    pd.DataFrame(
        [status_record]
    ).to_csv(
        STATUS_PATH,
        index=False,
    )

    alert_lines = (
        "\n".join(
            f"- {alert}"
            for alert in result.alerts
        )
        if result.alerts
        else "- No monitoring threshold was breached."
    )

    report = f"""# FX Option Monitoring Report

## Decision

Monitoring status: **{result.monitoring_status}**

Revalidation required: **{str(result.revalidation_required).upper()}**

Production approval: **NO**

Market-quote benchmark: **{contract.model_boundaries.market_quote_benchmark}**

## Quantitative controls

| Control | Observed | Threshold | Breach |
|---|---:|---:|---|
| Relative spot move | {result.spot_move_relative:.12f} | {contract.monitoring.spot_move_relative_threshold:.12f} | {result.spot_move_relative >= contract.monitoring.spot_move_relative_threshold} |
| Absolute realised-volatility change | {result.realised_volatility_change_absolute:.12f} | {contract.monitoring.realised_volatility_change_absolute_threshold:.12f} | {result.realised_volatility_change_absolute >= contract.monitoring.realised_volatility_change_absolute_threshold} |
| Absolute domestic-rate change | {result.domestic_rate_change_absolute:.12f} | {contract.monitoring.domestic_rate_change_absolute_threshold:.12f} | {result.domestic_rate_change_absolute >= contract.monitoring.domestic_rate_change_absolute_threshold} |
| Absolute foreign-rate change | {result.foreign_rate_change_absolute:.12f} | {contract.monitoring.foreign_rate_change_absolute_threshold:.12f} | {result.foreign_rate_change_absolute >= contract.monitoring.foreign_rate_change_absolute_threshold} |
| Relative parity gap | {result.parity_relative_gap:.12f} | {contract.monitoring.parity_relative_gap_threshold:.12f} | {result.parity_relative_gap >= contract.monitoring.parity_relative_gap_threshold} |
| Call-delta sign change | {result.delta_sign_change} | False | {result.delta_sign_change} |
| Vega sign change | {result.vega_sign_change} | False | {result.vega_sign_change} |

## Alerts

{alert_lines}

## Ownership

- Model owner: `{contract.monitoring.model_owner}`
- Validation owner: `{contract.monitoring.validation_owner}`
- Escalation owner: `{contract.monitoring.escalation_owner}`
- Review frequency: `{contract.monitoring.review_frequency}`

## Governance boundary

The thresholds are public validation controls. They are not production limits, trading limits or regulatory materiality thresholds.

A threshold breach creates a revalidation requirement in the repository evidence. External alert delivery and production workflow integration remain outside the public repository scope.
"""

    REPORT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    REPORT_PATH.write_text(
        report,
        encoding="utf-8",
    )

    print(
        f"Wrote {STATUS_PATH.relative_to(ROOT)}"
    )
    print(
        f"Wrote {REPORT_PATH.relative_to(ROOT)}"
    )
    print(
        f"Monitoring status: {result.monitoring_status}"
    )
    print(
        "Revalidation required: "
        f"{result.revalidation_required}"
    )

    if result.revalidation_required:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
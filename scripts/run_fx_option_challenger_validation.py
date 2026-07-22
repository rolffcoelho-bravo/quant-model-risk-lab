"""Run independent FX-option challenger and numerical-Greek validation."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from qmrl.fx_option_challenger import (
    black76_fx_price,
    finite_difference_greeks,
    relative_error,
)
from qmrl.fx_options import (
    garman_kohlhagen_price,
)


SUMMARY_PATH = (
    ROOT
    / "data"
    / "official"
    / "processed"
    / "fx_option_validation_summary.csv"
)

OUTPUT_PATH = (
    ROOT
    / "data"
    / "official"
    / "processed"
    / "fx_option_challenger_benchmark.csv"
)

REPORT_PATH = (
    ROOT
    / "reports"
    / "fx_option_challenger_validation_report.md"
)


PRICE_RELATIVE_TOLERANCE = 1.0e-10
DELTA_RELATIVE_TOLERANCE = 5.0e-5
GAMMA_RELATIVE_TOLERANCE = 5.0e-4
VEGA_RELATIVE_TOLERANCE = 5.0e-4


def gk_premium(
    *,
    option_type: str,
    spot_rate: float,
    strike_rate: float,
    domestic_rate: float,
    foreign_rate: float,
    volatility: float,
    maturity_years: float,
    notional_foreign: float,
) -> float:
    return garman_kohlhagen_price(
        option_type=option_type,
        spot_rate=spot_rate,
        strike_rate=strike_rate,
        domestic_rate=domestic_rate,
        foreign_rate=foreign_rate,
        volatility=volatility,
        maturity_years=maturity_years,
        notional_foreign=notional_foreign,
    ).premium_domestic


def run_challenger_validation() -> None:
    subprocess.run(
        [
            sys.executable,
            "scripts/run_fx_options_validation.py",
        ],
        check=True,
    )

    summary = pd.read_csv(
        SUMMARY_PATH
    ).iloc[0]

    inputs = {
        "spot_rate": float(
            summary["spot_rate_brl_per_usd"]
        ),
        "strike_rate": float(
            summary["strike_rate"]
        ),
        "domestic_rate": float(
            summary["domestic_rate_brl"]
        ),
        "foreign_rate": float(
            summary["foreign_rate_usd"]
        ),
        "volatility": float(
            summary["realised_volatility_input"]
        ),
        "maturity_years": float(
            summary["maturity_years"]
        ),
        "notional_foreign": float(
            summary["notional_usd"]
        ),
    }

    rows: list[dict[str, object]] = []

    for option_type in ("call", "put"):
        gk = garman_kohlhagen_price(
            option_type=option_type,
            **inputs,
        )

        black76_price = black76_fx_price(
            option_type=option_type,
            **inputs,
        )

        numerical = finite_difference_greeks(
            gk_premium,
            option_type=option_type,
            **inputs,
        )

        price_error = relative_error(
            gk.premium_domestic,
            black76_price,
        )

        delta_error = relative_error(
            gk.delta,
            numerical.delta,
        )

        gamma_error = relative_error(
            gk.gamma,
            numerical.gamma,
        )

        vega_error = relative_error(
            gk.vega,
            numerical.vega,
        )

        status = (
            "PASS"
            if (
                price_error
                <= PRICE_RELATIVE_TOLERANCE
                and delta_error
                <= DELTA_RELATIVE_TOLERANCE
                and gamma_error
                <= GAMMA_RELATIVE_TOLERANCE
                and vega_error
                <= VEGA_RELATIVE_TOLERANCE
            )
            else "FAIL"
        )

        rows.append(
            {
                "model_id": "QMRL-FX-OPT-001",
                "option_type": option_type,
                "gk_premium_brl": (
                    gk.premium_domestic
                ),
                "black76_challenger_premium_brl": (
                    black76_price
                ),
                "price_relative_error": price_error,
                "analytic_delta": gk.delta,
                "finite_difference_delta": (
                    numerical.delta
                ),
                "delta_relative_error": delta_error,
                "analytic_gamma": gk.gamma,
                "finite_difference_gamma": (
                    numerical.gamma
                ),
                "gamma_relative_error": gamma_error,
                "analytic_vega": gk.vega,
                "finite_difference_vega": (
                    numerical.vega
                ),
                "vega_relative_error": vega_error,
                "implementation_challenger_status": (
                    status
                ),
                "market_quote_benchmark_status": (
                    "OPEN_NO_PUBLIC_QUOTE_DATA"
                ),
            }
        )

    benchmark = pd.DataFrame(rows)

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    benchmark.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    overall_status = (
        "PASS"
        if set(
            benchmark[
                "implementation_challenger_status"
            ]
        ) == {"PASS"}
        else "FAIL"
    )

    report = f"""# FX Option Challenger Validation Report

## Purpose

This control compares the repository Garman-Kohlhagen implementation with an independently formulated forward-based Black-76 challenger.

It also compares analytic delta, gamma and vega with central finite-difference estimates.

## Governed market inputs

- Currency pair: `{summary["currency_pair"]}`
- Quote convention: `{summary["quote_convention"]}`
- Spot source: `{summary["spot_source_id"]}`
- Domestic-rate source: `{summary["domestic_rate_source_id"]}`
- Foreign-rate source: `{summary["foreign_rate_source_id"]}`
- Input contract: `{summary["input_contract_status"]}`

## Implementation benchmark

Overall challenger status: **{overall_status}**

{benchmark.to_markdown(index=False)}

## Market benchmark boundary

Market-quote benchmark status: **OPEN_NO_PUBLIC_QUOTE_DATA**

The implementation benchmark verifies internal pricing equivalence and numerical Greeks. It does not demonstrate agreement with traded USD/BRL option quotes or a market volatility surface.

Market-quote benchmarking remains an open validation gate and must not be inferred from the implementation challenger.

## Model-use decision

The corrected layer is available for governed validation review of vanilla European USD/BRL option pricing.

It is not production approved and does not support smile-calibrated, barrier, path-dependent or automated trading use.
"""

    REPORT_PATH.write_text(
        report,
        encoding="utf-8",
    )

    print(
        f"Wrote {OUTPUT_PATH.relative_to(ROOT)}"
    )
    print(
        f"Wrote {REPORT_PATH.relative_to(ROOT)}"
    )
    print(
        f"Implementation challenger: {overall_status}"
    )
    print(
        "Market quote benchmark: OPEN_NO_PUBLIC_QUOTE_DATA"
    )

    if overall_status != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    run_challenger_validation()
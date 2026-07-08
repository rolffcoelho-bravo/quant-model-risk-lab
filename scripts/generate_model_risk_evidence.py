"""Generate a public model-risk evidence report."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.append(str(SRC))

from qmrl.black_scholes import OptionInputs, black_scholes_price, delta, vega
from qmrl.monitoring import threshold_monitor
from qmrl.reporting import dataframe_to_markdown, validation_decision, write_markdown_report
from qmrl.stress_testing import stress_loss
from qmrl.var_backtesting import count_var_exceptions, exception_rate, historical_var


def main() -> None:
    model_register = pd.read_csv(ROOT / "model_inventory" / "model_register.csv")
    validation_status = pd.read_csv(ROOT / "model_inventory" / "validation_status.csv")
    findings_log = pd.read_csv(ROOT / "model_inventory" / "findings_log.csv")

    returns = pd.Series(
        [
            0.004, -0.006, 0.003, -0.012, 0.008,
            -0.021, 0.011, -0.004, -0.033, 0.006,
            -0.014, 0.002, -0.009, 0.007, -0.018,
            0.005, -0.027, 0.009, -0.003, -0.011,
        ],
        name="returns",
    )

    var_95 = historical_var(returns, confidence_level=0.95)
    exceptions = count_var_exceptions(returns, var_95)
    ex_rate = exception_rate(returns, var_95)

    option = OptionInputs(
        spot=100.0,
        strike=100.0,
        rate=0.05,
        volatility=0.20,
        maturity=1.0,
        option_type="call",
    )

    option_price = black_scholes_price(option)
    option_delta = delta(option)
    option_vega = vega(option)

    stressed_loss = stress_loss(portfolio_value=1_000_000.0, shock_return=-0.08)

    monitoring_result = threshold_monitor(
        model_id="MRM002",
        metric_name="VaR exception rate",
        metric_value=ex_rate,
        threshold=0.10,
    )

    decision = validation_decision(exception_rate=ex_rate, threshold=0.10)

    summary = {
        "black_scholes_call_price": round(option_price, 6),
        "black_scholes_delta": round(option_delta, 6),
        "black_scholes_vega": round(option_vega, 6),
        "historical_var_95": round(var_95, 6),
        "var_exceptions": exceptions,
        "var_exception_rate": round(ex_rate, 6),
        "stress_loss_8pct": round(stressed_loss, 2),
        "monitoring_status": monitoring_result.status,
        "validation_decision": decision,
    }

    sections = {
        "Executive Summary": (
            "This report is generated from the public Quant Model Risk Lab codebase. "
            "It demonstrates model inventory tracking, validation-status evidence, "
            "Black-Scholes option-pricing checks, Historical VaR monitoring, stress testing "
            "and documentation of model limitations."
        ),
        "Model Inventory": dataframe_to_markdown(model_register),
        "Validation Status": dataframe_to_markdown(validation_status),
        "Findings Log": dataframe_to_markdown(findings_log),
        "Black-Scholes Validation Snapshot": (
            f"Call price: {option_price:.6f}\n\n"
            f"Delta: {option_delta:.6f}\n\n"
            f"Vega: {option_vega:.6f}\n\n"
            "Interpretation: the option-pricing module produces positive prices and expected "
            "sensitivity behaviour under standard inputs. The model remains limited by constant "
            "volatility and simplified market assumptions."
        ),
        "VaR Monitoring Snapshot": (
            f"Historical VaR 95 percent: {var_95:.6f}\n\n"
            f"Exceptions: {exceptions}\n\n"
            f"Exception rate: {ex_rate:.6f}\n\n"
            f"Monitoring status: {monitoring_result.status}\n\n"
            f"Validation decision: {decision}"
        ),
        "Stress Testing Snapshot": (
            f"Portfolio value: 1,000,000\n\n"
            f"Shock return: -8 percent\n\n"
            f"Stress loss: {stressed_loss:.2f}"
        ),
        "Limitations": (
            "This evidence package is educational and public. It does not represent proprietary "
            "banking models, production systems, confidential data or formal institutional approval. "
            "Its purpose is to show reproducible validation logic, documentation discipline and "
            "Python-based risk analytics."
        ),
    }

    write_markdown_report(
        path=ROOT / "reports" / "generated_model_risk_evidence.md",
        title="Generated Model Risk Evidence Report",
        sections=sections,
    )

    (ROOT / "reports" / "generated_model_risk_evidence.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )

    print("Generated reports:")
    print("reports/generated_model_risk_evidence.md")
    print("reports/generated_model_risk_evidence.json")


if __name__ == "__main__":
    main()

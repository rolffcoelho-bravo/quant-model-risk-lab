# Generated Model Risk Evidence Report

## Executive Summary

This report is generated from the public Quant Model Risk Lab codebase. It demonstrates model inventory tracking, validation-status evidence, Black-Scholes option-pricing checks, Historical VaR monitoring, stress testing and documentation of model limitations.

## Model Inventory

| model_id | model_name | asset_class | model_type | owner | status | last_validation | next_review | risk_rating |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MRM001 | Black-Scholes Option Model | Equity Options | Valuation | Research | Pass with limitations | 2026-07-08 | 2027-01-08 | Medium |
| MRM002 | Historical VaR Model | Market Risk | Risk Model | Research | Under review | 2026-07-08 | 2027-01-08 | High |
| MRM003 | Stress Testing Module | Market Risk | Scenario Model | Research | Draft | 2026-07-08 | 2027-01-08 | Medium |

## Validation Status

| model_id | validation_area | check_name | result | comment |
| --- | --- | --- | --- | --- |
| MRM001 | Implementation | Call price positive | Pass | Price output is positive for standard inputs |
| MRM001 | Sensitivity | Higher volatility increases call value | Pass | Expected option-pricing behaviour |
| MRM002 | Backtesting | VaR exceptions counted | Pass | Exception count generated from return series |
| MRM003 | Stress | Negative shock reduces portfolio value | Pass | Stress logic behaves as expected |

## Findings Log

| finding_id | model_id | severity | status | finding | owner | target_date |
| --- | --- | --- | --- | --- | --- | --- |
| F001 | MRM001 | Medium | Open | Black-Scholes assumes constant volatility and does not represent volatility-smile dynamics | Research | 2027-01-08 |
| F002 | MRM002 | High | Open | Historical VaR can underestimate risk during regime shifts and volatility clustering | Research | 2027-01-08 |
| F003 | MRM003 | Medium | Open | Stress scenarios are simplified and require stronger scenario calibration before production use | Research | 2027-01-08 |

## Black-Scholes Validation Snapshot

Call price: 10.450584

Delta: 0.636831

Vega: 37.524035

Interpretation: the option-pricing module produces positive prices and expected sensitivity behaviour under standard inputs. The model remains limited by constant volatility and simplified market assumptions.

## VaR Monitoring Snapshot

Historical VaR 95 percent: 0.027300

Exceptions: 1

Exception rate: 0.050000

Monitoring status: pass

Validation decision: Pass

## Stress Testing Snapshot

Portfolio value: 1,000,000

Shock return: -8 percent

Stress loss: 80000.00

## Limitations

This evidence package is educational and public. It does not represent proprietary banking models, production systems, confidential data or formal institutional approval. Its purpose is to show reproducible validation logic, documentation discipline and Python-based risk analytics.

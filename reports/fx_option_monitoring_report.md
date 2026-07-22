# FX Option Monitoring Report

## Decision

Monitoring status: **PASS**

Revalidation required: **FALSE**

Production approval: **NO**

Market-quote benchmark: **OPEN_NO_PUBLIC_QUOTE_DATA**

## Quantitative controls

| Control | Observed | Threshold | Breach |
|---|---:|---:|---|
| Relative spot move | 0.000000000000 | 0.050000000000 | False |
| Absolute realised-volatility change | 0.000000000000 | 0.050000000000 | False |
| Absolute domestic-rate change | 0.000000000000 | 0.010000000000 | False |
| Absolute foreign-rate change | 0.000000000000 | 0.010000000000 | False |
| Relative parity gap | 0.000000000000 | 0.000001000000 | False |
| Call-delta sign change | False | False | False |
| Vega sign change | False | False | False |

## Alerts

- No monitoring threshold was breached.

## Ownership

- Model owner: `ShockBridge Pulse Research`
- Validation owner: `Independent Model Validation`
- Escalation owner: `Model Risk Governance`
- Review frequency: `per governed validation run`

## Governance boundary

The thresholds are public validation controls. They are not production limits, trading limits or regulatory materiality thresholds.

A threshold breach creates a revalidation requirement in the repository evidence. External alert delivery and production workflow integration remain outside the public repository scope.

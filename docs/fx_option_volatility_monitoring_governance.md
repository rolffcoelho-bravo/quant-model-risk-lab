# FX Option Volatility and Monitoring Governance

## Purpose

This control closes the repository-level governance gaps for realised-volatility estimation, volatility-floor behaviour, monitoring thresholds, ownership, alerts and revalidation triggers.

## Realised-volatility estimator

The estimator uses log returns from positive FX levels.

The governed parameters are stored in `configs/fx_option_governance_contract.json`.

The current public validation contract preserves the prior estimator design while making every assumption explicit and testable:

- annualisation observations: `252`
- maximum lookback: `60` returns
- minimum observations before estimation: `20`
- insufficient-data fallback: `0.15`
- lower estimator bound: `0.05`
- upper estimator bound: `0.60`

The fallback is used only when the available return history is below the minimum requirement.

The lower and upper bounds are model boundaries rather than empirical claims of universal FX volatility ranges. They prevent the public validation example from silently producing degenerate or explosive inputs.

## Volatility floor

The scenario surface uses an absolute volatility floor of `0.01`.

The floor is classified as a numerical-domain control. It prevents non-positive volatility inputs after a negative volatility shock.

The floor is not a market calibration assumption and does not imply that one-percent volatility is economically representative.

Automated tests verify activation below the floor, preservation above the floor and rejection of non-finite values.

## Monitoring thresholds

The public monitoring layer evaluates:

- relative spot movement
- absolute realised-volatility change
- absolute domestic-rate change
- absolute foreign-rate change
- relative put-call parity gap
- call-delta sign changes
- vega sign changes

The quantitative thresholds are stored in the governance contract and are applied consistently by `scripts/run_fx_option_monitoring.py`.

A threshold breach generates an alert artifact and changes the model status to `REVALIDATION_REQUIRED`.

## Ownership

The contract records:

- model owner
- validation owner
- escalation owner
- review frequency
- alert artifact
- revalidation status

The public repository produces auditable alert evidence. Integration with production messaging, ticketing or incident-management platforms remains outside the repository scope.

## Market benchmark boundary

Market-quote benchmarking remains `OPEN_NO_PUBLIC_QUOTE_DATA`.

Monitoring internal model outputs does not demonstrate market calibration.

## Model-use boundary

These controls support governed validation review.

They do not constitute production approval, trading limits, regulatory materiality thresholds or external operational alerting.

## Governed volatility data source

The realised-volatility estimator uses the historical observations contained in `data/official/raw/bcb_usd_brl_sgs1.json`.

The source identifier `BCB_SGS_1` is a governed source identity, not a DataFrame column name. The validation script therefore resolves that identifier to the official cached BCB history and parses the `valor` field as BRL per USD.

Generic panel columns are not substituted for the governed USD/BRL history. This prevents source identifiers from being confused with physical column names and prevents unrelated exchange-rate series from entering the volatility estimate.

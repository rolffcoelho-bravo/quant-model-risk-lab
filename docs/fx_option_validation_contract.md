# FX Option Validation Contract

## Purpose

This contract governs the market inputs, implementation benchmark, numerical controls and model-use boundaries of the USD/BRL vanilla FX option layer.

## Market-input identity

The pricing layer must fail closed unless all source identities and unit conventions are explicit.

| Input | Required source | Required model unit |
|---|---|---|
| USD/BRL spot | BCB SGS series 1 | BRL per USD |
| BRL domestic-rate proxy | BCB SGS series 432 | Annual decimal |
| USD foreign-rate proxy | FRED DGS1 | Annual decimal |

The previous generic panel-selection logic is not permitted for USD/BRL pricing because semantic or scale-based column selection can confuse unrelated currencies or rates.

## Date alignment

The governed as-of date is the latest valid DGS1 observation in the repository curve layer.

The BCB spot and Selic observations must occur on or before that date. Any input more than fourteen calendar days stale is rejected.

## Strike construction

The validation strike is the covered-interest-parity model forward:

\[
K = S_0 \exp((r_d-r_f)T)
\]

The forward-to-spot relationship must reconcile exactly with the supplied rate differential and maturity.

A large strike-to-spot ratio is not accepted solely because the pricing formula reproduces it. The source identity and unit contract must pass first.

## Put-call parity tolerance

The parity status uses a relative numerical tolerance scaled by the call premium.

The tolerance is a floating-point implementation control, not a business-materiality threshold and not evidence of market accuracy.

Business materiality requires a separate governed threshold and remains outside this public validation layer.

## Independent implementation challenger

The Garman-Kohlhagen premium is compared with the mathematically equivalent forward-based Black-76 representation.

Analytic delta, gamma and vega are also compared with central finite-difference estimates.

The challenger must pass before the generated evidence is accepted for validation review.

## Market benchmark boundary

The repository does not contain public, dated and executable USD/BRL option quote data across strikes and maturities.

Market-quote comparison therefore remains open.

An implementation challenger cannot be represented as a market benchmark.

## Model-use boundary

Permitted use:

- reproducible model-validation review
- implementation equivalence testing
- numerical Greek verification
- parity and scenario analysis

Prohibited use:

- formal production approval
- automated trading
- smile-calibrated pricing
- barrier or path-dependent valuation
- regulatory capital or valuation adjustment decisions
- claims of market calibration without quote evidence
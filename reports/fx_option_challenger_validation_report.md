# FX Option Challenger Validation Report

## Purpose

This control compares the repository Garman-Kohlhagen implementation with an independently formulated forward-based Black-76 challenger.

It also compares analytic delta, gamma and vega with central finite-difference estimates.

## Governed market inputs

- Currency pair: `USD/BRL`
- Quote convention: `BRL per USD`
- Spot source: `BCB_SGS_1`
- Domestic-rate source: `BCB_SGS_432`
- Foreign-rate source: `FRED_DGS1`
- Input contract: `PASS`

## Implementation benchmark

Overall challenger status: **PASS**

| model_id        | option_type   |   gk_premium_brl |   black76_challenger_premium_brl |   price_relative_error |   analytic_delta |   finite_difference_delta |   delta_relative_error |   analytic_gamma |   finite_difference_gamma |   gamma_relative_error |   analytic_vega |   finite_difference_vega |   vega_relative_error | implementation_challenger_status   | market_quote_benchmark_status   |
|:----------------|:--------------|-----------------:|---------------------------------:|-----------------------:|-----------------:|--------------------------:|-----------------------:|-----------------:|--------------------------:|-----------------------:|----------------:|-------------------------:|----------------------:|:-----------------------------------|:--------------------------------|
| QMRL-FX-OPT-001 | call          |           376962 |                           376962 |            1.54413e-15 |           517113 |                    517113 |            9.68667e-09 |           387781 |                    387781 |            3.01643e-08 |     1.97253e+06 |              1.97253e+06 |           3.27422e-12 | PASS                               | OPEN_NO_PUBLIC_QUOTE_DATA       |
| QMRL-FX-OPT-001 | put           |           376962 |                           376962 |            7.72064e-16 |          -444157 |                   -444157 |            1.12804e-08 |           387781 |                    387781 |            3.07265e-08 |     1.97253e+06 |              1.97253e+06 |           3.27422e-12 | PASS                               | OPEN_NO_PUBLIC_QUOTE_DATA       |

## Market benchmark boundary

Market-quote benchmark status: **OPEN_NO_PUBLIC_QUOTE_DATA**

The implementation benchmark verifies internal pricing equivalence and numerical Greeks. It does not demonstrate agreement with traded USD/BRL option quotes or a market volatility surface.

Market-quote benchmarking remains an open validation gate and must not be inferred from the implementation challenger.

## Model-use decision

The corrected layer is available for governed validation review of vanilla European USD/BRL option pricing.

It is not production approved and does not support smile-calibrated, barrier, path-dependent or automated trading use.

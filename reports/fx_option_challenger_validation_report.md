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
| QMRL-FX-OPT-001 | call          |           207429 |                           207429 |            2.24491e-15 |           500708 |                    500707 |            1.82557e-08 |           707696 |                    707696 |            6.83271e-08 |     1.97878e+06 |              1.97878e+06 |           1.05591e-11 | PASS                               | OPEN_NO_PUBLIC_QUOTE_DATA       |
| QMRL-FX-OPT-001 | put           |           207429 |                           207429 |            2.24491e-15 |          -460562 |                   -460562 |            1.98513e-08 |           707696 |                    707696 |            7.78775e-08 |     1.97878e+06 |              1.97878e+06 |           1.15028e-11 | PASS                               | OPEN_NO_PUBLIC_QUOTE_DATA       |

## Market benchmark boundary

Market-quote benchmark status: **OPEN_NO_PUBLIC_QUOTE_DATA**

The implementation benchmark verifies internal pricing equivalence and numerical Greeks. It does not demonstrate agreement with traded USD/BRL option quotes or a market volatility surface.

Market-quote benchmarking remains an open validation gate and must not be inferred from the implementation challenger.

## Model-use decision

The corrected layer is available for governed validation review of vanilla European USD/BRL option pricing.

It is not production approved and does not support smile-calibrated, barrier, path-dependent or automated trading use.

# Curve Pricing Validation Harness

## Executive summary

This report validates a simple curve-based pricing workflow using official public U.S. Treasury curve data already stored in the repository.

The harness transforms observed Treasury curve nodes into interpolated zero rates, discount factors, bond cashflows, a fixed-rate bond value, DV01 and parallel-shock valuation evidence.

This is not a production pricing engine. It is a transparent model-risk validation harness designed to show how valuation inputs, assumptions and sensitivities can be reviewed.

## Latest curve date

2026-07-06

## Instrument under review

| Field | Value |
|---|---|
| Instrument type | Fixed-rate bond validation instrument |
| Face value | 100 |
| Maturity | 5 years |
| Coupon rate | 0.042100 |
| Coupon frequency | Semiannual |
| Curve source | Official public Treasury curve nodes |
| Pricing method | Interpolated zero curve with continuous discounting |

## Discount curve

| maturity_years | interpolated_zero_rate_percent | discount_factor_continuous |
| --- | --- | --- |
| 1.000000 | 3.950000 | 0.961270 |
| 2.000000 | 4.130000 | 0.920719 |
| 3.000000 | 4.156667 | 0.882762 |
| 5.000000 | 4.210000 | 0.810179 |
| 7.000000 | 4.318000 | 0.739146 |
| 10.000000 | 4.480000 | 0.638905 |
| 30.000000 | 4.990000 | 0.223801 |

## Bond cashflows

| payment_number | payment_time_years | cashflow |
| --- | --- | --- |
| 1.000000 | 0.500000 | 2.105000 |
| 2.000000 | 1.000000 | 2.105000 |
| 3.000000 | 1.500000 | 2.105000 |
| 4.000000 | 2.000000 | 2.105000 |
| 5.000000 | 2.500000 | 2.105000 |
| 6.000000 | 3.000000 | 2.105000 |
| 7.000000 | 3.500000 | 2.105000 |
| 8.000000 | 4.000000 | 2.105000 |
| 9.000000 | 4.500000 | 2.105000 |
| 10.000000 | 5.000000 | 102.105000 |

## Valuation result

| Metric | Value |
|---|---|
| Base clean-price proxy | 99.828614 |
| DV01 | 0.045517 |

## Parallel shock table

| parallel_shift_bp | bond_price | price_change | price_change_percent |
| --- | --- | --- | --- |
| -100.000000 | 104.492024 | 4.663410 | 4.671417 |
| -50.000000 | 102.132166 | 2.303552 | 2.307507 |
| -25.000000 | 100.973438 | 1.144824 | 1.146789 |
| 0.000000 | 99.828614 | 0.000000 | 0.000000 |
| 25.000000 | 98.697524 | -1.131089 | -1.133031 |
| 50.000000 | 97.580002 | -2.248612 | -2.252473 |
| 100.000000 | 95.384997 | -4.443617 | -4.451246 |

## Model-risk interpretation

A model validator is not only checking whether a price was produced. The review must ask whether the market data are traceable, whether interpolation is documented, whether discounting assumptions are explicit, whether sensitivity behaves in the expected direction and whether valuation outputs can be reproduced.

This harness creates that evidence from public official data:

1. Curve nodes are read from the official-data pipeline.
2. Interpolated zero rates are generated at review maturities.
3. Discount factors are calculated transparently.
4. Bond cashflows are listed.
5. Base price and DV01 are computed.
6. Parallel rate shocks are applied.
7. Outputs are stored as reproducible CSV and markdown evidence.

## Limitation

The harness is intentionally simple. It does not claim to reproduce proprietary bank curve construction, bootstrapping, collateral curves, XVA, multi-curve frameworks, inflation swap curves or production derivative libraries.

Its purpose is public model-risk evidence: transparent inputs, explicit assumptions, sensitivity checks, reproducible outputs and tests.

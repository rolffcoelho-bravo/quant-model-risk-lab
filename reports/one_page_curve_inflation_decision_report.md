# One-Page Curve and Inflation Decision Report

## Decision state: Watch

**Curve date:** 2026-07-06  
**Inflation date:** 2026-07-07  
**Decision flags:** +100bp valuation loss above 4 percent

![Curve and inflation decision map](figures/curve_inflation_decision_map.png)

## Core metrics

| Metric | Value |
|---|---:|
| 1Y Treasury | 3.950% |
| 2Y Treasury | 4.130% |
| 5Y Treasury | 4.210% |
| 10Y Treasury | 4.480% |
| 30Y Treasury | 4.990% |
| 2s10s slope | 0.350 pp |
| 5s30s slope | 0.780 pp |
| 10Y breakeven inflation | 2.250% |
| Validation bond price | 99.8286 |
| DV01 | 0.045517 |
| +50bp valuation impact | -2.252% |
| +100bp valuation impact | -4.451% |

## Model-risk interpretation

- **Curve input risk:** The term-structure shape defines the valuation environment. A negative or unstable 2s10s slope raises the need to challenge interpolation, extrapolation and rate-sensitivity assumptions.
- **Inflation input risk:** The 10Y breakeven rate is a direct public inflation-compensation input. Elevated inflation compensation increases the importance of inflation-linked valuation review and scenario testing.
- **Valuation sensitivity:** The +50bp and +100bp shock losses convert curve movement into pricing impact. This is the cleanest validation bridge between market data and model-output review.
- **Decision use:** The report is not a forecast. It is an evidence object for model validation, revalidation prioritization, sensitivity review and monitoring escalation.

## Bank implication

Prioritize review of curve construction, input lineage, interpolation assumptions, DV01 behavior, shock sensitivity and inflation-linked valuation inputs. The validation question is whether pricing outputs remain stable and explainable under rate and inflation stress.

## Investor implication

The risk profile is dominated by curve sensitivity and inflation compensation. The key question is not direction alone, but whether valuation loss under rate shocks is consistent with duration, curve shape and inflation-pressure assumptions.

## Validator challenge

Challenge the curve source, missing-data treatment, interpolation method, discounting convention, shock design, inflation proxy, sensitivity stability and whether the current environment sits outside the model-development distribution.

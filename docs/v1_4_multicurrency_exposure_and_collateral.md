# v1.4 Gate 2 — Multi-Currency Exposure and Collateral

## Purpose

Gate 2 extends the canonical Gate 1 portfolio into a governed multi-currency exposure layer. It converts trade and collateral values into the portfolio reporting currency, applies currency-specific discount curves, preserves pathwise lineage, and exposes currency attribution and independent challenge evidence.

## Conversion-before-netting rule

For trade \(i\), path \(p\), and time \(t\), reporting-currency value is

\[
V^R_{i,p,t}
=
V^{C_i}_{i,p,t}
\times
FX_{C_i\rightarrow R,p,t}.
\]

Converted trade values are then aggregated inside the legal netting set. The implementation prohibits netting local-currency values before conversion because that would mix economically different units and conceal FX-driven exposure.

Collateral held in currency \(K\) is converted consistently:

\[
C^R_{p,t}
=
C^K_{p,t}
\times
FX_{K\rightarrow R,p,t}.
\]

Under the held-positive convention, pathwise exposure is

\[
E_{p,t}
=
\sum_i V^R_{i,p,t}
-
\sum_j C^R_{j,p,t},
\]

with positive and negative exposure reported as separate non-negative magnitudes.

## FX governance

The FX quote convention is target-currency units per one source-currency unit. Gate 2 permits:

- direct conversion;
- inverse conversion;
- explicitly governed triangular conversion.

Missing paths are blocking errors. Extrapolation is forbidden. All quotes must share time and path dimensions. When a direct quote and triangular path coexist, the triangulation report measures their absolute difference against a governed tolerance.

## Currency-specific curves

Gate 2 introduces typed discount, funding, and collateral-remuneration curves. Discount factors are used for discounted exposure profiles. Funding curves are represented and validated for later use but do not create FVA, MVA, or KVA calculations in this gate.

## Collateral remuneration and switching

Collateral balances may be accrued using a declared remuneration-rate profile. Currency-switch analysis converts balances so scenario reporting value is preserved. Gate 2 does not perform collateral optimization, cheapest-to-deliver selection, initial-margin calculation, or legal agreement interpretation.

## Currency attribution

Each netting-set result retains expected reporting-currency contributions by source currency. The attribution reconciles to expected net value within the absolute tolerance declared in the Gate 2 contract.

## Independent challenger

The primary engine and challenger use separate aggregation paths. The challenger independently loops over netting sets, trades, paths, times, and collateral balances and reconciles:

- expected positive exposure;
- expected negative exposure;
- discounted expected positive exposure;
- discounted expected negative exposure.

## Single-currency compatibility

When every trade, collateral balance, curve, and reporting unit uses the same currency, FX conversion is the identity. The Gate 2 result must reduce to direct v1.3-compatible netting and collateral exposure within governed tolerance.

This is a compatibility contract, not a modification of the frozen v1.3.0 release evidence.

## Validation evidence

Gate 2 includes:

- strict domain and dimension tests;
- direct, inverse, and triangular FX benchmarks;
- collateral remuneration tests;
- collateral-currency switching;
- conversion-before-netting tests;
- discounting tests;
- attribution reconciliation;
- independent challenger reconciliation;
- canonical Gate 1 snapshot compatibility;
- normalized SHA-256 release evidence.

## Model boundaries

Gate 2 does not introduce:

- live or proprietary market data;
- stochastic FX calibration;
- currency-basis calibration;
- MVA;
- KVA;
- incremental XVA;
- production collateral optimization;
- regulatory approval;
- production approval.

The next approved gate is Gate 3: initial margin and Margin Valuation Adjustment.

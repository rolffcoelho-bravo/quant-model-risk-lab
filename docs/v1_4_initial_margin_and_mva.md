# v1.4 Gate 3 — Initial Margin and Margin Valuation Adjustment

## Purpose

Gate 3 adds transparent public initial-margin proxies and a separately attributable Margin Valuation Adjustment. It builds on validated portfolio ingestion and multi-currency exposure without changing the frozen v1.3 release.

## Approved initial-margin proxies

The historical-simulation-style proxy applies a governed quantile to pathwise value losses over the margin period of risk. The parametric proxy applies a normal quantile to a sensitivity-covariance quadratic form with square-root-of-time scaling.

Every output is labelled `PUBLIC_PROXY_NOT_SIMM_OR_CCP`. The repository does not claim SIMM certification, CCP replication, legal enforceability, production approval, or regulatory approval.

## Posted and received margin

Posted and received profiles are reported separately. Posted initial margin is treated as segregated. Received-margin funding benefit is recognized only when the policy explicitly marks received margin as reusable.

## MVA

For each time interval, the engine integrates discounted, survival-weighted posted margin against the positive difference between the currency funding rate and collateral remuneration rate. The public convention clamps a negative effective spread to zero.


\[
MVA = \int_0^T DF(0,t)\,S(0,t)\,\max(f_F(t)-r_{IM}(t),0)\,IM^P_t\,dt
\]

Received-margin benefit is disclosed separately and net MVA reconciles as posted MVA less reusable received-margin benefit.

## Separation from FVA

MVA is never silently embedded in FVA. The result schema contains an enforced `fva_embedded: false` boundary and tests the component identity directly.

## Validation evidence

Gate 3 includes confidence, MPOR, volatility, funding, remuneration, and margin-scale sensitivities; deterministic benchmarks; time-bucket and currency attribution; concentration diagnostics; and an independent loop challenger.

## Boundaries

KVA, incremental XVA, production initial-margin approval, regulatory approval, live market data, certified SIMM, and CCP margin replication remain outside Gate 3.

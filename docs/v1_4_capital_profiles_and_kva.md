# v1.4 Gate 4 — Capital Profiles and KVA

## Purpose

Gate 4 introduces transparent public capital profiles and Capital Valuation Adjustment without making regulatory or production claims. The implementation converts validated expected exposure into an exposure-at-default proxy, applies visible risk-weight, capital-ratio, maturity, and stress multipliers, and integrates the resulting capital profile against discount, survival, and hurdle-rate term structures.

## Quantitative definition

For netting set \(n\) and time \(t\):

\[
EAD_{n,t}=EE_{n,t}\times m_{EAD}
\]

\[
K_{n,t}=EAD_{n,t}\times RW_n\times c\times m_M\times m_S
\]

\[
KVA_n=\int_0^T DF(t)S(t)h(t)K_{n,t}\,dt
\]

Endpoint and trapezoidal integration are supported. A zero hurdle-rate term structure must produce zero KVA.

## Attribution and diagnostics

KVA remains attributable by counterparty, netting set, trade, currency, and time bucket. The implementation also reports concentration HHI, maximum netting-set share, peak capital, standardized sensitivities, and independent challenger reconciliation.

## Model boundaries

All outputs carry `PUBLIC_CAPITAL_PROXY_NOT_REGULATORY_APPROVAL`. The release does not claim SA-CCR, IMM, Basel, regulatory-capital, economic-capital, or production approval. Institution-specific legal, regulatory, accounting, funding, and capital policies remain outside the public model boundary.

## Promotion rule

Gate 4 may pass only when capital profiles, KVA integration, attribution, sensitivities, benchmarks, and the independent challenger reconcile, while regulatory and production approval remain false. Incremental and marginal XVA remain outside this gate.

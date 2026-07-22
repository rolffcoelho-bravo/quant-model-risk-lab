# XVA Counterparty Credit Calibration

## Gate 4 objective

Gate 4 establishes independently validated credit-spread, hazard-rate, survival-probability, default-probability, recovery, LGD, and proxy controls before exposure profiles are integrated into CVA or DVA.

Gate 4 is not a CVA, DVA, or FVA integration layer. It produces governed credit term structures only.

## Risk-neutral versus historical separation

Every quote and curve records its probability measure. Risk-neutral market-implied curves and historical default-frequency estimates cannot be silently mixed. Market-implied XVA curves use the risk-neutral measure; historical curves remain separate validation or stress evidence.

## Credit quote governance

Each quote records an identifier, obligor, tenor, spread, as-of date, source, quote type, probability measure, currency, and seniority. Controls reject duplicate tenors, stale or future-dated observations, missing required tenors, mixed measures, mixed currencies, and mixed seniorities.

CDS spreads are the primary calibration input. Bond spreads may be admitted only as an explicitly approved proxy because Gate 4 does not decompose liquidity, funding, and credit components.

## Piecewise-constant hazard calibration

The calibration solves one non-negative hazard segment at a time. Each node reprices its governed par spread using a discrete premium leg, accrued premium on default, and a protection leg scaled by LGD.

For hazard rate h(t), survival is

S(t) = exp(- integral from 0 to t of h(u) du).

Cumulative default probability is 1 - S(t), and marginal interval default probability is the decline in survival between adjacent nodes.

The curve fails closed when a quote structure would require a negative incremental hazard. Source-quote repricing, non-negative hazards, monotone survival, and probability bounds are promotion requirements.

## Interpolation and extrapolation

Piecewise-constant hazard implies linear cumulative hazard within each tenor interval. Extrapolation is either forbidden or explicitly controlled through a flat terminal hazard. Silent extrapolation is not allowed.

## Recovery and LGD governance

Recovery is bounded in [0, 1), matched to obligor and seniority, dated, sourced, and subject to staleness controls. LGD is defined as 1 - recovery. Spread and recovery sensitivities are mandatory calibration evidence.

## Counterparty and own-credit separation

Counterparty and own-credit curves are separate objects with separate obligors, roles, sources, and calibration evidence. One curve cannot be reused for both CVA and DVA without an explicit governed mapping.

## Proxy hierarchy

The controlled Proxy hierarchy is:

1. direct obligor quote
2. parent quote
3. sovereign proxy
4. sector proxy

Eligibility requires matching tenor, measure, currency, and seniority, together with current data and a recorded basis adjustment. Any non-direct selection requires human review.

## Deterministic benchmark framework

The locked benchmark suite covers analytic flat-hazard survival, piecewise quote repricing, PD reconciliation, stale-data rejection, missing-tenor rejection, proxy hierarchy, forbidden extrapolation, spread sensitivity, recovery sensitivity, and deterministic evidence hashing.

## Validation boundaries

Gate 4 does not include default dependence, wrong-way risk, exposure-credit integration, CVA, DVA, FVA, legal enforceability evidence, production market-data feeds, or production approval.

## Promotion rule

Gate 4 is complete only when all credit benchmarks pass, all prior XVA gates remain green, the complete repository suite passes, the required GitHub Actions check passes, and human review approves the pull request.

Gate 5 will integrate independently validated exposure and credit term structures into CVA, DVA, and FVA attribution.

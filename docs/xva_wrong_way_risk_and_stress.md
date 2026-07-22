# XVA Wrong-Way Risk Dependence and Stress Scenarios

## Gate 6 objective

Gate 6 introduces controlled dependence between market-driven exposure and counterparty credit deterioration while preserving the independent Gate 5 result as the mandatory baseline.

The implementation is not a production stress engine. It is a public validation layer for dependence assumptions, scenario governance, stressed attribution, and reproducible evidence.

## Gaussian copula baseline

A one-factor Gaussian copula links a standardized path-level exposure score to conditional default probabilities. Positive correlation represents wrong-way risk; negative correlation represents right-way risk; zero correlation reproduces the independent result.

Conditional default probabilities are integrated against pathwise MPOR exposure. The base CVA, dependence-adjusted CVA, uplift, uplift ratio, netting-set attribution, tail-exposure share, and concentration HHI remain separately observable.

## Baseline preservation

Gate 6 never replaces the Gate 5 independent XVA result. Evidence must retain distinct values for:

- independent baseline
- wrong-way-risk adjustment
- right-way-risk comparison
- deterministic stress scenario
- total stressed adjustment

## Stress-channel governance

Supported channels are systemic, sector, sovereign, commodity, FX, rates, and idiosyncratic. Every scenario requires an as-of date, calibration source, rationale, severity, plausibility score, and approval status.

Severe scenarios and low-plausibility assumptions require explicit human approval. Correlations and correlation shifts are bounded. Specific wrong-way risk cannot bypass human review.

## Stressed attribution

Stress scenarios can modify:

- positive and negative exposure
- counterparty and own hazard rates
- borrowing and lending funding spreads
- discount rates
- dependence correlation

CVA, DVA, FCA, FBA, FVA, and total-adjustment deltas reconcile by netting set and portfolio. The sign convention remains:

\[
\Delta XVA = -\Delta CVA + \Delta DVA - \Delta FCA + \Delta FBA
\]

## Locked benchmarks

Eleven deterministic benchmarks cover independence, wrong-way uplift, right-way reduction, near-perfect dependence, hazard stress, exposure stress, funding stress, discount stress, component reconciliation, governance rejection, and deterministic evidence hashes.

## Validation boundaries

Gate 6 does not provide production correlation calibration, stochastic intensity estimation, replacement-closeout recursion, legal enforceability evidence, enterprise stress libraries, capital aggregation, or production approval.

The next gate is independent challenger expansion, model stability, and promotion governance.

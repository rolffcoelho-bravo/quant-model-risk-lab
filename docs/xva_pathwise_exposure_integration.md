# XVA Pathwise Exposure Integration

## Gate 3 objective

Gate 3 connects the Gate 2 future-value cube to the Gate 1 legal netting and collateral framework.

It produces governed pathwise exposure profiles by legal netting set, counterparty, and portfolio while preserving explicit model-risk boundaries.

Gate 3 is not a counterparty credit calibration layer. It does not introduce PD, LGD, CVA, DVA, FVA, wrong-way-risk dependence, or production legal opinions.

## Pathwise trade-to-netting-set allocation

Every trade in the future-value cube must be allocated exactly once to a governed netting set.

The allocation layer rejects:

- unallocated trades
- unknown trade identifiers
- duplicate cross-set membership
- inconsistent netting-set identifiers
- silent cross-netting across legal agreements

The pathwise netting cube is indexed by path, time, and netting set.

For eligible legal sets, trade future values are summed before positive and negative exposure are calculated.

For noneligible treatment, gross positive and negative trade values are preserved. Multi-trade noneligible sets cannot receive a shared collateral agreement in Gate 3.

## Collateral state by path

The Gate 1 collateral state process is executed independently for every simulated path and governed netting set.

The resulting collateral cube contains:

- settled face balance
- effective balance after haircut
- transfer called
- pending face balance

The implementation retains thresholds, minimum transfer amounts, independent amounts, initial margin, haircuts, rounding, call frequency, settlement lag, margin period of risk, and agreement directionality.

Missing agreement references fail closed.

## Exposure integration

For clean netting-set value \(V_{p,t,n}\) and effective collateral \(C_{p,t,n}\):

\[
X_{p,t,n} = V_{p,t,n} - C_{p,t,n}
\]

\[
E^{+}_{p,t,n} = \max(X_{p,t,n}, 0)
\]

\[
E^{-}_{p,t,n} = \max(-X_{p,t,n}, 0)
\]

For noneligible multi-trade treatment without collateral, gross positive and negative trade values are retained.

## Margin period of risk

MPOR targets are date based rather than inferred from a fixed number of array steps.

For each observation date, the engine selects the first future grid date on or after the governed MPOR endpoint. Future clean value is then compared with collateral available at the current observation date.

## No cross-netting across legal sets

Portfolio and counterparty exposure are aggregated by summing positive and negative exposure across legal netting sets.

Values from separate legal agreements are never offset during exposure aggregation.

Potential future exposure is calculated on the pathwise sum of legal-set positive exposures, not by summing independent set-level quantiles.

## Exposure metrics

Gate 3 produces:

- expected positive exposure by netting set
- expected negative exposure by netting set
- PFE by netting set
- effective EPE by netting set
- MPOR expected positive exposure
- counterparty exposure profiles
- portfolio exposure profiles
- portfolio EPE
- portfolio ENE
- portfolio peak PFE

## Reconciliation and challenger controls

The integration layer independently reconciles:

- trade values to netting-set clean values
- clean value minus collateral to net exposure
- positive exposure minus negative exposure to net exposure
- vectorized exposure calculations to an explicit loop challenger

All controls must remain within the governed numerical tolerance.

## Deterministic benchmark framework

Ten locked cases cover:

1. offsetting trades within one legal netting set
2. separate legal sets without cross-netting
3. perfect collateralization
4. threshold residual exposure
5. minimum-transfer-amount discontinuity
6. settlement-lag and pending-transfer exposure
7. haircut face-value compensation
8. margin-period-of-risk exposure
9. counterparty aggregation
10. reconciliation and content-addressed evidence

## Machine-readable evidence

The exposure manifest records:

- path count
- time count
- netting-set count
- legal-set identifiers
- counterparty identifiers
- PFE quantile
- portfolio EPE
- portfolio ENE
- peak PFE
- SHA-256 content hash

## Validation boundaries

Gate 3 does not provide:

- counterparty-specific PD term structures
- LGD calibration
- default dependence
- wrong-way-risk modeling
- CVA, DVA, or FVA integration
- legal enforceability opinions
- production collateral feeds
- enterprise exposure limits
- production approval

## Promotion rule

Gate 3 is complete only when:

- all integration benchmarks pass
- all Gate 1 and Gate 2 tests remain green
- the complete repository test suite passes
- pull-request CI passes
- post-merge main CI passes
- human review approves the merge

The next phase is Gate 4: counterparty credit calibration and default-probability term structures.

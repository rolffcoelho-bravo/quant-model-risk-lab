# XVA Exposure Simulation Architecture

## Gate 1 objective

Gate 1 establishes the deterministic architecture and control contracts required before stochastic future-exposure simulation is introduced.

The implementation converts the existing static XVA module into a backward-compatible package and adds explicit controls for:

- time-grid construction
- netting-set representation
- collateral agreement mechanics
- collateral state transitions
- collateralized exposure
- expected positive and negative exposure
- potential future exposure
- margin-period-of-risk views
- deterministic benchmark evidence

Gate 1 is not a production exposure engine. It is a public, reproducible validation foundation.

## Design principles

1. **Preserve existing evidence**  
   The public v0.9 XVA functions remain import-compatible through `qmrl.xva`.

2. **Separate legal structure from numerical aggregation**  
   Netting eligibility is governed by a netting-set contract rather than inferred from values.

3. **Model collateral through time**  
   Collateral calls, pending transfers, settlement lag, thresholds, minimum transfer amounts, haircuts, and directionality are represented as a state process.

4. **Lock deterministic reference cases first**  
   Stochastic simulation cannot be promoted until analytically understandable cases pass.

5. **Retain human approval**  
   Passing code and benchmarks does not grant production approval or legal enforceability.

## Time-grid control

The unified grid contains dates required for:

- valuation
- exposure observation
- margin calls
- collateral settlement
- margin-period-of-risk endpoints
- maturity

The grid is sorted, unique, deterministic, business-day adjusted, and represented with explicit date-role markers.

Gate 1 uses transparent ACT/365 year fractions and weekend-only business-day handling. Holiday calendars and institution-specific schedules remain later calibration controls.

## Netting-set representation

Each governed netting set contains:

- netting-set identifier
- counterparty identifier
- legal agreement identifier
- settlement currency
- explicit trade membership
- netting eligibility
- collateral agreement reference
- close-out convention
- wrong-way-risk classification
- effective date
- review date

A trade cannot be silently assigned to multiple incompatible netting sets. Counterparty and currency consistency are validated before aggregation.

Eligible sets aggregate to net clean value before positive and negative exposure are calculated. Noneligible sets retain gross positive and negative exposure.

## Collateral as a state process

Collateral is not treated as an instantaneous scalar deduction.

The Gate 1 collateral process includes:

- received and posted thresholds
- minimum transfer amount
- independent amount
- initial margin
- haircut
- transfer rounding
- call frequency
- settlement lag
- margin period of risk
- collateral currency
- remuneration rate metadata
- rehypothecation flag
- two-way, receive-only, and post-only directionality

The state records settled face balance, effective collateral after haircut, called transfer, and pending transfer balance.

## Exposure definitions

For clean portfolio value \(V_t\) and effective collateral \(C_t\):

\[
X_t = V_t - C_t
\]

\[
E_t^{+} = \max(X_t, 0)
\]

\[
E_t^{-} = \max(-X_t, 0)
\]

Across paths, Gate 1 provides:

- expected positive exposure profile
- expected negative exposure profile
- PFE profile at a governed quantile
- effective EPE profile
- time-averaged EPE
- time-averaged ENE
- discounted EPE
- peak PFE

The MPOR control evaluates a future clean value against collateral available at the current observation point.

## Deterministic benchmark framework

The benchmark contract contains ten locked cases:

1. single positive-value trade without collateral
2. perfect collateralization
3. threshold-only agreement
4. minimum-transfer-amount discontinuity
5. settlement-lag exposure
6. margin-period-of-risk exposure
7. offsetting trades in one eligible netting set
8. identical trades under gross or noneligible treatment
9. collateral haircut impact
10. negative portfolio value and ENE generation

Each benchmark contains:

- benchmark identifier
- case type
- governed inputs
- expected output
- numerical tolerance
- PASS or FAIL result

## Configuration format

The `.yml` contracts use JSON syntax. JSON is valid YAML 1.2, which allows the repository to keep human-readable contracts without introducing another runtime parser dependency.

## Validation boundaries

Gate 1 does not include:

- stochastic market-factor simulation
- counterparty-specific PD or LGD term structures
- wrong-way-risk dependence calibration
- legal opinions confirming enforceability
- production collateral feeds
- multi-currency collateral optimization
- enterprise workflow integration
- production approval

## Promotion rule

Gate 1 may be treated as complete only when:

- all deterministic benchmark cases pass
- legacy XVA tests remain green
- new contract, time-grid, netting, collateral, and exposure tests pass
- the complete repository suite passes
- the required GitHub Actions check passes
- human review approves the pull request

The next gate is scenario-path and future-value simulation.

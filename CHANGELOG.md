# Changelog


## [1.2.0] - 2026-07-22

### Added

- governed GenAI architecture and public operating boundaries
- release-level validation matrix
- machine-readable v1.2 release manifest
- formal release notes
- repository citation metadata
- release-contract tests

### Changed

- updated the root README around the implemented model-risk platform
- removed obsolete release framing and conflicting test counts
- consolidated FX, XVA, monitoring, GenAI, CI, and lifecycle evidence
- separated implemented controls from open validation gates
- elevated CI and branch protection into the public governance narrative

### Validation

- Python 3.12 GitHub Actions validation is required on `main`
- complete deterministic test collection: `136` tests
- JUnit evidence is retained by the CI workflow
- the USD/BRL market-option quote benchmark remains explicitly open

### Governance boundary

This release does not grant production approval, regulatory approval, or market-calibration certification.

All notable repository changes are documented here.

## [Unreleased]




### Gate 5 - CVA, DVA, and FVA integration and attribution

- CVA, DVA, FCA, FBA, FVA, and total-adjustment integration
- bilateral first-to-default survival controls
- governed discount and funding curves
- time-bucket, netting-set, counterparty, portfolio, and trade attribution
- independent loop challenger and reconciliation
- spread, recovery, funding, and discount sensitivities
- deterministic calculation manifests and eleven locked benchmarks
- Gate 5 validation across `266` collected tests

### Gate 4 - Counterparty credit calibration and PD/LGD term structures

- Added governed credit-spread quote, recovery, LGD, and proxy contracts.
- Added piecewise-constant hazard calibration with source-quote repricing.
- Added survival, cumulative default, and marginal default-probability term structures.
- Added explicit risk-neutral and historical probability-measure separation.
- Added counterparty and own-credit curve roles.
- Added stale-data, missing-tenor, bond-proxy, and extrapolation controls.
- Added direct, parent, sovereign, and sector proxy hierarchy with mandatory human review for non-direct selections.
- Added parallel spread and recovery sensitivity evidence.
- Added deterministic credit-curve manifests and ten locked Gate 4 benchmarks.
- Gate 4 and all prior XVA gates validated across `239` collected tests.
- Gate 4 remains outside CVA, DVA, FVA, wrong-way-risk, legal-enforceability, and production-approval scope.

### Gate 3 - Pathwise netting, collateral, and exposure integration

### Gate 3 - Pathwise netting, collateral, and exposure integration

#### Added

- pathwise trade allocation to governed legal netting sets
- collateral-state simulation across paths and netting sets
- date-based margin-period-of-risk exposure
- legal-set, counterparty, and portfolio exposure aggregation
- EE, EPE, ENE, PFE, effective EPE, and peak-PFE evidence
- independent reconciliation and content-addressed manifests
- ten locked Gate 3 integration benchmarks

#### Validation

- Gate 3 targeted tests: PASS
- Gate 1, Gate 2, and legacy XVA tests remain compatible
- complete collected test surface: `211` tests

#### Boundaries

Gate 3 does not introduce counterparty PD/LGD calibration, default dependence, wrong-way risk, CVA, DVA, FVA, legal enforceability evidence, or production approval.

### Gate 2 — Scenario-Path and Future-Value Simulation

#### Added

- governed risk-factor and dependence contracts
- PCG64 seed and antithetic random-number controls
- correlated GBM FX and Vasicek short-rate scenario paths
- immutable scenario and future-value cubes
- SHA-256 scenario reproducibility manifests
- pathwise FX-forward and zero-coupon valuation adapters
- Monte Carlo convergence diagnostics
- analytical GBM and Vasicek moment challengers
- eight locked Gate 2 benchmark cases

#### Validation

- Gate 2 targeted tests: PASS
- Gate 1 and legacy XVA compatibility: PASS
- complete collected test surface: `183` tests

#### Boundaries

Gate 2 produces future clean-value paths only. It does not provide production calibration, credit integration, wrong-way-risk modelling, collateral integration, final XVA attribution, or production approval.

### Added

- XVA exposure-simulation architecture and model contract
- deterministic time-grid construction
- governed netting-set representation
- collateral agreement and state-process mechanics
- collateralized exposure and MPOR controls
- EPE, ENE, PFE, effective EPE, and discounted-EPE aggregation
- ten configuration-driven deterministic benchmarks
- backward-compatible migration of `qmrl.xva` from module to package

### Validation

- Gate 1 targeted tests: PASS
- legacy XVA tests remain compatible
- complete collected test surface: `157` tests

### Boundaries

Gate 1 does not provide stochastic market-factor simulation, counterparty-specific calibration, legal enforceability evidence, or production approval.

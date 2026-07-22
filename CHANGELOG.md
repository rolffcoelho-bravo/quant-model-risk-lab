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

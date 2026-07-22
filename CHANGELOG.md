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









## [1.3.0] - 2026-07-22

### Added

- complete XVA exposure simulation and counterparty risk validation platform
- scenario paths, future-value cubes, netting, collateral, exposure, and MPOR controls
- counterparty hazard, survival, PD, recovery, and LGD term structures
- CVA, DVA, FCA, FBA, FVA, attribution, sensitivities, and reconciliation
- wrong-way risk, stress scenarios, concentration, and tail diagnostics
- independent challengers, convergence, stability, and promotion governance
- decision-grade dashboard and lifecycle monitoring
- governed GenAI release challenge with repository artifact citations and mandatory human review
- final v1.3 release manifest, validation matrix, citation metadata, and release-contract tests

### Validation

- complete deterministic collection: `350` tests
- required pull-request check: `Python 3.12 validation`
- required post-merge main validation
- explicit human `RELEASE` approval before tag publication

### Boundaries

The release is public research software. It does not grant production or regulatory approval, assert legal enforceability, or represent confidential institutional calibration.

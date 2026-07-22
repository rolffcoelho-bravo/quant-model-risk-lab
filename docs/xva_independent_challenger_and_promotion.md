# XVA Independent Challengers, Stability, and Promotion Governance

## Gate 7 objective

Gate 7 determines whether the complete XVA stack is sufficiently reconciled, stable, reproducible, and governed to become a formal v1.3 release candidate.

Gate 7 creates a release-candidate evidence package. It does not publish v1.3 and does not grant production approval.

## Independent challenger layer

The challenger layer separates validation calculations from the primary Gate 5 and Gate 6 implementations. It provides:

- independent loop-based CVA and DVA integration
- independent funding-cost and funding-benefit integration
- scalar and vector component reconciliation
- soft and hard tolerance hierarchy
- materiality-aware discrepancy classification
- deterministic challenger evidence hashes
- mandatory root-cause evidence for `REMEDIATE` and `BLOCK`

No silent benchmark or challenger override is permitted.

## Stability and convergence

The governed diagnostics include:

- path-count convergence
- repeated-seed stability
- antithetic versus standard sampling dispersion
- time-grid refinement
- exposure-quantile stability
- wrong-way-risk correlation stability
- hazard-curve perturbation stability
- collateral-parameter stability
- attribution stability
- deterministic benchmark drift

Stability is separated from model uncertainty. A numerically stable estimate can still be economically sensitive and therefore require monitoring.

## Model-risk diagnostics

Gate 7 provides:

- sensitivity-driver ranking
- threshold and minimum-transfer-amount discontinuity flags
- benchmark-drift controls
- challenger disagreement scores
- concentration and tail-instability evidence references
- unstable component identification

## Promotion statuses

Every material component receives one status:

- `PASS`
- `PASS_WITH_MONITORING`
- `REMEDIATE`
- `BLOCK`

The portfolio cannot pass when there is any material component classified as `BLOCK`.

A material unresolved challenger discrepancy also forces `BLOCK`. Failed locked benchmarks, failed reproducibility, failed required CI, or incomplete evidence are hard blocking gates.

## Release-candidate evidence

The machine-readable release-candidate evidence package contains:

- candidate version
- component decisions
- hard-gate status
- unresolved findings
- diagnostic metrics
- evidence references
- repository commit
- collected test count
- prior gate manifests
- deterministic SHA-256 evidence hash

Human review remains mandatory. The Gate 7 package is not a production approval record.

## Promotion boundary

Gate 7 is complete only when:

- all locked Gate 7 benchmarks pass
- independent challenger discrepancies are within governed boundaries or explicitly remediated
- convergence and stability evidence meets minimum requirements
- no material component classified as `BLOCK`
- the full repository test suite passes
- the required GitHub Actions check passes
- the pull request receives explicit human approval

Gate 8 will add dashboards, lifecycle monitoring, governed GenAI challenge, final documentation, and v1.3 release consolidation.

# v1.4 Gate 8 — Release Consolidation

Gate 8 consolidates the validated v1.4 release line into a publication-grade model-risk evidence package. It does not change the primary quantitative methods approved in Gates 1–7.

## Release identity

\[
	ext{v1.4 Release Eligible}
\iff
igwedge_{g=0}^{7}	ext{Gate}_g	ext{ Validated}
\land 	ext{PR CI Pass}
\land 	ext{Post-Merge CI Pass}
\land 	ext{Human RELEASE Approval}.
\]

The public release status is `RELEASED_WITH_MONITORING`. This status preserves explicit monitoring obligations and does not grant production or regulatory approval.

## Consolidated capabilities

- canonical portfolio ingestion, referential integrity, lineage, and deterministic content hashing;
- multi-currency exposure, collateral remuneration, FX conversion, triangulation, and currency attribution;
- transparent historical-simulation-style and parametric initial-margin proxies with separately attributable MVA;
- transparent public capital proxies, capital profiles, and KVA under a non-regulatory boundary;
- full-revaluation incremental XVA, marginal diagnostics, Euler validity controls, and residual reconciliation;
- dependency-aware partial recalculation, deterministic caching, checkpoints, chunking, and parallel reproducibility;
- unified challengers, stability, drift, remediation governance, lifecycle monitoring, and advisory-only GenAI evidence challenge.

## Publication controls

The release package requires explicit `SQUASH` approval for the consolidation pull request and explicit `RELEASE` approval before the annotated `v1.4.0` tag and GitHub release are created.

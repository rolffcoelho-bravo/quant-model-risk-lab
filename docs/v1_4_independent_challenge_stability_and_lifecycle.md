# v1.4 Gate 7 — Independent Challenge, Stability, and Lifecycle Governance

Gate 7 consolidates independent challenge across every validated v1.4 layer and determines whether the release line is eligible to enter final consolidation. It does not change primary quantitative methods, approve production use, grant regulatory approval, or create the v1.4 release tag.

## Scope

The Gate 7 layer introduces:

- a unified challenger registry for portfolio ingestion, multi-currency exposure, MVA, KVA, incremental allocation, and operational execution;
- component-level primary-versus-challenger reconciliation;
- disagreement classification using `PASS`, `PASS_WITH_MONITORING`, `REMEDIATE`, `BLOCK`, and `INVALID`;
- seed, path-count, time-grid, input-perturbation, and sensitivity-ranking stability diagnostics;
- lifecycle drift evidence and repeated-monitoring detection;
- remediation ownership, action, evidence, reviewer, and disposition controls;
- a machine-readable lifecycle dashboard;
- governed GenAI evidence challenge with complete lineage and deterministic fixtures;
- release-candidate assessment under an explicit human decision boundary.

## Challenger governance

Each validated model layer has one named challenger specification with:

- a primary method;
- an independent challenger method;
- a numerical tolerance;
- a materiality threshold;
- required evidence fields;
- a deterministic registry identity.

Differences at or below tolerance pass. Differences above tolerance but below materiality require remediation. Differences above materiality block promotion.

## Stability and drift

Stability evidence is separated from model-performance claims. The layer evaluates whether results remain governed under:

- different deterministic seeds;
- increasing path counts;
- alternate time grids;
- FX, curve, spread, collateral, margin, and capital-policy perturbations;
- changes in sensitivity ordering.

Drift evidence records reference value, current value, absolute shift, relative shift, thresholds, and resulting status. Repeated monitoring breaches remain visible rather than being silently reset.

## Remediation and promotion

A Gate 7 release-candidate assessment may pass only when:

1. every required challenger is registered;
2. no `BLOCK` or `INVALID` item remains;
3. every `REMEDIATE` item has a resolved disposition;
4. stability and drift evidence contain no blocking observation;
5. the governed GenAI boundary passes;
6. the release-candidate decision is made by a human reviewer.

The target status is:

```text
RELEASE_CANDIDATE_VALIDATED
```

This is not the v1.4 release. Gate 8 remains responsible for release consolidation, final documentation, assurance, explicit `RELEASE` approval, annotated tagging, GitHub release publication, and post-release assurance.

## Governed GenAI boundary

GenAI is limited to advisory evidence challenge. Every record retains:

- prompt identifier;
- model identifier and version;
- input and output hashes;
- human reviewer;
- final disposition.

GenAI cannot:

- approve a model;
- alter a quantitative result;
- close a remediation without human review;
- promote a release candidate;
- create a release tag;
- grant production or regulatory approval.

The enforced boundary is:

```text
GENAI_ADVISORY_ONLY_NO_AUTONOMOUS_APPROVAL
```

## Promotion identity

The governing rule is:

\[
\text{Eligible for Gate 8}
\iff
\text{No Material BLOCK}
\land
\text{All REMEDIATE Items Resolved}
\land
\text{Human Decision}.
\]

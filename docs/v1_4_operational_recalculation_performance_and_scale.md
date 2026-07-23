# v1.4 Gate 6 — Operational Recalculation, Performance, and Scale

Gate 6 converts the validated v1.4 quantitative stack into a controlled operational calculation framework. It does not change the economics established in Gates 1–5. Its purpose is to determine what must be recalculated, what may be reused, how interrupted runs recover, and whether scale improvements preserve the validated outputs.

## Governing boundary

Every operational optimization remains subject to:

\[
\boxed{
\text{Optimized Result}
=
\text{Validated Full-Recalculation Result}
\quad \text{within governed tolerance.}
}
\]

A faster result is not acceptable when it is quantitatively different, based on stale evidence, or cannot be reproduced from its inputs.

## Dependency graph

The governed graph covers:

1. portfolio ingestion;
2. market and policy state;
3. FX conversion;
4. exposure;
5. credit and funding XVA;
6. initial margin and MVA;
7. capital profile and KVA;
8. total XVA;
9. allocation analytics.

The graph is acyclic and has a deterministic topological order. A change is propagated to all descendants. Graph-topology changes force full recalculation.

## Snapshot comparison and change impact

Operational snapshots retain hashes for:

- the canonical portfolio;
- each trade;
- market factors;
- policy inputs;
- dependency-graph topology;
- engine version.

Comparison produces explicit added, removed, and modified trades, changed market factors, changed policies, and graph changes. Every recalculated node retains a reason tied to those changes.

## Cache controls

Cache identity includes the node, dependency output hashes, external input, policy hash, engine version, seed, and calculation scope. Cache entries are atomic, content addressed, and independently checked for:

- key consistency;
- output integrity;
- metadata integrity;
- staleness;
- corruption.

A stale or corrupt entry is never reused.

## Restartable execution

Run checkpoints retain the plan hash, node states, chunk states, completed output hashes, and failures. Writes are atomic and hash verified. Recovery resumes pending work without treating failed or incomplete work as completed.

## Chunking and parallel determinism

Work is ordered by stable item identifier and divided into deterministic chunks. Item-level seeds are derived from the global seed and item identifier. Parallel results are reordered before aggregation, chunk checksums are verified, and `math.fsum` is used for stable summation.

The same inputs must produce the same quantitative outputs under one worker or several workers.

## Performance evidence

The benchmark layer records:

- trade count;
- path count;
- chunk size;
- worker count;
- elapsed time;
- peak allocated memory;
- deterministic checksum;
- budget status.

Timing is evidence, not a substitute for correctness. Promotion requires full-versus-partial, cached-versus-uncached, and sequential-versus-parallel reconciliation.

## Model boundaries

Gate 6 does not grant production approval, regulatory approval, or infrastructure certification. The implementation is a public operational-control reference layer. Gate 7 remains responsible for independent challenge, stability, lifecycle monitoring, and governed GenAI evidence review.

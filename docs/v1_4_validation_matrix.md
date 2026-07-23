# v1.4 Validation Matrix

| Gate | Layer | Target status | Release evidence |
|---:|---|---|---|
| 0 | Architecture, scope, and contract freeze | `ARCHITECTURE_FROZEN` | architecture and gate-sequence contracts |
| 1 | Canonical portfolio ingestion and lineage | `PORTFOLIO_CONTRACTS_VALIDATED` | schemas, fixtures, lineage, parser challenger |
| 2 | Multi-currency exposure and collateral | `MULTI_CURRENCY_VALIDATED` | FX parity, triangulation, collateral-currency benchmarks |
| 3 | Initial margin and MVA | `MVA_VALIDATED` | IM proxy benchmarks, MVA attribution, challenger |
| 4 | Capital profiles and KVA | `KVA_VALIDATED` | capital/KVA profiles, sensitivities, challenger |
| 5 | Incremental, marginal, and allocation analytics | `INCREMENTAL_ANALYTICS_VALIDATED` | full revaluation, approximation disclosure, residual reconciliation |
| 6 | Operational recalculation, performance, and scale | `OPERATIONAL_SCALE_VALIDATED` | partial/full equivalence, cache, checkpoints, parallel determinism |
| 7 | Independent challenge, stability, and lifecycle | `RELEASE_CANDIDATE_VALIDATED` | challenger registry, drift, remediation, advisory GenAI |
| 8 | Release consolidation | `RELEASED_WITH_MONITORING` | release manifest, dashboard, assurance, tag, GitHub release |

Validated test surface: `708 collected tests` for v1.4.0.

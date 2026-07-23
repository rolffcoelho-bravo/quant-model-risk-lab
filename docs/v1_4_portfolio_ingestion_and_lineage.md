# v1.4 Gate 1 — Canonical Portfolio Ingestion and Lineage

## Decision status

Gate 1 establishes the authoritative public portfolio representation for the v1.4 development line. The layer is intentionally limited to domain modelling, strict ingestion, validation, lineage, data-quality evidence, parser challenge, and deterministic benchmarks.

It does not introduce multi-currency valuation, initial margin, MVA, capital profiles, KVA, incremental XVA, or production trade capture.

Target status:

```text
PORTFOLIO_CONTRACTS_VALIDATED
```

## Promotion rule

\[
\boxed{
\text{No downstream calculation may consume an invalid, incomplete, or partially mapped portfolio snapshot.}
}
\]

An invalid snapshot receives `BLOCK`. Only a snapshot with validation status `PASS` may be promoted to Gate 2 calculations.

## Canonical hierarchy

The canonical portfolio graph is:

```text
PortfolioSnapshot
├── CurrencyDefinition
├── LegalEntity
├── Counterparty hierarchy
├── AgreementTerms
├── NettingSet
├── CollateralSet
└── TradeRecord
```

Each calculation-ready trade must map to:

```text
TradeRecord
  → LegalEntity
  → Counterparty
  → NettingSet
  → AgreementTerms
  → optional CollateralSet
  → declared currencies
```

The mapping is validated before any quantitative engine receives the snapshot.

## Strict ingestion

The Gate 1 JSON parser:

- requires the governed root fields;
- rejects unknown fields;
- rejects incorrect object and array types;
- rejects non-numeric notional fields;
- rejects non-JSON attributes;
- preserves a raw source hash;
- creates a deterministic canonical representation;
- supports explicit validation without allowing partial mapping.

Schema rejection and business validation are separate:

- malformed structure raises `PortfolioSchemaError`;
- structurally valid but inconsistent data produces validation issues;
- `reject_invalid=True` raises `PortfolioIngestionError`;
- `reject_invalid=False` permits evidence generation but does not permit downstream calculation.

## Validation controls

The validator covers:

- duplicate identifiers;
- identifier syntax;
- ISO currency declarations;
- reporting-currency declarations;
- counterparty-parent existence;
- counterparty hierarchy cycles;
- legal-entity references;
- counterparty references;
- agreement references;
- netting-set references;
- collateral-set references;
- agreement consistency;
- trade-to-netting counterparty consistency;
- trade-to-netting legal-entity consistency;
- trade-to-collateral-set consistency;
- finite and non-zero notionals;
- ISO trade dates;
- effective/maturity ordering;
- exclusion of matured active trades.

The data-quality report provides entity counts, error counts, warning counts, issue details, and the explicit downstream-calculation decision.

## Deterministic canonicalization

Canonical serialization uses:

- UTF-8;
- lexicographic object keys;
- identifier-sorted entity collections;
- sorted eligible-currency lists;
- finite JSON values only;
- stable numeric representation supplied by Python JSON serialization.

Equivalent snapshots with different input collection order produce the same canonical portfolio hash.

Raw source hashes remain separate from canonical hashes. This distinguishes transport-level evidence from semantic calculation identity.

## Calculation lineage

Every future calculation must be traceable to a `CalculationRun` containing:

- run identifier;
- valuation date;
- portfolio snapshot identifier;
- model version;
- configuration hash;
- canonical input hash;
- raw source hash;
- random seed;
- creation timestamp.

The deterministic run identifier depends on:

```text
canonical input hash
+ configuration hash
+ model version
+ valuation date
+ random seed
```

The creation timestamp is evidence metadata and does not alter deterministic calculation identity.

## Independent parser challenge

The independent challenger does not reuse the primary relationship indexes. It independently:

- counts every canonical entity collection;
- reconstructs netting-set references;
- reconstructs collateral-set references;
- checks trade counterparty mappings;
- checks trade legal-entity mappings;
- checks trade collateral mappings;
- compares trade identifier sets.

A discrepancy produces `BLOCK`.

## Synthetic reference evidence

The public Gate 1 fixtures include:

- a valid multi-counterparty reference portfolio;
- a missing-netting-set case;
- a duplicate-trade case;
- a counterparty-hierarchy cycle;
- a collateral-mapping mismatch;
- an unknown-field schema rejection.

These are synthetic validation fixtures. They do not represent confidential trades, legal agreements, or institution-specific capital policy.

## Benchmark evidence

The benchmark suite locks:

- valid portfolio entity counts;
- invalid portfolio issue codes;
- strict unknown-field rejection;
- deterministic result ordering;
- complete case execution.

Benchmarks are machine-readable in:

```text
configs/v1_4_portfolio_benchmark_contract.yml
```

## Model boundaries

Gate 1 does not claim:

- production trade-capture compatibility;
- legal enforceability of agreement terms;
- complete product economics;
- live market-data integration;
- production data governance;
- regulatory reporting;
- SIMM certification;
- quantitative XVA readiness from invalid snapshots.

The public schemas are designed to support transparent research, validation, and portfolio-model architecture. Institution-specific adapters remain outside the Gate 1 boundary.

## Gate 2 handoff

Gate 2 may consume only a Gate 1 result satisfying:

```text
validation.is_valid == True
downstream_calculation_permitted == True
challenger.status == PASS
canonical input hash present
calculation lineage complete
```

Gate 2 will extend the validated snapshot into multi-currency exposure and collateral calculations while preserving single-currency v1.3 compatibility.

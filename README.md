# Quant Model Risk Lab

![Release](https://img.shields.io/badge/release-v1.4.0-176B52)
![Python](https://img.shields.io/badge/Python-3.12-blue)
[![Validation CI](https://github.com/rolffcoelho-bravo/quant-model-risk-lab/actions/workflows/validation-ci.yml/badge.svg?branch=main)](https://github.com/rolffcoelho-bravo/quant-model-risk-lab/actions/workflows/validation-ci.yml)
![Status](https://img.shields.io/badge/Status-RELEASED_WITH_MONITORING-C69214)
![Tests](https://img.shields.io/badge/tests-708%20collected-176B52)
![Use](https://img.shields.io/badge/Use-Public%20Research%20Evidence-lightgrey)

**Open Portfolio-Scale Model Validation, XVA, Derivatives, Monitoring, and Risk Analytics Laboratory**

**Publisher:** ShockBridge Pulse Research  
**Research site:** https://www.shockbridgepulse.com  
**Author:** Rodolfo Pereira  
**Repository type:** Public quantitative model-risk evidence package  
**Current release:** v1.4.0 Portfolio-Scale Quantitative Model-Risk Laboratory  
**Release status:** `RELEASED_WITH_MONITORING`

---

## What this repository proves

Quant Model Risk Lab demonstrates how portfolio-scale quantitative model-risk work can be made inspectable through executable models, canonical portfolio lineage, independent challengers, governed inputs, deterministic benchmarks, valuation-adjustment attribution, monitoring rules, lifecycle evidence, structured findings, and enforced continuous integration.

The v1.4.0 release provides a coherent public validation chain:

```text
Validated portfolio snapshot and lineage
        |
        v
Multi-currency exposure and collateral
        |
        v
CVA / DVA / FVA / MVA / KVA
        |
        v
Incremental, marginal, and allocation analytics
        |
        v
Dependency-aware recalculation and scale controls
        |
        v
Independent challenge, stability, drift, lifecycle, and human release governance
```

No single layer is treated as sufficient validation evidence on its own. A material `BLOCK` cannot be offset by stronger results in another component.

## v1.4 portfolio-scale platform

| Gate | Validation layer | Primary evidence | Status |
|---:|---|---|---|
| 0 | Architecture, scope, and contract freeze | Architecture and gate-sequence contracts | `ARCHITECTURE_FROZEN` |
| 1 | Canonical portfolio ingestion and lineage | Schemas, fixtures, lineage, and parser challenger | `PORTFOLIO_CONTRACTS_VALIDATED` |
| 2 | Multi-currency exposure and collateral | FX parity, triangulation, collateral-currency benchmarks | `MULTI_CURRENCY_VALIDATED` |
| 3 | Initial margin and MVA | IM proxy benchmarks, MVA attribution, and challenger | `MVA_VALIDATED` |
| 4 | Capital profiles and KVA | Capital and KVA profiles, sensitivities, and challenger | `KVA_VALIDATED` |
| 5 | Incremental, marginal, and allocation analytics | Full revaluation, approximation disclosure, and residual reconciliation | `INCREMENTAL_ANALYTICS_VALIDATED` |
| 6 | Operational recalculation, performance, and scale | Partial/full equivalence, cache, checkpoints, and parallel determinism | `OPERATIONAL_SCALE_VALIDATED` |
| 7 | Independent challenge, stability, and lifecycle | Challenger registry, drift, remediation, and advisory GenAI | `RELEASE_CANDIDATE_VALIDATED` |
| 8 | Release consolidation | Release manifest, dashboard, assurance, tag, and GitHub release | `RELEASED_WITH_MONITORING` |

**Validated test surface:** `708 collected tests`.

Every pull request targeting `main` must pass the provider-bound check `Python 3.12 validation`.

## Decision-grade v1.4 release evidence

- [`configs/release_manifest_v1_4_gate8.json`](configs/release_manifest_v1_4_gate8.json)
- [`docs/v1_4_validation_matrix.md`](docs/v1_4_validation_matrix.md)
- [`reports/v1_4_validation_dashboard.md`](reports/v1_4_validation_dashboard.md)
- [`reports/v1_4_lifecycle_report.md`](reports/v1_4_lifecycle_report.md)
- [`reports/v1_4_release_assurance.md`](reports/v1_4_release_assurance.md)
- [`docs/releases/v1.4.0.md`](docs/releases/v1.4.0.md)
- [`docs/v1_4_model_boundaries_and_governance.md`](docs/v1_4_model_boundaries_and_governance.md)
- [`CITATION_v1_4.cff`](CITATION_v1_4.cff)

## Dashboard and lifecycle monitoring

The v1.4 dashboard is a validation object, not a market forecast or production risk report. It presents controlled status, ownership, evidence, and escalation information across portfolio ingestion, exposure, credit, XVA, MVA, KVA, allocation, stress, challenger, stability, drift, and release layers.

Lifecycle monitoring covers:

- benchmark drift
- challenger disagreement
- input freshness
- path convergence
- tail concentration
- allocation residuals
- operational recovery state
- open validation gates
- remediation ownership
- revalidation and escalation status

## Governed GenAI validation layer

GenAI is used as a controlled validation assistant and documentation challenger. It is not an autonomous model approver.

Controls include:

1. approved and hashed evidence only
2. versioned instructions and prohibited actions
3. structured findings
4. mandatory repository artifact citations
5. deterministic schema and grounding tests without a live provider credential
6. mandatory human review

GenAI cannot approve production use, close material findings, override quantitative tests, invent calibration evidence, or remove explicit model boundaries.

## Preserved v1.3 XVA foundation

The immutable v1.3.0 release remains the validated XVA foundation beneath v1.4.0.

| Gate | Validation layer | Primary evidence | Status |
|---:|---|---|---|
| 1 | Time grids, netting, collateral, and deterministic exposure controls | `docs/xva_exposure_simulation_architecture.md` | `PASS` |
| 2 | Correlated scenario paths and future-value cubes | `docs/xva_scenario_path_architecture.md` | `PASS` |
| 3 | Pathwise netting, collateral, and exposure integration | `docs/xva_pathwise_exposure_integration.md` | `PASS` |
| 4 | Counterparty credit calibration and PD/LGD term structures | `docs/xva_counterparty_credit_calibration.md` | `PASS_WITH_MONITORING` |
| 5 | CVA, DVA, FCA, FBA, FVA, sensitivities, and attribution | `docs/xva_integration_and_attribution.md` | `PASS` |
| 6 | Wrong-way risk, stress, tail exposure, and concentration | `docs/xva_wrong_way_risk_and_stress.md` | `PASS_WITH_MONITORING` |
| 7 | Independent challenge, stability, and promotion governance | `docs/xva_independent_challenger_and_promotion.md` | `PASS` |
| 8 | Dashboard, lifecycle monitoring, governed GenAI, and release governance | `docs/xva_v1_3_release_validation.md` | `PASS_WITH_MONITORING` |

The v1.3.0 validated test surface remains `350 collected tests` and is preserved by the v1.4 release-assurance contract.

### Preserved v1.3 evidence

- [`reports/xva_v1_3_validation_dashboard.md`](reports/xva_v1_3_validation_dashboard.md)
- [`reports/xva_v1_3_validation_dashboard.json`](reports/xva_v1_3_validation_dashboard.json)
- [`reports/xva_v1_3_lifecycle_monitoring.md`](reports/xva_v1_3_lifecycle_monitoring.md)
- [`reports/xva_v1_3_lifecycle_monitoring.json`](reports/xva_v1_3_lifecycle_monitoring.json)
- [`configs/release_manifest_v1_3.json`](configs/release_manifest_v1_3.json)
- [`docs/validation_matrix.md`](docs/validation_matrix.md)
- [`docs/releases/v1.3.0.md`](docs/releases/v1.3.0.md)
- [`data/genai/inputs/xva_v1_3_release_evidence.json`](data/genai/inputs/xva_v1_3_release_evidence.json)
- [`data/genai/outputs/xva_v1_3_release_challenge.json`](data/genai/outputs/xva_v1_3_release_challenge.json)
- [`data/genai/outputs/xva_v1_3_human_review.json`](data/genai/outputs/xva_v1_3_human_review.json)

## Other implemented platform layers

| Layer | Public evidence |
|---|---|
| Interest-rate valuation | Swap valuation, par rate, NPV, DV01, curve shocks, and lifecycle evidence |
| Inflation derivatives | BEI mapping, inflation sensitivity, shock tables, and decision dashboard |
| FX forwards | Official input controls, covered-interest-parity valuation, shocks, and lifecycle evidence |
| FX options | Garman-Kohlhagen valuation, Greeks, parity, volatility governance, and independent challenger |
| FX monitoring | Thresholds, ownership, alerts, revalidation state, and open market-quote gate |
| XVA exposure | EE, EPE, ENE, PFE, MPOR, netting, collateral, and counterparty calibration |
| Portfolio XVA | CVA, DVA, FVA, MVA, KVA, incremental analytics, allocation, and attribution |
| ML model-risk monitoring | Shrinkage Mahalanobis distance, PCA drift, regime classification, and decision controls |
| Governed GenAI | Evidence packages, structured challenges, grounding, and human review |
| Continuous integration | Python 3.12 compilation, dependency verification, full pytest, and JUnit evidence |

## Repository map

```text
.github/workflows/   Enforced continuous-integration workflows
configs/             Versioned model, monitoring, GenAI, and release contracts
data/                Public validation evidence and governed GenAI packages
docs/                Architecture, governance, validation matrix, and releases
model_inventory/     Lifecycle, remediation, and findings records
reports/             Decision-facing validation reports and dashboards
scripts/             Reproducible evidence-generation entry points
src/qmrl/            Quantitative models and validation components
tests/               Unit, property, benchmark, governance, and release tests
```

## Run the validation suite

```powershell
python -m pip install -r requirements.txt
python -m pytest
```

Current validation state: **708 collected tests passing**.

## Current public boundaries

This repository does not claim:

- production or regulatory model approval
- access to proprietary OTC portfolios or counterparty data
- institution-approved CSA or legal-enforceability opinions
- confidential funding, liquidity, credit, capital, margin, or stress calibration
- enterprise collateral, limit, alert, or workflow integration
- investment advice or trading recommendations

The dated USD/BRL market-option quote benchmark remains `OPEN_NO_PUBLIC_QUOTE_DATA`.

Public thresholds and parameters are validation controls. Initial-margin and capital outputs remain transparent public proxies. CI success demonstrates reproducibility, not production approval.

## Commercial application boundary

Quant Model Risk Lab is the public research and evidence foundation for ShockBridge Pulse quantitative model-risk work. It is not a free or community edition of a commercial product.

**ShockBridge XVA Portfolio Scan** is a separate paid diagnostic service priced at **$199 per portfolio scan**. The commercial service is not distributed through this repository and is governed by separate commercial terms.

The public repository does not include:

- the proprietary ShockBridge XVA Pressure Score methodology
- commercial portfolio-intake and schema-mapping workflows
- customer-specific thresholds and scenario configuration
- commercial report generation and executive interpretation
- client delivery, support, monitoring, or service-level commitments
- private deployment, integration, or licensing assets

The proprietary ShockBridge XVA Pressure Score is defined across five controlled dimensions:

- exposure pressure
- valuation-adjustment burden
- counterparty and trade concentration
- wrong-way and stress sensitivity
- model-risk and monitoring weakness

Its weights, transformations, thresholds, aggregation rules, validation contract, and implementation are not part of this public repository.

## License boundary

Code and documentation already published in this repository remain available under the repository's MIT License. Separate commercial software, proprietary methodologies, service workflows, client reports, and future private components are not licensed under the MIT License merely because they use or reference this public research foundation.

## Release history

- **v1.4.0** — Portfolio ingestion and lineage, multi-currency exposure, MVA, KVA, incremental and allocation analytics, operational scale, stability, drift, lifecycle governance, and advisory GenAI challenge
- **v1.3.0** — XVA exposure simulation, counterparty calibration, valuation adjustments, WWR, stress, independent challenge, lifecycle monitoring, and governed GenAI release review
- **v1.2.0** — Governed GenAI and model-risk platform consolidation
- **v1.1** — FX options validation
- **v1.0** — FX derivatives validation
- **v0.9** — Transparent static XVA validation layer

## Citation

Pereira, Rodolfo. (2026). *Quant Model Risk Lab v1.4.0: Portfolio-Scale Quantitative Model-Risk Laboratory*. ShockBridge Pulse Research. Python research software.

See [`CITATION_v1_4.cff`](CITATION_v1_4.cff) for machine-readable citation metadata.

## Disclaimer

This project is for research, education, validation evidence, and professional portfolio demonstration. It does not provide investment advice, trading recommendations, regulatory validation, production model approval, or a substitute for institution-specific independent validation.

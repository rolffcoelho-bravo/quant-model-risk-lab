# Quant Model Risk Lab

![Release](https://img.shields.io/badge/release-v1.3.0-176B52)
![Python](https://img.shields.io/badge/Python-3.12-blue)
[![Validation CI](https://github.com/rolffcoelho-bravo/quant-model-risk-lab/actions/workflows/validation-ci.yml/badge.svg?branch=main)](https://github.com/rolffcoelho-bravo/quant-model-risk-lab/actions/workflows/validation-ci.yml)
![Status](https://img.shields.io/badge/Status-PASS_WITH_MONITORING-C69214)
![Use](https://img.shields.io/badge/Use-Research%20Only-lightgrey)

**Open Model Validation, XVA, Derivatives, Monitoring, and Risk Analytics Lab**

**Publisher:** ShockBridge Pulse Research  
**Research site:** https://www.shockbridgepulse.com  
**Author:** Rodolfo Pereira  
**Repository type:** Public model-risk evidence package  
**Current release:** v1.3.0 XVA Exposure Simulation and Counterparty Risk Validation Platform

---

## What this repository proves

Quant Model Risk Lab demonstrates how quantitative model-risk work can be made inspectable through executable models, independent challengers, governed inputs, deterministic benchmarks, monitoring rules, lifecycle evidence, structured findings, and enforced continuous integration.

The v1.3.0 release provides a coherent public XVA validation chain:

```text
Market-factor scenarios
        |
        v
Pathwise future values
        |
        v
Legal netting and collateral state
        |
        v
EE, EPE, ENE, PFE, and MPOR exposure
        |
        v
Counterparty hazard, survival, PD, recovery, and LGD
        |
        v
CVA, DVA, FCA, FBA, FVA, and attribution
        |
        v
Wrong-way risk and stress scenarios
        |
        v
Independent challengers and stability diagnostics
        |
        v
Lifecycle monitoring, governed GenAI challenge, and human release decision
```

No single layer is treated as sufficient validation evidence on its own.

## v1.3 XVA platform

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

**Validated test surface:** `350 collected tests`.

Every pull request targeting `main` must pass the provider-bound check `Python 3.12 validation`.

## Decision-grade release evidence

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

## Dashboard and lifecycle monitoring

The v1.3 dashboard is a validation object, not a market forecast or production risk report. It presents controlled status, ownership, evidence, and escalation information across exposure, credit, XVA, stress, challenger, and release layers.

Lifecycle monitoring covers:

- benchmark drift
- challenger disagreement
- input freshness
- path convergence
- tail concentration
- open validation gates
- revalidation and escalation status

A material `BLOCK` cannot be offset by stronger results in another component.

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

## Other implemented platform layers

| Layer | Public evidence |
|---|---|
| Interest-rate valuation | Swap valuation, par rate, NPV, DV01, curve shocks, and lifecycle evidence |
| Inflation derivatives | BEI mapping, inflation sensitivity, shock tables, and decision dashboard |
| FX forwards | Official input controls, covered-interest-parity valuation, shocks, and lifecycle evidence |
| FX options | Garman-Kohlhagen valuation, Greeks, parity, volatility governance, and independent challenger |
| FX monitoring | Thresholds, ownership, alerts, revalidation state, and open market-quote gate |
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

Current validation state: **350 collected tests passing**.

## Current public boundaries

This repository does not claim:

- production or regulatory model approval
- access to proprietary OTC portfolios or counterparty data
- institution-approved CSA or legal-enforceability opinions
- confidential funding, liquidity, credit, or stress calibration
- enterprise collateral, limit, alert, or workflow integration
- investment advice or trading recommendations

The dated USD/BRL market-option quote benchmark remains `OPEN_NO_PUBLIC_QUOTE_DATA`.

Public thresholds and parameters are validation controls. CI success demonstrates reproducibility, not production approval.

## Release history

- **v1.3.0** — XVA exposure simulation, counterparty calibration, valuation adjustments, WWR, stress, independent challenge, lifecycle monitoring, and governed GenAI release review
- **v1.2.0** — Governed GenAI and model-risk platform consolidation
- **v1.1** — FX options validation
- **v1.0** — FX derivatives validation
- **v0.9** — Transparent static XVA validation layer

## Citation

Pereira, Rodolfo. (2026). *Quant Model Risk Lab: XVA Exposure Simulation and Counterparty Risk Validation Platform*. ShockBridge Pulse Research. Python research software.

See [`CITATION.cff`](CITATION.cff) for machine-readable citation metadata.

## Disclaimer

This project is for research, education, and professional portfolio demonstration. It does not provide investment advice, trading recommendations, regulatory validation, or production model approval.

<!-- QMRL_V1_4_RELEASE_START -->
## v1.4.0 — Portfolio-Scale Quantitative Model-Risk Laboratory

**Latest governed release: v1.4.0**  
**Release status:** `RELEASED_WITH_MONITORING`  
**v1.4 validated test surface:** `708 collected tests`

The v1.4.0 release extends the immutable v1.3.0 XVA platform with canonical portfolio ingestion and lineage, governed multi-currency exposure, transparent initial-margin and capital proxies, MVA and KVA, full-revaluation incremental analytics, allocation residual controls, dependency-aware recalculation, deterministic caching and recovery, scale evidence, unified challengers, stability and drift diagnostics, lifecycle governance, and advisory-only GenAI evidence challenge.

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

Release evidence:

- [`configs/release_manifest_v1_4_gate8.json`](configs/release_manifest_v1_4_gate8.json)
- [`docs/v1_4_validation_matrix.md`](docs/v1_4_validation_matrix.md)
- [`reports/v1_4_validation_dashboard.md`](reports/v1_4_validation_dashboard.md)
- [`reports/v1_4_lifecycle_report.md`](reports/v1_4_lifecycle_report.md)
- [`reports/v1_4_release_assurance.md`](reports/v1_4_release_assurance.md)
- [`docs/releases/v1.4.0.md`](docs/releases/v1.4.0.md)
- [`CITATION_v1_4.cff`](CITATION_v1_4.cff)

The release remains public research software. Production approval and regulatory approval are false.
<!-- QMRL_V1_4_RELEASE_END -->

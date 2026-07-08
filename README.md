# Quant Model Risk Lab

**Open Model Validation, Official Rates, FX, Inflation & Risk Analytics Lab**

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Status](https://img.shields.io/badge/Status-Model%20Risk%20Evidence%20Lab-blue)
![Tests](https://img.shields.io/badge/Tests-20%20passing-brightgreen)
![Use](https://img.shields.io/badge/Use-Research%20Only-lightgrey)

**Publisher:** ShockBridge Pulse Research  
**Author:** Rodolfo Pereira  
**Repository type:** Public model-risk evidence package  
**Current release:** v0.3 official rates, FX and inflation data pipeline

---

## What this repository proves

Quant Model Risk Lab is a public evidence repository for model validation, model monitoring, official-data pipelines, derivative-pricing inputs and financial-risk documentation.

The project shows how model-risk work can be made inspectable through real official data, reproducible Python workflows, model inventory tracking, validation reports, findings logs, stress testing, VaR checks, Black-Scholes pricing checks and automated tests.

The objective is direct: provide public evidence of model-validation logic, data discipline, risk-model interpretation and documentation quality.

---

## Start here

For a fast review, inspect the repository in this order:

| File | Why it matters |
|---|---|
| `reports/official_rates_fx_inflation_pipeline_report.md` | Main official-data model-risk report |
| `data/official/manifest.json` | Data lineage, source URLs, hashes and output metadata |
| `data/official/processed/curve_validation_summary.csv` | Yield-curve validation and discount-factor evidence |
| `data/official/processed/fx_risk_summary.csv` | FX volatility and historical VaR summary |
| `model_inventory/model_register.csv` | Simplified model inventory |
| `model_inventory/validation_status.csv` | Validation-status evidence |
| `model_inventory/findings_log.csv` | Findings and limitations log |
| `reports/generated_model_risk_evidence.md` | Generated model-risk evidence report |
| `src/qmrl/` | Python implementation |
| `tests/` | Automated validation tests |

---

## Current evidence layer

| Evidence block | Status |
|---|---|
| Official rates, FX and inflation pipeline | Implemented |
| Raw official-data storage | Implemented |
| Processed data panels | Implemented |
| Data manifest and file hashes | Implemented |
| Curve-validation summary | Implemented |
| FX risk summary | Implemented |
| Black-Scholes validation module | Implemented |
| Historical VaR backtesting | Implemented |
| Stress testing | Implemented |
| Model monitoring | Implemented |
| Model inventory | Implemented |
| Validation-status tracking | Implemented |
| Findings log | Implemented |
| Automated tests | 20 tests passing |

---

## Real official-data layer

The v0.3 pipeline uses public official data aligned with model-risk workflows for rates, FX, inflation and derivative-pricing review.

| Data block | Public source | Model-risk purpose |
|---|---|---|
| USD interest-rate curve | FRED Treasury constant maturity rates | Curve nodes, discounting, rate sensitivity |
| FX reference rates | ECB euro foreign exchange reference rates | FX input validation, return-risk metrics, valuation inputs |
| Inflation compensation | FRED 10-year breakeven inflation | Inflation-risk review and inflation-linked model inputs |

This repository does not use ETF proxies as the main evidence layer. The current evidence layer is built around official rates, FX and inflation inputs because these are closer to model-risk work on Treasury, derivatives, curve building and valuation/risk review.

---

## Why this is close to real Model Risk work

Actual OTC derivative transaction data, XVA engines, internal curve systems and proprietary bank model inventories are usually not public.

This repository does not pretend otherwise.

Instead, it builds the closest public validation harness:

1. Download real official rates, FX and inflation data.
2. Store raw data and processed outputs.
3. Validate columns, missing values and data integrity.
4. Build curve and FX risk summaries.
5. Generate manifest files with hashes and source metadata.
6. Produce model-risk reports.
7. Track model inventory, validation status and findings.
8. Run automated tests.

---

## Run the full pipeline

Run:

    python -m pip install -r requirements.txt
    python scripts\run_official_rates_fx_inflation_pipeline.py
    python scripts\generate_model_risk_evidence.py
    python -m pytest

Current validation state: **20 tests passing**.

---

## What this project does not claim

This repository does not claim access to proprietary OTC transaction data, XVA engines, internal bank curve-construction systems, confidential model libraries, Archer records or formal institutional model approval.

It is a public, reproducible and educational model-risk evidence package.

---

## Citation

Pereira, Rodolfo. (2026). *Quant Model Risk Lab: Open Model Validation, Monitoring and Risk Analytics in Python*. ShockBridge Pulse Research. Python research software. https://github.com/rolffcoelho-bravo/quant-model-risk-lab

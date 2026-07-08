# Quant Model Risk Lab

**Open Model Validation, Official Rates, FX, Inflation and Risk Analytics Lab**

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Tests](https://img.shields.io/badge/Tests-32%20passing-brightgreen)
![Status](https://img.shields.io/badge/Status-Model%20Risk%20Evidence%20Lab-blue)
![Use](https://img.shields.io/badge/Use-Research%20Only-lightgrey)

**Publisher:** ShockBridge Pulse Research  
**Author:** Rodolfo Pereira  
**Repository type:** Public model-risk evidence package  
**Current release:** v0.5.4 institutional README upgrade  
**Latest analytical artifact:** v0.5.3 curve and inflation decision dashboard  

---

## What this repository proves

Quant Model Risk Lab is a public evidence repository for model validation, model monitoring, official-data pipelines, derivative-pricing inputs, curve-risk review, inflation-risk review and financial-risk documentation.

The project shows how model-risk work can be made inspectable through real official data, reproducible Python workflows, model inventory tracking, validation reports, findings logs, stress testing, VaR checks, curve-pricing checks, Black-Scholes pricing checks, institutional decision reports and automated tests.

The objective is direct: provide public evidence of model-validation logic, data discipline, valuation-review reasoning, risk-model interpretation and documentation quality.

---

## Start here

For a fast review, inspect these files first:

| Review item | File | What it proves |
|---|---|---|
| Decision dashboard | `reports/figures/curve_inflation_decision_map.png` | Bank-facing curve and inflation monitoring artifact |
| One-page report | `reports/one_page_curve_inflation_decision_report.md` | Decision state, model-risk trigger, bank action and investor read-through |
| Curve-pricing harness | `reports/curve_pricing_validation_harness.md` | Official curve inputs, discount factors, bond price, DV01 and shock sensitivity |
| Official-data report | `reports/official_rates_fx_inflation_pipeline_report.md` | Public official rates, FX and inflation data pipeline |
| Data lineage | `data/official/manifest.json` | Source URLs, hashes and reproducibility metadata |
| Model inventory | `model_inventory/model_register.csv` | Simplified model lifecycle evidence |
| Findings log | `model_inventory/findings_log.csv` | Validation findings and limitations |
| Source code | `src/qmrl/` | Python implementation |
| Tests | `tests/` | Automated validation checks |

---

## Current decision artifact

The current front-facing artifact is:

```text
reports/figures/curve_inflation_decision_map.png
reports/one_page_curve_inflation_decision_report.md
```

It uses real official data and transforms it into a model-risk decision dashboard:

| Block | Purpose |
|---|---|
| Treasury curve context | Latest curve versus 252-day range and median |
| Rate-shock loss surface | Valuation loss across tenor and parallel rate shocks |
| Curve and inflation monitor | 2s10s slope and 10Y breakeven inflation over time |
| Decision card | Model-risk state, pressure score, trigger, bank decision and investor decision |

The dashboard is not a market forecast. It is a validation object. It shows which input channel is active, which valuation loss is material, what the bank should review, and what an investor should monitor.

---

## Repository structure

```text
quant-model-risk-lab/
|-- data/
|   |-- README.md
|   `-- official/
|       |-- raw/
|       |-- processed/
|       `-- manifest.json
|-- docs/
|   |-- interview_alignment_note.md
|   |-- limitations_and_assumptions.md
|   |-- model_lifecycle.md
|   |-- model_risk_framework.md
|   |-- official_rates_fx_inflation_pipeline.md
|   `-- validation_policy.md
|-- model_inventory/
|   |-- findings_log.csv
|   |-- model_register.csv
|   `-- validation_status.csv
|-- reports/
|   |-- figures/
|   |   `-- curve_inflation_decision_map.png
|   |-- curve_pricing_validation_harness.md
|   |-- generated_model_risk_evidence.md
|   |-- official_rates_fx_inflation_pipeline_report.md
|   |-- one_page_curve_inflation_decision_report.md
|   |-- sample_model_monitoring_report.md
|   `-- sample_model_validation_report.md
|-- scripts/
|   |-- generate_model_risk_evidence.py
|   |-- run_curve_pricing_validation_harness.py
|   |-- run_official_rates_fx_inflation_pipeline.py
|   `-- run_one_page_curve_inflation_decision_report.py
|-- src/
|   `-- qmrl/
|       |-- black_scholes.py
|       |-- curve_pricing.py
|       |-- data_checks.py
|       |-- monitoring.py
|       |-- reporting.py
|       |-- stress_testing.py
|       `-- var_backtesting.py
|-- tests/
|-- README.md
|-- LICENSE
`-- requirements.txt
```

---

## Model architecture

The project follows a layered model-risk methodology:

1. Official rates, FX and inflation data ingestion  
2. Raw-data storage and reproducibility layer  
3. Data-quality and missing-value validation  
4. Curve, FX and inflation feature construction  
5. Curve-pricing validation harness  
6. Discount-factor, DV01 and rate-shock review  
7. Decision dashboard for bank and investor interpretation  
8. Model inventory, validation status and findings evidence  
9. Planned inflation-derivatives validation layer  
10. Planned ML model-risk monitoring layer  
11. Planned high-dimensional drift, shrinkage and nonlinear challenger layer  
12. Planned dynamic regime monitoring with Gaussian Hidden Markov Models  

---

## Real official-data layer

The repository uses public official data aligned with rates, FX, inflation and derivative-pricing model-risk workflows.

| Data block | Public source | Model-risk purpose |
|---|---|---|
| USD interest-rate curve | FRED Treasury constant maturity rates | Curve nodes, discounting, rate sensitivity and DV01 review |
| FX reference rates | ECB euro foreign exchange reference rates | FX input validation, return-risk metrics and valuation inputs |
| Inflation compensation | FRED 10-year breakeven inflation | Inflation-risk review and inflation-linked model inputs |

This repository does not use ETF proxies as the main evidence layer. The analytical layer is built around official rates, FX and inflation inputs because these are closer to model-risk work on Treasury, derivatives, curve building and valuation/risk review.

---

## Current implemented layers

| Component | Status |
|---|---|
| Core model-risk framework | Implemented |
| Model inventory | Implemented |
| Validation status tracking | Implemented |
| Findings log | Implemented |
| Official rates, FX and inflation pipeline | Implemented |
| Data manifest and file hashes | Implemented |
| Curve-pricing validation harness | Implemented |
| Discount-factor review | Implemented |
| DV01 calculation | Implemented |
| Rate-shock loss surface | Implemented |
| One-page curve and inflation decision dashboard | Implemented |
| Black-Scholes validation module | Implemented |
| Historical VaR backtesting | Implemented |
| Stress testing | Implemented |
| Monitoring module | Implemented |
| Automated tests | 32 tests passing |

---

## Why this is close to real Model Risk work

Actual OTC derivative transaction data, XVA production inputs, internal curve-construction systems and proprietary bank model inventories are usually not public.

This repository does not pretend otherwise.

Instead, it builds the closest public validation harness:

1. Download real official rates, FX and inflation data.
2. Store raw files and processed outputs.
3. Validate data completeness and input structure.
4. Build curve and inflation monitoring features.
5. Generate discount factors, bond-pricing outputs and DV01.
6. Apply +50bp, +100bp and broader curve shocks.
7. Convert valuation movement into decision evidence.
8. Document limitations, triggers and validation actions.
9. Run automated tests.

This gives a reviewer public evidence of model-validation logic, documentation discipline, reproducibility, Python workflows and risk-model interpretation.

---

## Inflation derivatives roadmap

Inflation derivatives are a core next layer because inflation-linked valuation and risk review require clear input mapping, breakeven interpretation, sensitivity testing and scenario logic.

Planned v0.6:

| Artifact | Purpose |
|---|---|
| `src/qmrl/inflation_pricing.py` | Standardized inflation-linked validation instrument |
| `scripts/run_inflation_derivatives_validation.py` | Real-data inflation validation workflow |
| `reports/inflation_derivatives_validation_report.md` | Inflation compensation, payoff logic and sensitivity review |
| `reports/figures/inflation_derivatives_validation_map.png` | Inflation sensitivity decision graphic |
| `data/official/processed/inflation_derivatives_summary.csv` | Inflation-linked validation metrics |
| `tests/test_inflation_pricing.py` | Tests for inflation valuation logic |

Initial focus:

1. Use real 10Y breakeven inflation data.
2. Build a standardized inflation-linked validation payoff.
3. Apply inflation-compensation shocks.
4. Report inflation sensitivity and threshold triggers.
5. Explain what should be challenged by a validator.

---

## Machine-learning model-risk roadmap

The ML layer is not designed to forecast markets. It is designed to select the appropriate statistical or machine-learning tool according to the validation question.

Model-risk questions:

| Question | Candidate tools |
|---|---|
| Is the current input environment abnormal? | Isolation Forest, Mahalanobis distance, robust covariance |
| Is there an abrupt jump in curve or inflation inputs? | Haar jump detector, rolling z-score |
| Is the market-data regime changing? | KMeans, Gaussian Mixture, Bayesian Gaussian Mixture |
| Is the covariance structure unstable? | Ledoit-Wolf shrinkage, Oracle Approximating Shrinkage |
| Is high-dimensional input structure drifting? | PCA reconstruction error, shrinkage Mahalanobis distance |
| Are nonlinearities present? | Kernel PCA, Isolation Forest, Gaussian Process challenger |
| Is the system switching between latent regimes? | Gaussian Hidden Markov Model, Kalman/state-space challenger |

Planned ML outputs:

| Artifact | Purpose |
|---|---|
| `src/qmrl/ml_features.py` | Rates, FX and inflation feature construction |
| `src/qmrl/model_selection.py` | Dynamic model-selection logic |
| `src/qmrl/high_dimensional_drift.py` | Input drift and shrinkage diagnostics |
| `reports/ml_model_risk_monitoring_report.md` | Monitoring report with model choice and challenger evidence |
| `reports/model_selection_memo.md` | Why the selected model fits the validation question |
| `reports/figures/ml_regime_monitoring_map.png` | Regime and anomaly dashboard |

Model-selection principle:

```text
The chosen model must be justified by the validation question, data structure, sample size, feature shape, interpretability need, robustness requirement and model-risk objective.
```

---

## Gaussian model family

Gaussian tools are not limited to Gaussian Mixture Models. The roadmap keeps the full Gaussian family available where appropriate.

| Tool | Model-risk use |
|---|---|
| Gaussian Mixture Model | Static regime classification |
| Bayesian Gaussian Mixture | Regime classification when the number of states is uncertain |
| Gaussian Hidden Markov Model | Dynamic latent regime-switching monitor |
| Gaussian Process Regression | Nonlinear challenger with uncertainty bands |
| Gaussian Process Classification | Probabilistic stress classification |
| Mahalanobis distance | Covariance-based anomaly detection |
| Robust covariance / Elliptic Envelope | Outlier-robust Gaussian anomaly detection |
| Kalman filter / state-space model | Dynamic curve, inflation or latent-state tracking |
| Gaussian copula | Dependence and joint-distribution review |

Gaussian Hidden Markov Models are reserved for dynamic regime-switching diagnostics. They are used when the validation question is not only whether the current input environment is abnormal, but whether rates, FX and inflation inputs are transitioning between latent market-data regimes.

---

## High-dimensional model-risk roadmap

The second phase will add high-dimensional input drift, shrinkage and nonlinear diagnostics.

Planned focus:

| Layer | Purpose |
|---|---|
| High-dimensional input drift | Detect whether current inputs no longer fit model-development history |
| Shrinkage covariance | Stabilize covariance estimates under noisy, correlated features |
| PCA reconstruction error | Detect factor-structure breaks |
| Shrinkage Mahalanobis distance | Detect abnormal multivariate states with better covariance stability |
| Nonlinear anomaly detection | Capture abnormal states missed by linear diagnostics |
| Challenger monitoring | Compare baseline, Gaussian and nonlinear model-risk signals |

This layer will be used for model monitoring, anomaly detection, regime review and challenger evidence. It will not be presented as a trading strategy.

---

## Run the full pipeline

Run:

```powershell
python -m pip install -r requirements.txt
python scripts\run_official_rates_fx_inflation_pipeline.py
python scripts\run_curve_pricing_validation_harness.py
python scripts\run_one_page_curve_inflation_decision_report.py
python scripts\generate_model_risk_evidence.py
python -m pytest
```

Current validation state: **32 tests passing**.

---

## What this project does not claim

This repository does not claim access to proprietary OTC transaction data, XVA engines, internal bank curve-construction systems, confidential model libraries, Archer records or formal institutional model approval.

It is a public, reproducible and educational model-risk evidence package.

---

## Disclaimer

This project is for research, education and professional portfolio demonstration only. It does not provide investment advice, trading recommendations, regulatory validation or production model approval.

---

## Citation

Pereira, Rodolfo. (2026). *Quant Model Risk Lab: Open Model Validation, Monitoring and Risk Analytics in Python*. ShockBridge Pulse Research. Python research software. https://github.com/rolffcoelho-bravo/quant-model-risk-lab

### BibTeX

```bibtex
@software{pereira2026quantmodelrisklab,
  author = {Pereira, Rodolfo},
  title = {Quant Model Risk Lab: Open Model Validation, Monitoring and Risk Analytics in Python},
  year = {2026},
  publisher = {ShockBridge Pulse Research},
  type = {Python research software},
  url = {https://github.com/rolffcoelho-bravo/quant-model-risk-lab}
}
```

# Quant Model Risk Lab

**Open Model Validation, Official Rates, FX, Inflation and Risk Analytics Lab**

![Python](https://img.shields.io/badge/Python-3.12-blue)
[![Validation CI](https://github.com/rolffcoelho-bravo/quant-model-risk-lab/actions/workflows/validation-ci.yml/badge.svg?branch=main)](https://github.com/rolffcoelho-bravo/quant-model-risk-lab/actions/workflows/validation-ci.yml)
![Status](https://img.shields.io/badge/Status-Model%20Risk%20Evidence%20Lab-blue)
![Use](https://img.shields.io/badge/Use-Research%20Only-lightgrey)

**Publisher:** ShockBridge Pulse Research  
**Research site:** https://www.shockbridgepulse.com  
**Author:** Rodolfo Pereira  
**Repository type:** Public model-risk evidence package  
**Current release:** v0.8 interest-rate derivatives pricing validation
**Latest analytical artifacts:** v0.8 IR derivatives pricing validation dashboard; v0.7.1 ML model-risk decision intelligence dashboard; v0.6 inflation derivatives validation dashboard

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

## First-review ML artifacts

| Artifact | File | Purpose |
|---|---|---|
| IR derivatives pricing dashboard | `reports/figures/ir_derivatives_pricing_validation_map.png` | Fixed-for-floating swap valuation, par rate, NPV, DV01 and curve-shock sensitivity |
| ML decision dashboard | `reports/figures/ml_model_risk_monitoring_map.png` | ML model-risk monitoring, PCA drift, Mahalanobis abnormality and decision gate |
| IR derivatives pricing report | `reports/ir_derivatives_pricing_validation_report.md` | Swap pricing validation, bank decision, DV01, shock table and model lifecycle decision |
| IR model lifecycle register | `data/official/processed/ir_derivatives_model_lifecycle_register.csv` | Archer/MRM-style model lifecycle fields, monitoring trigger and next validation gate |
| ML monitoring report | `reports/ml_model_risk_monitoring_report.md` | Decision intelligence, model-use gate, bank action and investor action |

## v0.8 interest-rate derivatives pricing validation

The v0.8 layer makes derivatives pricing explicit. It validates a plain-vanilla fixed-for-floating interest-rate swap using official curve inputs from the repository data layer.

| Validation item | Evidence |
|---|---|
| Instrument | Fixed-for-floating interest-rate swap |
| Pricing output | Par swap rate, fixed-leg PV, floating-leg PV, payer NPV and receiver NPV |
| Sensitivity output | Payer DV01, receiver DV01 and parallel curve-shock table |
| Decision output | Allowed use, blocked use and validation boundary |
| Main script | `scripts/run_ir_derivatives_pricing_validation.py` |
| Main source module | `src/qmrl/ir_derivatives.py` |
| Main report | `reports/ir_derivatives_pricing_validation_report.md` |
| Main figure | `reports/figures/ir_derivatives_pricing_validation_map.png` |

This layer does not delete or replace the curve, inflation or ML layers. It extends the repository with an explicit derivatives-pricing validation control.

## Current release evidence

The current public release is **v0.8 interest-rate derivatives pricing validation**.

| Layer | Evidence |
|---|---|
| Official-data layer | Rates, FX and inflation public-data pipeline |
| Curve validation | Discount factors, bond pricing, DV01 and shock table |
| Inflation derivatives | BEI input mapping, inflation DV01, shock-value range and validation report |
| ML model-risk monitoring | z-score, shrinkage Mahalanobis distance, PCA drift and static regime classification |
| Decision intelligence | Allowed actions, blocked actions, escalation triggers, bank next action and investor next action |
| Test suite | 57 automated tests passing |

The ML layer is not a forecasting engine. It is a model-risk decision layer. It asks whether official rates, FX and inflation inputs are stable enough for model use, whether the current state requires enhanced review, and which decisions should be allowed or blocked.

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
| Inflation derivatives validation dashboard | Implemented |
| Inflation DV01 and BEI shock table | Implemented |
| ML model-risk feature layer | Implemented |
| Shrinkage Mahalanobis abnormality monitor | Implemented |
| PCA reconstruction-error drift monitor | Implemented |
| Static regime clustering | Implemented |
| ML decision intelligence gate | Implemented |
| Automated tests | 69 tests passing |

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
python scripts\run_inflation_derivatives_validation.py
python scripts\run_ml_model_risk_monitoring.py
python scripts\generate_model_risk_evidence.py
python -m pytest
```

Current validation state: **69 tests passing**.

---

## Next roadmap

Planned next layer:

| Version | Focus |
|---|---|
| v0.8 | Gaussian Mixture / Gaussian HMM challenger roadmap implementation |
| v0.9 | High-dimensional shrinkage, covariance drift and nonlinear monitoring |
| v1.0 | Consolidated model-risk evidence pack for interview review |

The next technical step should not replace the current transparent monitoring stack. It should add challenger evidence and explain when Gaussian regimes, hidden states or nonlinear anomaly tools are justified by the validation question.

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

## v0.8.1 Excel/VBA Revalidation Bridge

This layer demonstrates how the Python IR derivatives validation engine can be consumed by Excel/VBA review workflows.

Evidence added:
- excel_vba/vba/Revalidate_IR_Swap.bas
- excel_vba/exports/ir_swap_revalidation_control_panel.csv
- excel_vba/exports/ir_swap_revalidation_shock_table.csv
- excel_vba/exports/ir_swap_revalidation_lifecycle_record.csv
- excel_vba/templates/ir_swap_revalidation_template.xlsx
- scripts/export_ir_swap_excel_pack.py
- reports/excel_vba_revalidation_bridge.md
- tests/test_excel_vba_bridge.py

The bridge validates PV symmetry, DV01 sign, rate-shock direction and the model-use boundary. Python remains the pricing engine. Excel/VBA is the reviewer and legacy workflow interface.

## v0.9 XVA Validation Layer

This layer extends the clean IR swap validation engine into a transparent XVA review layer.

Evidence added:
- src/qmrl/xva.py
- scripts/run_xva_validation.py
- data/official/processed/xva_exposure_profile.csv
- data/official/processed/xva_summary.csv
- data/official/processed/xva_sensitivity_table.csv
- reports/xva_validation_report.md
- reports/figures/xva_validation_map.png
- tests/test_xva.py
- tests/test_xva_outputs.py

The layer computes scenario exposure, expected exposure, PFE, CVA, DVA, FVA and XVA sensitivities. It does not overclaim production XVA coverage. The next validation gate is time-grid exposure simulation with counterparty-specific calibration.

## v1.0 FX Derivatives Validation Layer

This layer adds a base Foreign Exchange derivatives validation layer using official USD/BRL and interest-rate inputs.

Evidence added:
- src/qmrl/fx_derivatives.py
- scripts/run_fx_derivatives_validation.py
- data/official/processed/fx_forward_validation_summary.csv
- data/official/processed/fx_forward_shock_table.csv
- data/official/processed/fx_model_lifecycle_register.csv
- reports/fx_forward_validation_report.md
- reports/figures/fx_forward_validation_map.png
- tests/test_fx_derivatives.py
- tests/test_fx_derivatives_outputs.py

The layer validates covered-interest-parity forward pricing, FX delta, long/short symmetry, spot-shock behaviour and the Archer/MRM lifecycle action. FX options, volatility surfaces and cross-currency basis remain the next validation gates.

## v1.1 FX Options Validation Layer

This layer adds vanilla Foreign Exchange option validation on top of the USD/BRL FX forward layer.

Evidence added:
- src/qmrl/fx_options.py
- scripts/run_fx_options_validation.py
- data/official/processed/fx_option_validation_summary.csv
- data/official/processed/fx_option_spot_vol_surface.csv
- data/official/processed/fx_option_put_call_parity_table.csv
- data/official/processed/fx_option_lifecycle_register.csv
- reports/fx_option_validation_report.md
- reports/figures/fx_option_validation_map.png
- tests/test_fx_options.py
- tests/test_fx_options_outputs.py

The layer validates Garman-Kohlhagen FX option pricing, Greeks, put-call parity, realised-volatility input, spot shocks, volatility shocks and Archer/MRM lifecycle action. SABR, volatility smile calibration, barrier options and path-dependent FX options remain the next validation gates.



## FX input remediation and option challenger

The USD/BRL forward and option layers now use a fail-closed market-input contract.

Evidence added:

- `src/qmrl/fx_market_inputs.py`
- `scripts/build_usd_brl_market_inputs.py`
- `data/official/processed/usd_brl_market_inputs.csv`
- `data/official/processed/usd_brl_market_input_manifest.json`
- `src/qmrl/fx_option_challenger.py`
- `scripts/run_fx_option_challenger_validation.py`
- `data/official/processed/fx_option_challenger_benchmark.csv`
- `reports/fx_option_challenger_validation_report.md`
- `docs/fx_option_validation_contract.md`
- `model_inventory/fx_option_remediation_register.csv`

The source contract requires BCB SGS series 1 for USD/BRL spot, BCB SGS series 432 for the BRL rate proxy and FRED DGS1 for the USD rate proxy.

The Garman-Kohlhagen implementation is challenged through a forward-based Black-76 formulation and finite-difference Greek verification.

Market option quote benchmarking remains explicitly open. The implementation challenger is not represented as evidence of market calibration.


## FX option volatility and monitoring governance

The FX-option layer now includes an externalized volatility-estimation contract, governed volatility floor, quantitative monitoring thresholds, ownership, alert evidence and automatic revalidation status.

Primary evidence:

- `configs/fx_option_governance_contract.json`
- `src/qmrl/fx_option_governance.py`
- `src/qmrl/fx_option_monitoring.py`
- `scripts/run_fx_option_monitoring.py`
- `data/official/processed/fx_option_monitoring_baseline.csv`
- `data/official/processed/fx_option_monitoring_status.csv`
- `reports/fx_option_monitoring_report.md`
- `docs/fx_option_volatility_monitoring_governance.md`

The controls are repository-level validation controls. They do not grant production approval or replace the open USD/BRL market-quote benchmark gate.


## Continuous integration validation

The repository runs its complete deterministic validation suite through GitHub Actions for every pull request targeting `main` and every push to `main`.

Primary evidence:

- `.github/workflows/validation-ci.yml`
- `docs/continuous_integration_policy.md`
- `tests/test_validation_ci_contract.py`
- GitHub Actions JUnit test artifact

The workflow uses Python 3.12, pip dependency caching, headless Matplotlib, deterministic numerical-thread controls and read-only repository permissions.

The workflow does not receive provider credentials and does not execute the controlled GenAI API call. GenAI schema, grounding and governance tests remain part of the deterministic CI suite.

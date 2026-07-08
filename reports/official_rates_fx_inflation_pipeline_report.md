# Official Rates, FX and Inflation Model-Risk Pipeline Report

## Executive summary

This report is generated from a real public official-data pipeline aligned with rates, FX, inflation and derivative-pricing model-risk workflows.

The pipeline downloads official interest-rate, inflation-compensation and FX data, stores raw files, builds processed panels, creates curve-validation summaries, computes FX return-risk metrics and generates reproducibility evidence through hashes and a manifest.

## Data sources

| Data block | Source |
|---|---|
| U.S. Treasury rates | FRED Treasury constant maturity series |
| Inflation compensation | FRED 10-year breakeven inflation |
| FX rates | ECB euro foreign exchange reference rates |

## Latest complete official-data row

| date | DGS1 | DGS2 | DGS5 | DGS10 | DGS30 | T10YIE | USD | GBP | JPY | CHF |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-07-06 00:00:00 | 3.950000 | 4.130000 | 4.210000 | 4.480000 | 4.990000 | 2.240000 | 1.141500 | 0.855380 | 185.310000 | 0.920100 |

## Curve validation summary

| maturity_years | yield_percent | discount_factor_simple |
| --- | --- | --- |
| 1.000000 | 3.950000 | 0.962001 |
| 2.000000 | 4.130000 | 0.922249 |
| 5.000000 | 4.210000 | 0.813679 |
| 10.000000 | 4.480000 | 0.645161 |
| 30.000000 | 4.990000 | 0.232040 |

## FX risk summary

| currency | observations | mean_return | volatility | historical_var_95 | worst_return | best_return |
| --- | --- | --- | --- | --- | --- | --- |
| USD | 7043 | 0.000012 | 0.005828 | 0.009348 | -0.046251 | 0.042938 |
| GBP | 7043 | 0.000038 | 0.004801 | 0.007289 | -0.029250 | 0.054246 |
| JPY | 7043 | 0.000071 | 0.007060 | 0.011425 | -0.059395 | 0.055445 |
| CHF | 7043 | -0.000072 | 0.003929 | 0.005065 | -0.144047 | 0.083251 |

## Model-risk interpretation

This pipeline does not claim access to proprietary OTC derivative trades, XVA production inputs, internal bank curve systems or confidential model inventories.

It builds the closest public validation harness: real official data, raw-data storage, processed panels, curve checks, FX risk summaries, reproducibility hashes and documentation. This supports model-risk reasoning for IR, FX and inflation workflows without pretending to replicate a bank production environment.

## Generated artifacts

- data/official/raw/fred_us_rates_inflation.csv
- data/official/raw/ecb_eurofxref_hist.zip
- data/official/raw/ecb_eurofxref_hist.csv
- data/official/processed/usd_treasury_curve_nodes.csv
- data/official/processed/breakeven_inflation_panel.csv
- data/official/processed/ecb_fx_panel.csv
- data/official/processed/official_rates_fx_inflation_panel.csv
- data/official/processed/fx_daily_returns.csv
- data/official/processed/curve_validation_summary.csv
- data/official/processed/fx_risk_summary.csv
- data/official/manifest.json

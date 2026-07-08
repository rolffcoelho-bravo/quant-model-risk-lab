# Official Rates, FX and Inflation Data Pipeline

This pipeline uses public official data aligned with model-risk validation for Treasury, rates, FX, inflation and derivative-pricing workflows.

## Data blocks

| Data block | Public source | Model-risk purpose |
|---|---|---|
| USD interest-rate curve | FRED Treasury constant maturity rates | IR curve construction, interpolation, discounting and rate sensitivity |
| EUR/USD FX rate | ECB euro foreign exchange reference rates | FX data validation, currency-risk inputs and FX valuation workflows |
| Inflation compensation | FRED 10-year breakeven inflation | Inflation-risk inputs and inflation-linked model review |

## Why this matters

The job profile asks for valuation and risk calculations, IR, FX and inflation derivatives, curve-building concepts, model validation, model monitoring, VaR, stress methodologies, documentation and Python automation.

Actual OTC derivative transaction data, XVA production inputs and bank curve-construction systems are usually not public. This repository does not pretend otherwise.

Instead, it builds the closest public validation harness:

1. Download real official data.
2. Store raw files.
3. Validate schema and missing values.
4. Build processed rate, FX and inflation panels.
5. Construct simple curve and risk summaries.
6. Generate model-risk evidence reports.
7. Run reproducibility tests.

## Data policy

No synthetic data is presented as market evidence. The pipeline uses public official data and stores raw and processed files for inspection.

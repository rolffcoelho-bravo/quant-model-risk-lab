# XVA Validation Report

## Purpose

This layer extends the clean IR swap validation engine into transparent XVA review.

The objective is not to claim a production XVA engine. The objective is to show the validation path: exposure profile, expected exposure, PFE, CVA, DVA, FVA, sensitivities and model-use decision.

## Acronyms

| Acronym | Meaning | Use in this layer |
|---|---|---|
| EE | Expected Exposure | Average positive exposure across rate-shock scenarios |
| PFE | Potential Future Exposure | High-percentile positive exposure proxy |
| CVA | Credit Valuation Adjustment | Counterparty default-risk charge |
| DVA | Debit Valuation Adjustment | Own default-risk valuation benefit |
| FVA | Funding Valuation Adjustment | Funding-spread adjustment on positive exposure |
| XVA | Valuation adjustment framework | Combined CVA, DVA and FVA review layer |

## Base XVA result

| Metric | Value |
|---|---:|
| Clean payer NPV | -111,654 |
| Expected exposure | 90,201 |
| Expected negative exposure | 207,380 |
| PFE 95 | 291,857 |
| Counterparty PD | 7.9956% |
| Own PD | 6.4493% |
| CVA | 3,499 |
| DVA | 6,488 |
| FVA | 1,823 |
| XVA reserve | -1,166 |
| XVA-adjusted payer value | -110,488 |

## Model-use decision

The XVA layer is available for transparent CVA, DVA and FVA review using the scenario exposure profile produced by the clean IR swap engine.

It is not a production exposure engine. The next validation gate is a time-grid exposure simulation with counterparty-specific credit calibration, collateral terms and netting-set treatment.

## Archer / MRM action

Create a linked XVA model record:

| Field | Record |
|---|---|
| Model ID | QMRL-XVA-IR-SWAP-001 |
| Source model | QMRL-IR-SWAP-001 |
| Product | Fixed-for-floating interest-rate swap |
| Stage | Transparent XVA validation layer |
| Monitoring trigger | Spread change, exposure sign change, funding spread change, recovery assumption change |
| Next gate | Time-grid EE/PFE simulation and counterparty-specific calibration |

## Sensitivity summary

| case                           |   counterparty_spread_bps |   own_spread_bps |   funding_spread_bps |   recovery_rate |   expected_exposure |   pfe_95 |     cva |      dva |     fva |   xva_reserve |   xva_adjusted_payer_value |
|:-------------------------------|--------------------------:|-----------------:|---------------------:|----------------:|--------------------:|---------:|--------:|---------:|--------:|--------------:|---------------------------:|
| base                           |                       100 |               80 |                   50 |             0.4 |             90201.3 |   291857 | 3498.81 |  6488.4  | 1823.31 |     -1166.28  |                    -110488 |
| counterparty_spread_plus_50bp  |                       150 |               80 |                   50 |             0.4 |             90201.3 |   291857 | 5141.87 |  6488.4  | 1823.31 |       476.777 |                    -112131 |
| counterparty_spread_minus_50bp |                        50 |               80 |                   50 |             0.4 |             90201.3 |   291857 | 1785.85 |  6488.4  | 1823.31 |     -2879.25  |                    -108775 |
| own_spread_plus_50bp           |                       100 |              130 |                   50 |             0.4 |             90201.3 |   291857 | 3498.81 | 10329.4  | 1823.31 |     -5007.28  |                    -106647 |
| funding_spread_plus_25bp       |                       100 |               80 |                   75 |             0.4 |             90201.3 |   291857 | 3498.81 |  6488.4  | 2734.97 |      -254.626 |                    -111399 |
| recovery_20pct                 |                       100 |               80 |                   50 |             0.2 |             90201.3 |   291857 | 3535    |  6542.17 | 1823.31 |     -1183.86  |                    -110470 |
| recovery_60pct                 |                       100 |               80 |                   50 |             0.6 |             90201.3 |   291857 | 3427.91 |  6382.64 | 1823.31 |     -1131.41  |                    -110523 |

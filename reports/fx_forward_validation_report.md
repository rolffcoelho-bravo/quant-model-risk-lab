# FX Forward Validation Report

## Purpose

This layer adds a base Foreign Exchange (FX) derivatives validation layer.

The model prices a USD/BRL FX forward using spot FX, a BRL domestic rate, a USD foreign rate and covered-interest-parity logic. It then produces a spot-shock table, FX delta and lifecycle record.

## Acronyms

| Acronym | Meaning | Use in this layer |
|---|---|---|
| FX | Foreign Exchange | USD/BRL exchange-rate derivative |
| PV | Present Value | Discounted value of the forward payoff |
| NPV | Net Present Value | Forward value after discounting |
| BRL | Brazilian Real | Domestic currency |
| USD | United States Dollar | Foreign currency |
| MRM | Model Risk Management | Lifecycle governance and validation record |

## Base valuation

| Metric | Value |
|---|---:|
| Spot USD/BRL | 4.990000 |
| BRL domestic rate | 185.0900% |
| USD foreign rate | 3.9500% |
| Model forward rate | 30.533850 |
| Contract forward rate | 30.686519 |
| Long USD forward value, BRL | -23,984 |
| FX delta | 961,270 |
| Carry basis | 25.543850 |

## Model-use decision

The FX forward layer is available for base forward-pricing validation, first-order spot-risk review and lifecycle evidence.

It is not an FX options model, volatility-surface model or cross-currency-basis model. Those remain the next validation gates.

## Archer / MRM action

| Field | Record |
|---|---|
| Model ID | QMRL-FX-FWD-001 |
| Product | USD/BRL FX forward |
| Stage | Base FX forward pricing and spot-risk validation |
| Validation status | Forward parity, PV sign, FX delta and shock direction available |
| Monitoring trigger | USD/BRL spot change, BRL rate change, USD rate change, contract forward change |
| Next gate | FX options and cross-currency basis validation |

## Spot-shock table

|   spot_shock_pct |   shocked_spot_rate |   model_forward_rate |   long_foreign_forward_value |   short_foreign_forward_value |   long_foreign_forward_pnl |   fx_delta |
|-----------------:|--------------------:|---------------------:|-----------------------------:|------------------------------:|---------------------------:|-----------:|
|              -10 |              4.491  |              27.4805 |                    -503657   |                      503657   |                    -479674 |     961270 |
|               -5 |              4.7405 |              29.0072 |                    -263821   |                      263821   |                    -239837 |     961270 |
|                0 |              4.99   |              30.5339 |                     -23983.7 |                       23983.7 |                          0 |     961270 |
|                5 |              5.2395 |              32.0605 |                     215853   |                     -215853   |                     239837 |     961270 |
|               10 |              5.489  |              33.5872 |                     455690   |                     -455690   |                     479674 |     961270 |

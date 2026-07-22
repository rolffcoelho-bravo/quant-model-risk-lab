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
| Spot USD/BRL, BRL per USD | 5.167000 |
| BRL domestic rate | 14.2500% |
| USD foreign rate | 3.9500% |
| Model forward rate, BRL per USD | 5.727575 |
| Contract forward rate | 5.756213 |
| Long USD forward value, BRL | -24,834 |
| FX delta | 961,270 |
| Carry basis | 0.560575 |

## Model-use decision

The FX forward layer is available for governed base forward-pricing validation, first-order spot-risk review and lifecycle evidence.

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
|              -10 |             4.6503  |              5.15482 |                    -521523   |                      521523   |                    -496688 |     961270 |
|               -5 |             4.90865 |              5.4412  |                    -273179   |                      273179   |                    -248344 |     961270 |
|                0 |             5.167   |              5.72758 |                     -24834.4 |                       24834.4 |                          0 |     961270 |
|                5 |             5.42535 |              6.01395 |                     223510   |                     -223510   |                     248344 |     961270 |
|               10 |             5.6837  |              6.30033 |                     471854   |                     -471854   |                     496688 |     961270 |

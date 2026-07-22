# FX Options Validation Report

## Purpose

This layer adds vanilla FX option validation on top of the USD/BRL FX forward layer.

The pricing engine uses the Garman-Kohlhagen lognormal FX option model. The validation evidence covers call and put values, Greeks, put-call parity, spot shocks, volatility shocks and model lifecycle controls.

## Acronyms

| Acronym | Meaning | Use in this layer |
|---|---|---|
| FX | Foreign Exchange | USD/BRL option exposure |
| GK | Garman-Kohlhagen | Lognormal FX option pricing model |
| PV | Present Value | Discounted option premium |
| Delta | Spot sensitivity | First-order FX risk |
| Gamma | Delta convexity | Second-order spot risk |
| Vega | Volatility sensitivity | Volatility-risk control |
| SABR | Stochastic Alpha Beta Rho | Next smile-calibration gate |
| MRM | Model Risk Management | Lifecycle governance record |

## Base valuation

| Metric | Value |
|---|---:|
| Spot USD/BRL, BRL per USD | 5.167000 |
| Strike, BRL per USD | 5.727575 |
| Model forward, BRL per USD | 5.727575 |
| BRL domestic rate | 14.2500% |
| USD foreign rate | 3.9500% |
| Realised volatility input | 10.4731% |
| Call value, BRL | 207,429 |
| Put value, BRL | 207,429 |
| Call delta | 500,708 |
| Put delta | -460,562 |
| Call gamma | 707,696 |
| Call vega | 1,978,784 |
| Put-call parity gap | 0.000000 |

## Put-call parity control

| Check | Status | Gap |
|---|---|---:|
| Put-call parity | PASS | 0.000000 |

## Model-use decision

The layer is available for governed validation review of vanilla European USD/BRL FX option pricing, Greeks, put-call parity and first-order scenario review.

It is not a smile-calibrated volatility-surface model, SABR model, barrier-option model or path-dependent option engine. Those remain the next validation gates.

## Archer / MRM action

| Field | Record |
|---|---|
| Model ID | QMRL-FX-OPT-001 |
| Product | USD/BRL European FX option |
| Stage | Vanilla FX option validation |
| Validation status | Garman-Kohlhagen price, Greeks, put-call parity, spot and volatility shocks available |
| Monitoring trigger | spot move, realised volatility change, rate change, parity gap, delta/vega sign change |
| Next gate | SABR smile and path-dependent FX option validation |

## Spot and volatility shock surface

|   spot_shock_pct |   vol_shock_abs |   shocked_spot_rate |   volatility |   call_value_domestic |   put_value_domestic |   call_delta |   put_delta |        call_vega |         put_vega |   put_call_parity_gap |
|-----------------:|----------------:|--------------------:|-------------:|----------------------:|---------------------:|-------------:|------------:|-----------------:|-----------------:|----------------------:|
|              -10 |           -0.05 |             4.6503  |    0.0547309 |               2669.67 |            499358    |      27749.9 |   -933520   | 294601           | 294601           |          -2.91038e-10 |
|              -10 |            0    |             4.6503  |    0.104731  |              40611.6  |            537300    |     163542   |   -797728   |      1.13176e+06 |      1.13176e+06 |           5.82077e-11 |
|              -10 |            0.05 |             4.6503  |    0.154731  |             107398    |            604086    |     262492   |   -698778   |      1.48639e+06 |      1.48639e+06 |          -4.65661e-10 |
|               -5 |           -0.05 |             4.90865 |    0.0547309 |              24838.9  |            273183    |     174430   |   -786840   |      1.24442e+06 |      1.24442e+06 |          -2.32831e-10 |
|               -5 |            0    |             4.90865 |    0.104731  |             101826    |            350170    |     318095   |   -643174   |      1.7107e+06  |      1.7107e+06  |          -2.91038e-11 |
|               -5 |            0.05 |             4.90865 |    0.154731  |             190688    |            439032    |     384216   |   -577054   |      1.82261e+06 |      1.82261e+06 |          -2.03727e-10 |
|                0 |           -0.05 |             5.167   |    0.0547309 |             108436    |            108436    |     491128   |   -470142   |      1.98076e+06 |      1.98076e+06 |          -4.51621e-10 |
|                0 |            0    |             5.167   |    0.104731  |             207429    |            207429    |     500708   |   -460562   |      1.97878e+06 |      1.97878e+06 |           8.87155e-10 |
|                0 |            0.05 |             5.167   |    0.154731  |             306294    |            306294    |     510274   |   -450996   |      1.97558e+06 |      1.97558e+06 |           4.50598e-10 |
|                5 |           -0.05 |             5.42535 |    0.0547309 |             276754    |             28410    |     789111   |   -172158   |      1.36415e+06 |      1.36415e+06 |          -5.52973e-10 |
|                5 |            0    |             5.42535 |    0.104731  |             359424    |            111080    |     670822   |   -290448   |      1.81914e+06 |      1.81914e+06 |           0           |
|                5 |            0.05 |             5.42535 |    0.154731  |             453568    |            205224    |     627445   |   -333825   |      1.92619e+06 |      1.92619e+06 |           6.69388e-10 |
|               10 |           -0.05 |             5.6837  |    0.0547309 |             501397    |              4708.76 |     924296   |    -36974.2 | 456048           | 456048           |           0           |
|               10 |            0    |             5.6837  |    0.104731  |             550434    |             53745.8  |     799853   |   -161417   |      1.37169e+06 |      1.37169e+06 |          -5.82077e-10 |
|               10 |            0.05 |             5.6837  |    0.154731  |             628933    |            132245    |     726674   |   -234596   |      1.71396e+06 |      1.71396e+06 |          -2.91038e-10 |

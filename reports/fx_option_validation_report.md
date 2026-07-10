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
| Spot USD/BRL | 4.990000 |
| Strike | 30.533850 |
| Model forward | 30.533850 |
| BRL domestic rate | 185.0900% |
| USD foreign rate | 3.9500% |
| Realised volatility input | 12.2241% |
| Call value, BRL | 233,777 |
| Put value, BRL | 233,777 |
| Call delta | 504,060 |
| Put delta | -457,210 |
| Call gamma | 627,520 |
| Call vega | 1,910,050 |
| Put-call parity gap | 0.000000 |

## Put-call parity control

| Check | Status | Gap |
|---|---|---:|
| Put-call parity | PASS | 0.000000 |

## Model-use decision

The layer is valid for vanilla European USD/BRL FX option pricing, Greeks, put-call parity and first-order scenario review.

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
|              -10 |           -0.05 |              4.491  |    0.0722408 |               10579   |             490253   |      74463.2 |   -886807   | 626321           | 626321           |           1.16415e-10 |
|              -10 |            0    |              4.491  |    0.122241  |               59807.5 |             539481   |     203430   |   -757839   |      1.24983e+06 |      1.24983e+06 |          -2.91038e-10 |
|              -10 |            0.05 |              4.491  |    0.172241  |              129447   |             609120   |     287985   |   -673285   |      1.50008e+06 |      1.50008e+06 |          -4.65661e-10 |
|               -5 |           -0.05 |              4.7405 |    0.0722408 |               47424.8 |             287262   |     240494   |   -720776   |      1.44864e+06 |      1.44864e+06 |          -2.91038e-11 |
|               -5 |            0    |              4.7405 |    0.122241  |              127761   |             367598   |     346047   |   -615223   |      1.7048e+06  |      1.7048e+06  |          -2.32831e-10 |
|               -5 |            0.05 |              4.7405 |    0.172241  |              215138   |             454975   |     400060   |   -561210   |      1.77766e+06 |      1.77766e+06 |          -4.07454e-10 |
|                0 |           -0.05 |              4.99   |    0.0722408 |              138211   |             138211   |     494484   |   -466786   |      1.91237e+06 |      1.91237e+06 |           4.50598e-10 |
|                0 |            0    |              4.99   |    0.122241  |              233777   |             233777   |     504060   |   -457210   |      1.91005e+06 |      1.91005e+06 |           4.50598e-10 |
|                0 |            0.05 |              4.99   |    0.172241  |              329197   |             329197   |     513621   |   -447649   |      1.90654e+06 |      1.90654e+06 |           4.31442e-11 |
|                5 |           -0.05 |              5.2395 |    0.0722408 |              292700   |              52862.8 |     732116   |   -229154   |      1.55997e+06 |      1.55997e+06 |           2.32831e-10 |
|                5 |            0    |              5.2395 |    0.122241  |              378349   |             138512   |     651099   |   -310171   |      1.80737e+06 |      1.80737e+06 |          -4.65661e-10 |
|                5 |            0.05 |              5.2395 |    0.172241  |              470756   |             230919   |     619135   |   -342135   |      1.87679e+06 |      1.87679e+06 |          -2.91038e-11 |
|               10 |           -0.05 |              5.489  |    0.0722408 |              495544   |              15870.3 |     877029   |    -84241.2 | 840020           | 840020           |           1.16415e-09 |
|               10 |            0    |              5.489  |    0.122241  |              556197   |              76523.7 |     768798   |   -192472   |      1.4782e+06  |      1.4782e+06  |          -2.91038e-10 |
|               10 |            0.05 |              5.489  |    0.172241  |              636927   |             157254   |     710131   |   -251139   |      1.71574e+06 |      1.71574e+06 |           4.07454e-10 |

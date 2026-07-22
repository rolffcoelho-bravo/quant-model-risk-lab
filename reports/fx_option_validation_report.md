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
| Realised volatility input | 19.0528% |
| Call value, BRL | 376,962 |
| Put value, BRL | 376,962 |
| Call delta | 517,113 |
| Put delta | -444,157 |
| Call gamma | 387,781 |
| Call vega | 1,972,528 |
| Put-call parity gap | -0.000000 |

## Put-call parity control

| Check | Status | Gap |
|---|---|---:|
| Put-call parity | PASS | -0.000000 |

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

|   spot_shock_pct |   vol_shock_abs |   shocked_spot_rate |   volatility |   call_value_domestic |   put_value_domestic |   call_delta |   put_delta |   call_vega |    put_vega |   put_call_parity_gap |
|-----------------:|----------------:|--------------------:|-------------:|----------------------:|---------------------:|-------------:|------------:|------------:|------------:|----------------------:|
|              -10 |           -0.05 |             4.6503  |     0.140528 |               86769.1 |               583457 |       238795 |     -722475 | 1.41573e+06 | 1.41573e+06 |          -2.32831e-10 |
|              -10 |            0    |             4.6503  |     0.190528 |              162948   |               659637 |       311042 |     -650228 | 1.60598e+06 | 1.60598e+06 |          -2.32831e-10 |
|              -10 |            0.05 |             4.6503  |     0.240528 |              245744   |               742432 |       360792 |     -600478 | 1.69554e+06 | 1.69554e+06 |          -5.23869e-10 |
|               -5 |           -0.05 |             4.90865 |     0.140528 |              164938   |               413282 |       369221 |     -592049 | 1.80241e+06 | 1.80241e+06 |           2.32831e-10 |
|               -5 |            0    |             4.90865 |     0.190528 |              256561   |               504905 |       414261 |     -547009 | 1.85416e+06 | 1.85416e+06 |          -4.36557e-10 |
|               -5 |            0.05 |             4.90865 |     0.240528 |              349850   |               598194 |       445026 |     -516244 | 1.8743e+06  | 1.8743e+06  |          -2.91038e-11 |
|                0 |           -0.05 |             5.167   |     0.140528 |              278228   |               278228 |       507559 |     -453711 | 1.97661e+06 | 1.97661e+06 |          -1.50635e-11 |
|                0 |            0    |             5.167   |     0.190528 |              376962   |               376962 |       517113 |     -444157 | 1.97253e+06 | 1.97253e+06 |          -1.50635e-11 |
|                0 |            0.05 |             5.167   |     0.240528 |              475460   |               475460 |       526644 |     -434626 | 1.96722e+06 | 1.96722e+06 |           4.50598e-10 |
|                5 |           -0.05 |             5.42535 |     0.140528 |              426341   |               177997 |       636195 |     -325075 | 1.90696e+06 | 1.90696e+06 |          -4.65661e-10 |
|                5 |            0    |             5.42535 |     0.190528 |              523117   |               274772 |       612650 |     -348620 | 1.95604e+06 | 1.95604e+06 |           2.32831e-10 |
|                5 |            0.05 |             5.42535 |     0.240528 |              621460   |               373116 |       602422 |     -358848 | 1.97475e+06 | 1.97475e+06 |           5.82077e-11 |
|               10 |           -0.05 |             5.6837  |     0.140528 |              605045   |               108357 |       742983 |     -218287 | 1.64715e+06 | 1.64715e+06 |          -2.91038e-10 |
|               10 |            0    |             5.6837  |     0.190528 |              692478   |               195790 |       696197 |     -265073 | 1.82549e+06 | 1.82549e+06 |          -5.82077e-11 |
|               10 |            0.05 |             5.6837  |     0.240528 |              786044   |               289356 |       670249 |     -291021 | 1.90745e+06 | 1.90745e+06 |           5.82077e-11 |

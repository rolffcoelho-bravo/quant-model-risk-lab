# ML Model-Risk Monitoring Report

## Decision state: Enhanced model-risk review

**Monitoring date:** 2026-07-06  
**ML pressure score:** 77.8 / 100  
**Decision flags:** no major ML monitoring threshold breach  
**Static regime:** Normal input regime

![ML model-risk monitoring map](figures/ml_model_risk_monitoring_map.png)

## Direct interpretation

This layer does not forecast markets. It creates a model-risk decision gate.

**Decision gate: AMBER REVIEW.**

Use the ML output as a monitoring control only. Do not use it to approve new exposure, change limits or recalibrate thresholds automatically.

Why this is Amber:

- The maximum z-score is below a hard single-input breach.
- Mahalanobis distance is elevated, but below the 95th-percentile stop-review level.
- PCA drift is the main warning because the recent input factor structure changed.
- The static regime remains normal, so this is not a full stress-state failure.

## Latest signals

| Signal | Value |
|---|---:|
| Max absolute rolling z-score | 1.905 |
| Main z-score feature | real_rate_proxy |
| Mahalanobis distance | 2.963 |
| Mahalanobis percentile | 83.7 |
| PCA reconstruction error | 0.963 |
| PCA error percentile | 89.7 |
| Static regime | Normal input regime |

## Model-selection table

| Validation question | Primary tool | Challenger tool | Implemented in v0.7 | Rationale |
|---|---|---|---:|---|
| Is the current input move abnormal in one variable? | Rolling z-score | Rolling percentile rank | True | Useful for direct input-level breaches and easy validation audit trails. |
| Is the joint rates, FX and inflation state abnormal? | Shrinkage Mahalanobis distance | Robust covariance / Elliptic Envelope | True | Captures covariance-adjusted multivariate abnormality with stabilized covariance estimates. |
| Has the input factor structure drifted? | PCA reconstruction error | Kernel PCA | True | Detects whether current inputs are poorly explained by the recent factor structure. |
| Which static monitoring regime is active? | KMeans regime clustering | Gaussian Mixture Model | True | Provides a transparent static input-regime classification for monitoring reports. |
| Is there nonlinear anomaly behavior beyond distance metrics? | Isolation Forest | Local Outlier Factor | False | Planned challenger for nonlinear anomaly detection once dependency policy is expanded. |
| Is the system switching dynamically between latent regimes? | Gaussian Hidden Markov Model | Kalman/state-space model | False | Reserved for the dynamic regime layer after static monitoring is validated. |

## Bank implication

Keep reporting active, but freeze automatic threshold changes, production recalibration and new limit-use signoff from this ML layer. Decompose the PCA drift into rates, BEI, real-rate proxy and FX drivers, then rerun the stack under 126D and 252D windows. Escalate only if PCA drift persists across refreshes, Mahalanobis distance crosses the 95th percentile, or the maximum z-score breaches the hard single-input threshold.

## Investor implication

Do not increase exposure from this ML signal. Use the curve dashboard and the inflation-derivatives dashboard to decide exposure direction. If those dashboards confirm the exposure direction, keep sizing disciplined because the ML layer shows reduced model confidence. If confirmation is weak or contradictory, reduce sizing, widen risk bands or delay the trade.

## Validator challenge

Challenge whether the selected tool matches the validation question. A univariate breach should not be treated the same as covariance instability. PCA drift should not be treated as a trading signal. KMeans regime labels are static monitoring labels, not causal explanations. Isolation Forest and Gaussian HMM remain challenger roadmap tools until separately implemented and tested.

## Limitations

This v0.7 layer uses transparent dependency-light diagnostics: rolling z-scores, percentile ranks, shrinkage Mahalanobis distance, PCA reconstruction error and deterministic KMeans clustering. It does not yet implement Isolation Forest, Gaussian Mixture Models or Gaussian Hidden Markov Models.

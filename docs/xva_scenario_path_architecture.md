# XVA Scenario-Path and Future-Value Architecture

## Gate 2 objective

Gate 2 adds governed stochastic market-factor paths and pathwise future clean values on top of the deterministic Gate 1 exposure foundation.

The implementation is designed to answer a narrow validation question:

> Can the repository generate reproducible, correlated future market states and convert them into inspectable trade and portfolio clean-value paths without mixing simulation, credit calibration, collateral, or final XVA attribution?

Gate 2 is not a production Monte Carlo engine. It is a public validation layer with explicit model boundaries.

## Architecture

```text
Governed calibration inputs
        |
        v
Risk-factor contract and ordered dependence matrix
        |
        v
Seeded PCG64 random-number control
        |
        v
Antithetic independent innovations
        |
        v
Correlation transformation
        |
        v
GBM FX, Vasicek rate, and deterministic factor paths
        |
        v
Scenario cube: path x time x factor
        |
        v
Transparent valuation adapters
        |
        v
Future-value cube: path x time x trade
        |
        v
Portfolio clean-value paths
        |
        v
Convergence and analytical challenger evidence
        |
        v
Human validation decision
```

## Risk-factor definitions

Each factor has an explicit:

- name
- factor type
- model
- initial value
- drift
- volatility
- mean-reversion speed
- long-run mean
- currency
- calibration source
- calibration as-of date

Supported Gate 2 models are:

- geometric Brownian motion for positive FX spot factors
- exact-transition Vasicek dynamics for short-rate factors
- deterministic additive paths for locked controls and benchmark cases

The factor order is contractual because it defines the row and column order of the dependence matrix and the factor dimension of the scenario cube.

## Dependence controls

The correlation matrix must be:

- square
- finite
- symmetric
- bounded within minus one and one
- unit diagonal
- positive semidefinite
- dimensionally consistent with the ordered factor set

A symmetric eigenvalue square root is used so positive-semidefinite matrices remain admissible even when they are not strictly positive definite.

Gate 2 does not estimate the correlation matrix from scenario output. Calibration is external to forward simulation.

## Random-number and variance-reduction controls

The random-number contract fixes:

- PCG64 as the bit generator
- an explicit non-negative seed
- float64 numerical representation
- the number of paths
- the number of time steps
- the ordered number of factors
- antithetic variates as the first variance-reduction method

Antithetic simulation requires an even path count. Every base innovation has an exact negative pair.

A scenario manifest records the seed, path count, time count, factor order, calibration metadata, model version, and SHA-256 content hash.

## Scenario cube

The scenario cube is indexed by:

1. path
2. time
3. factor

The time dimension must:

- start at zero
- be finite
- be strictly increasing
- contain at least two observations

The factor dimension follows the governed factor order.

Scenario arrays are immutable after construction.

## FX scenario generation

FX spot factors use the exact geometric Brownian transition:

\[
S_{t+\Delta t}
=
S_t
\exp\left[
\left(\mu-\frac{1}{2}\sigma^2\right)\Delta t
+
\sigma\sqrt{\Delta t}Z
\right].
\]

This guarantees positive simulated spot values.

The drift and volatility are external governed inputs. Gate 2 does not claim a production risk-neutral calibration, local-volatility surface, stochastic volatility model, or cross-currency basis model.

## Interest-rate scenario generation

Short-rate factors use the exact Vasicek transition when the mean-reversion parameter is positive:

\[
r_{t+\Delta t}
=
\theta
+
(r_t-\theta)e^{-\kappa\Delta t}
+
\sigma
\sqrt{
\frac{1-e^{-2\kappa\Delta t}}{2\kappa}
}
Z.
\]

The zero-mean-reversion limit is represented as an additive Gaussian process with explicit drift.

Gate 2 does not construct a production multi-curve interest-rate model. Multiple rate factors may be represented, but curve calibration and arbitrage-free term-structure reconstruction remain separate controls.

## Future-value cube

The future-value cube is indexed by:

1. path
2. time
3. trade

The portfolio value is the exact sum across the trade dimension.

Gate 2 includes transparent public valuation adapters for:

- an FX forward using simulated spot and flat residual domestic and foreign rates
- a zero-coupon cash flow using the simulated short rate as a flat residual discounting proxy

These adapters are intentionally inspectable. They are challenger-ready public controls, not production curve or pricing implementations.

Required controls include:

- unique trade identifiers
- maturity within the scenario horizon
- finite pathwise values
- portfolio aggregation equality
- immutable output arrays

## Convergence diagnostics

The convergence layer reports:

- governed sample sizes
- running estimates
- standard errors
- confidence-interval half widths
- final estimate
- final standard error
- relative and absolute tolerances
- a transparent stability flag

A stable estimate does not constitute model approval. It only shows that the selected estimator meets the configured Monte Carlo precision control under the supplied model and sample.

## Analytical challengers

Independent analytical moment controls are supplied for:

- geometric Brownian motion
- Vasicek short-rate dynamics
- deterministic factors

The challenger compares simulated terminal mean and variance with the corresponding analytical moments.

The benchmark suite also validates:

- exact seed reproducibility
- antithetic zero-mean innovations
- recovery of a target correlation
- deterministic paths
- scenario-manifest metadata and hash length
- pathwise future-value aggregation

## Calibration and simulation separation

Gate 2 enforces the following direction:

```text
Historical or external calibration
        |
        v
Locked simulation parameters
        |
        v
Forward scenario generation
```

The reverse direction is prohibited. Scenario outputs cannot silently recalibrate:

- drift
- volatility
- mean reversion
- long-run mean
- correlation
- valuation assumptions

Calibration source and as-of metadata are retained in the factor set and scenario manifest.

## Validation boundaries

Gate 2 does not include:

- production historical calibration
- market-consistent or risk-neutral calibration approval
- stochastic volatility
- local volatility
- jump diffusion
- Hull-White or multifactor term-structure calibration
- optionality or path-dependent trade valuation
- counterparty PD or LGD calibration
- wrong-way-risk dependence
- collateral integration with simulated clean values
- CVA, DVA, or FVA attribution from the new scenario cube
- legal enforceability evidence
- production approval

## Promotion rule

Gate 2 may be treated as complete only when:

- seeded reproducibility tests pass
- correlation controls pass
- analytical moment challengers pass
- valuation-adapter tests pass
- scenario benchmark cases pass
- all Gate 1 and legacy XVA tests remain green
- the complete repository suite passes
- the required GitHub Actions check passes
- human review approves the pull request

The next gate is pathwise netting, collateral, and exposure integration.

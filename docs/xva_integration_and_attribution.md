# XVA Integration and Attribution Architecture

## Gate 5 objective

Gate 5 combines the collateralized exposure profiles validated in Gate 3 with the counterparty and own-credit term structures validated in Gate 4. It produces transparent CVA, DVA, FCA, FBA, net FVA, and total valuation-adjustment evidence.

Gate 5 is not a production XVA engine. It is a public validation layer with explicit sign conventions, attribution, challenger calculations, sensitivities, and human-review boundaries.

## Component definitions

For interval \((t_{i-1},t_i]\), discount factor \(D_i\), counterparty loss given default \(LGD_c\), own loss given default \(LGD_o\), expected positive exposure \(EE_i^+\), and expected negative exposure \(EE_i^-\):

\[
CVA = \sum_i D_i EE_i^+ LGD_c \Delta PD_{c,i} S_o(t_i)
\]

\[
DVA = \sum_i D_i EE_i^- LGD_o \Delta PD_{o,i} S_c(t_i)
\]

The survival multipliers are used in bilateral first-to-default mode. Unilateral CVA omits own survival and sets DVA to zero.

Funding components are:

\[
FCA = \sum_i D_i F_i^+ s_i^{borrow} \Delta t_i
\]

\[
FBA = \sum_i D_i F_i^- s_i^{lend} \Delta t_i
\]

\[
FVA = FCA - FBA
\]

The clean-value adjustment sign convention is:

\[
XVA_{adjustment} = -CVA + DVA - FCA + FBA
\]

## Discount and funding controls

Discount factors must start at one, remain positive, and be non-increasing. Interpolation is log-linear in discount factors. Extrapolation is either forbidden or based on the terminal zero rate.

Funding curves separate borrowing cost and lending benefit. Both are non-negative and the lending benefit cannot exceed the borrowing spread. Gate 5 supports collateralized or MPOR exposure as the funding basis.

## Attribution hierarchy

Every component is retained at five levels:

1. time bucket
2. legal netting set
3. counterparty
4. portfolio
5. governed trade allocation

No exposure or XVA offset is permitted across distinct legal netting sets. Trade allocation uses explicit non-negative component weights that sum to one within each netting set.

## Independent challenger and reconciliation

The primary engine is vectorized. A separate loop-based challenger recalculates every interval and netting set. Reconciliation tests cover:

- vectorized versus loop components
- bucket-to-netting-set totals
- netting-set-to-counterparty totals
- counterparty-to-portfolio totals
- CVA, DVA, FCA, FBA, FVA, and total-adjustment sign identities
- trade allocation back to portfolio totals

## Sensitivity evidence

Standard one-factor-at-a-time sensitivities cover:

- counterparty spread
- own spread
- counterparty recovery
- own recovery
- borrowing spread
- lending spread
- discount rate

Credit sensitivities use an explicit LGD-consistent piecewise-hazard approximation. This is a challenger control, not a substitute for full market recalibration.

## Deterministic benchmark framework

Locked Gate 5 cases cover unilateral CVA, bilateral CVA, DVA, FCA, FBA, total sign reconciliation, netting-set attribution, counterparty attribution, trade allocation, independent challenger reconciliation, and sensitivity direction.

## Validation boundaries

Gate 5 does not include:

- wrong-way-risk dependence
- correlated default simulation
- stressed exposure-credit coupling
- replacement closeout recursion
- market-observed funding calibration
- legal enforceability opinions
- production collateral or counterparty feeds
- production approval

Wrong-way risk, stress scenarios, and dependence controls remain Gate 6.

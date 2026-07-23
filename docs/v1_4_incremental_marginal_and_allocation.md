# v1.4 Gate 5 — Incremental, Marginal, and Allocation Analytics

Gate 5 measures how trades and portfolio changes contribute to valuation adjustment and capital use while preserving full revaluation as the authoritative reference.

## Scope

The layer supports:

- trade insertion, removal, and replacement;
- full-revaluation increments for CVA, DVA, FCA, FBA, FVA, MVA, KVA, WWR uplift, stress adjustment, and total adjustment;
- central finite-difference marginal analytics;
- bump-refinement convergence diagnostics;
- Euler-style allocation only when positive homogeneity is validated;
- leave-one-out allocation for nonlinear portfolios;
- trade, counterparty, netting-set, currency, and product-family attribution;
- concentration and ranking diagnostics;
- independent challenger reconciliation.

## Sign convention

Component magnitudes use the established clean-value identity:

\[
\text{Total Adjustment}
=
-\mathrm{CVA}
+\mathrm{DVA}
-\mathrm{FCA}
+\mathrm{FBA}
-\mathrm{MVA}
-\mathrm{KVA}
-\mathrm{WWR\ Uplift}
+\mathrm{StressAdjustment}.
\]

FVA remains \(\mathrm{FCA}-\mathrm{FBA}\). MVA is not embedded in FVA.

## Full-revaluation increments

For insertion of trade \(j\):

\[
\Delta XVA_j
=
XVA(P \cup \{j\}) - XVA(P).
\]

For removal:

\[
\Delta XVA^{remove}_j
=
XVA(P \setminus \{j\}) - XVA(P).
\]

The base result, changed result, and component delta are retained.

## Marginal analytics

A central finite difference estimates:

\[
\frac{\partial XVA}{\partial w_j}
\approx
\frac{XVA(w_j+h)-XVA(w_j-h)}{2h}.
\]

Gate 5 repeats the calculation at half the bump and reports convergence error. When requested, it compares the approximation with the full-revaluation leave-one-out contribution.

Approximate results never replace the full-revaluation record without status and error disclosure.

## Euler validity

Euler allocation is permitted only when the portfolio passes:

- positive-homogeneity reconciliation;
- threshold absence;
- MTA absence;
- concentration-add-on absence;
- collateral-regime-switch absence.

If any control fails, the Euler result is marked `INVALID`; the platform does not present it as an authoritative allocation.

## Residual reconciliation

For every allocation:

\[
\sum_i Allocation_i + Residual = PortfolioResult.
\]

Residuals are explicit component vectors and are never hidden.

## Boundaries

The layer retains:

`FULL_REVALUATION_PRIMARY_APPROXIMATION_DISCLOSED`

It does not provide production pricing, regulatory approval, certified capital allocation, or legally binding transfer pricing.

# IR Derivatives Model Lifecycle Decision Report

## Acronyms

| Acronym | Meaning |
|---|---|
| IR | Interest Rate |
| FX | Foreign Exchange |
| PV | Present Value |
| NPV | Net Present Value |
| DV01 | Dollar value change for a one-basis-point rate move |
| bp | Basis point |
| XVA | Valuation adjustment framework |
| CVA | Credit Valuation Adjustment |
| DVA | Debit Valuation Adjustment |
| FVA | Funding Valuation Adjustment |
| MRM | Model Risk Management |
| MMMRC | Model risk committee / model management review committee context |
| Archer | Model-risk system of record |

## Model-use decision

**Decision:** base IR swap pricing and rate-risk validation passes.

This result supports a model-risk evidence record for a plain-vanilla fixed-for-floating interest-rate swap. It does not complete the full derivatives model stack. The next required gate is XVA.

| Decision field | Result |
|---|---|
| Model ID | QMRL-IR-SWAP-001 |
| Asset class | IR derivatives |
| Product | Plain-vanilla fixed-for-floating swap |
| Lifecycle stage | Independent validation prototype |
| Approved use | Base pricing validation, PV checks, DV01 checks, curve-shock review |
| Blocked use | XVA approval, structured swaps, callable swaps, production multi-curve pricing |
| Next required gate | v0.9 XVA validation |

## Validation decision matrix

| Control | Evidence | Result | Action |
|---|---:|---|---|
| Par-rate calculation | 4.2502% | Pass | Accept base pricing formula |
| Off-market test rate | 4.5002% | Pass | Tests non-zero NPV behavior |
| Payer NPV | -111,654.04 | Pass | Payer fixed is below value because test fixed rate is above par |
| Receiver NPV | 111,654.04 | Pass | Receiver fixed captures opposite value |
| Payer/receiver symmetry | 0.00000000 | Pass | No valuation asymmetry breach |
| Payer DV01 | 4,586.15 | Pass | Payer fixed gains when rates rise |
| Receiver DV01 | -4,586.15 | Pass | Receiver fixed loses when rates rise |
| +100bp payer P&L | 447,746.34 | Pass | Shock direction is coherent |
| -100bp payer P&L | -469,844.13 | Pass | Shock direction is coherent |

## Archer and model lifecycle action

| Field | Record |
|---|---|
| Archer action | Create or update QMRL-IR-SWAP-001 |
| MRM status | Base pricing and rate-risk controls passed |
| MMMRC message | No valuation symmetry breach. No DV01 sign breach. XVA is required next. |
| Monitoring frequency | Rerun after official curve refresh or methodology change |
| Revalidation trigger | Curve input change, pricing formula change, DV01 sign breach, XVA extension |
| Next lifecycle gate | v0.9 XVA validation |

## XVA next gate

XVA is a required core layer. The next module must convert the swap valuation path into exposure and valuation-adjustment evidence.

| XVA component | Required output |
|---|---|
| Exposure profile | Expected exposure and potential future exposure |
| CVA | Counterparty credit adjustment |
| DVA | Own-credit adjustment |
| FVA | Funding valuation adjustment |
| Sensitivity | Credit spread, recovery, funding spread and exposure shocks |
| Decision | XVA-adjusted value, risk impact and model-use control |

## Scope control

This layer validates the clean IR swap pricing and rate-risk chain. It is useful because it creates the base engine required before XVA, inflation derivatives, FX derivatives, option models, VaR and stress layers.

## Full shock table

|   curve_shift_bp |   par_swap_rate |   fixed_leg_pv |   floating_leg_pv |   payer_swap_npv |   receiver_swap_npv |   payer_npv_change |   receiver_npv_change |
|-----------------:|----------------:|---------------:|------------------:|-----------------:|--------------------:|-------------------:|----------------------:|
|             -100 |       0.0323254 |    2.06432e+06 |       1.48282e+06 |          -581498 |              581498 |            -469844 |                469844 |
|              -50 |       0.0374074 |    2.03686e+06 |       1.69311e+06 |          -343746 |              343746 |            -232092 |                232092 |
|                0 |       0.042502  |    2.00986e+06 |       1.89821e+06 |          -111654 |              111654 |                  0 |                     0 |
|               50 |       0.0476094 |    1.98333e+06 |       2.09824e+06 |           114914 |             -114914 |             226568 |               -226568 |
|              100 |       0.0527296 |    1.95725e+06 |       2.29334e+06 |           336092 |             -336092 |             447746 |               -447746 |

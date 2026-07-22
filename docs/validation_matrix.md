
# Validation Matrix

| Domain | Primary validation evidence | Automated tests | Current public status | Open gate |
|---|---|---:|---|---|
| Interest-rate valuation | Pricing, sensitivities, scenarios, lifecycle evidence | Yes | Implemented | Production calibration and internal portfolio evidence |
| XVA | CVA, DVA, FVA-style controls, exposure assumptions, sensitivities | Yes | Implemented public layer | Time-grid exposure, netting, collateral, counterparty calibration, wrong-way risk |
| FX forwards | Official-source inputs, valuation, shocks, reports | Yes | Implemented | Institution-specific curve and execution data |
| FX options | Pricing, Greeks, parity, volatility governance, challenger | Yes | Implemented | Dated public market-option quote benchmark |
| FX monitoring | Baseline, thresholds, ownership, status, revalidation triggers | Yes | PASS at governed baseline | External enterprise alert delivery |
| Governed GenAI | Evidence package, structured schema, grounding, human review | Yes | Implemented controlled layer | Controlled provider execution and human sign-off |
| Continuous integration | Python 3.12 workflow, compilation, pytest, JUnit | Yes | Enforced on `main` | None for public repository execution |
| Release governance | README, changelog, release manifest, citation, release tests | Yes | v1.2.0 | Future release maintenance |

## Interpretation

`Implemented` means the repository contains executable public evidence for the stated layer.

It does not mean production approval, regulatory approval, confidential market calibration, institution-specific materiality calibration, or access to internal systems.

## Current explicit open benchmark

The USD/BRL market-option quote benchmark remains:

`OPEN_NO_PUBLIC_QUOTE_DATA`

This open status is intentional and must not be converted into a pass without dated, auditable market-option evidence.

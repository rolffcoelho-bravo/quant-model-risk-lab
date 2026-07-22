# Validation Matrix

| Domain | Primary validation evidence | Automated tests | Current public status | Open boundary |
|---|---|---:|---|---|
| Interest-rate valuation | Pricing, sensitivities, scenarios, and lifecycle evidence | Yes | Implemented | Institution-specific calibration and portfolio evidence |
| XVA exposure simulation | Time grid, scenario paths, future-value cubes, netting, collateral, EE/EPE/ENE/PFE | Yes | v1.3.0 implemented | Production portfolios, CSA systems, and confidential calibration |
| Counterparty credit | Hazard, survival, PD, recovery, LGD, proxy governance, and sensitivities | Yes | v1.3.0 implemented with monitoring | Direct market curves and institution-approved proxy hierarchy |
| CVA/DVA/FVA | Discounted default integration, bilateral controls, funding components, and attribution | Yes | v1.3.0 implemented | Production close-out, funding policy, and accounting conventions |
| Wrong-way risk and stress | Dependence, conditional default, WWR uplift, stress channels, and concentration | Yes | v1.3.0 implemented with monitoring | Institution-specific dependence calibration and scenario approval |
| Independent challenge | Alternative calculations, tolerance hierarchy, convergence, stability, and promotion | Yes | v1.3.0 implemented | Independent institutional validation sign-off |
| Dashboard and lifecycle | Decision panels, benchmark drift, input freshness, disagreement, and revalidation | Yes | v1.3.0 implemented with monitoring | Enterprise monitoring and alert delivery |
| Governed GenAI | Approved evidence, structured findings, artifact citations, and human review | Yes | Controlled release challenge implemented | Live provider execution and institutional reviewer sign-off |
| FX options | Pricing, Greeks, parity, volatility governance, and challenger | Yes | Implemented | `OPEN_NO_PUBLIC_QUOTE_DATA` |
| Continuous integration | Python 3.12 compilation, deterministic environment, pytest, and JUnit evidence | Yes | Enforced on `main` | None for public repository execution |
| Release governance | README, changelog, citation, release manifest, contracts, CI, and explicit release approval | Yes | v1.3.0 | Future maintenance and revalidation |

## Interpretation

`Implemented` means the repository contains executable, reproducible public evidence for the stated layer. It does not mean production approval, regulatory approval, confidential market calibration, institution-specific materiality calibration, legal enforceability, or access to internal systems.

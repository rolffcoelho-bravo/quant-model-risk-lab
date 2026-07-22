# XVA v1.3 Validation Dashboard

**Overall status:** `PASS_WITH_MONITORING`  
**Collected tests:** `350`  
**Required CI:** `Python 3.12 validation`  
**Production approval:** `False`

| Panel | Status | Evidence |
|---|---|---|
| Scenario paths and future value | `PASS` | `docs/xva_scenario_path_architecture.md` |
| Netting, collateral, and exposure | `PASS` | `docs/xva_pathwise_exposure_integration.md` |
| Counterparty credit calibration | `PASS_WITH_MONITORING` | `docs/xva_counterparty_credit_calibration.md` |
| CVA, DVA, and FVA | `PASS` | `docs/xva_integration_and_attribution.md` |
| Wrong-way risk and stress | `PASS_WITH_MONITORING` | `docs/xva_wrong_way_risk_and_stress.md` |
| Independent challenge and stability | `PASS` | `docs/xva_independent_challenger_and_promotion.md` |
| Lifecycle monitoring | `PASS_WITH_MONITORING` | `reports/xva_v1_3_lifecycle_monitoring.json` |
| Governed GenAI and release governance | `PASS_WITH_MONITORING` | `data/genai/outputs/xva_v1_3_human_review.json` |

This dashboard is a public validation object. It is not a production risk report or model approval.
